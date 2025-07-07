from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import subprocess, requests, re, os, sqlite3, json, pathlib

# ────────── DB (auto-migrate) ────────────────────────────────────────────────
DB = pathlib.Path(__file__).resolve().parent / "history.db"

def init_db():
    conn = sqlite3.connect(DB)
    cols = [r[1] for r in conn.execute("PRAGMA table_info(history)").fetchall()]
    if not {"cmd", "res", "lang"}.issubset(cols):
        conn.execute("DROP TABLE IF EXISTS history")
    conn.execute("""CREATE TABLE IF NOT EXISTS history(
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            cmd  TEXT,
            res  TEXT,
            lang TEXT,
            dt   DATETIME DEFAULT CURRENT_TIMESTAMP)""")
    conn.close()

def insert_history(cmd: str, res: str, lang: str):
    conn = sqlite3.connect(DB)
    conn.execute("INSERT INTO history(cmd,res,lang) VALUES (?,?,?)",
                 (cmd, res[:4000], lang))
    conn.commit()
    conn.close()

def get_history(limit: int = 30):
    conn = sqlite3.connect(DB)
    rows = conn.execute(
        "SELECT cmd,res,lang,dt FROM history ORDER BY id DESC LIMIT ?",
        (limit,)).fetchall()
    conn.close()
    return rows

# ────────── Config (settings.json) ───────────────────────────────────────────
CFG = pathlib.Path(__file__).resolve().parent.parent / "settings.json"

def _load():
    return json.load(open(CFG)) if CFG.exists() else {}

def _save(d):  # pretty-print UTF-8
    json.dump(d, open(CFG, "w"), indent=2, ensure_ascii=False)

def get_cfg(): return _load()

def set_cfg(k, v): cfg = _load(); cfg[k] = v; _save(cfg)

# ────────── FastAPI setup ────────────────────────────────────────────────────
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])
init_db()

MODELS = ["openai/gpt-4o", "cohere/command-r",
          "google/gemma-7b-it", "mistralai/mistral-7b-instruct"]

DANGER = {"rm", "reboot", "shutdown", "sudo", "dd", "mkfs", "init", "halt"}

# ────────── Utility helpers ──────────────────────────────────────────────────
def translit_he(word):
    heb = 'אבגדהוזחטיכךלמםנןסעפףצץקרשת'
    lat = ["a","b","g","d","h","v","z","ch","t","y",
           "k","k","l","m","m","n","n","s","a","p","f","tz","tz","k","r","sh","t"]
    return ''.join(lat[heb.index(c)] if c in heb else c for c in word)

def heb2latin(text):
    return ' '.join(translit_he(w) if re.search('[\u0590-\u05FF]', w) else w
                    for w in text.split())

def build_prompt(cmd, lang):
    """Prompt סלחני: מקבל שאלות או הוראות ומחזיר פקודת bash יחידה"""
    ex_he = ("דוגמאות:\n"
             "• \"מה הנתיב הנוכחי שלי?\" → pwd\n"
             "• \"מי המשתמש הנוכחי?\" → whoami\n"
             "• \"צור תיקיה בשם בדיקה\" → mkdir bidka\n")
    ex_en = ("Examples:\n"
             "• \"what is my current path?\" → pwd\n"
             "• \"who am I\" → whoami\n"
             "• \"create a folder test\" → mkdir test\n")
    if lang == "he":
        return ("המר כל הוראה או שאלה בעברית לפקודת bash יחידה, "
                "החזר רק את הפקודה.\n" + ex_he + heb2latin(cmd))
    return ("Convert ANY natural-language request to one bash command. "
            "Return ONLY the command.\n" + ex_en + cmd)

def ai_call(messages, model, key, provider):
    body = {"model": model, "messages": messages, "max_tokens": 64}
    if provider == "openai":
        url = "https://api.openai.com/v1/chat/completions"
        hdr = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    else:  # openrouter default
        url = "https://openrouter.ai/api/v1/chat/completions"
        hdr = {"Authorization": f"Bearer {key}",
               "HTTP-Referer": "http://localhost",
               "Content-Type": "application/json"}
    r = requests.post(url, headers=hdr, json=body, timeout=25)
    r.raise_for_status()
    return r.json()

def extract(cmd):
    m = re.search(r"```(?:bash)?(.*?)```", cmd, re.S)
    if m:
        return m.group(1).strip()
    return cmd.splitlines()[0].strip()

# ────────── API Endpoints ────────────────────────────────────────────────────
@app.post("/run_command")
async def run_command(req: Request):
    data = await req.json()
    lang = data.get("lang", "en")
    text = data.get("command", "").strip()
    model = data.get("model") or get_cfg().get("MODEL") or MODELS[0]
    key = get_cfg().get("API_KEY")
    provider = get_cfg().get("API_PROVIDER", "openrouter")
    force = data.get("force", False)

    if not key:
        return {"result": "API KEY missing", "bash_cmd": None}
    if not text:
        return {"result": "No command", "bash_cmd": None}

    # /ai passthrough
    if text.startswith("/ai"):
        q = text[3:].strip()
        try:
            out = ai_call([{"role": "user", "content": q}], model, key, provider)\
                    ["choices"][0]["message"]["content"]
        except Exception as e:
            out = f"Error contacting AI: {e}"
        insert_history(text, out, lang)
        return {"result": out, "bash_cmd": None}

    # translate to bash
    try:
        rsp = ai_call([{"role": "user", "content": build_prompt(text, lang)}],
                      model, key, provider)
        bash = extract(rsp["choices"][0]["message"]["content"])
    except Exception as e:
        err = "שגיאה בחיבור למנוע." if lang == "he" else "Error contacting AI."
        insert_history(text, err, lang)
        return {"result": err, "bash_cmd": None}

    if not bash:
        msg = ("⚠️ לא הצלחתי להבין." if lang == "he"
               else "⚠️ Could not understand.")
        insert_history(text, msg, lang)
        return {"result": msg, "bash_cmd": bash}

    if bash.split()[0] in DANGER and not force:
        warn = (f"⚠️ {bash} מסוכן! לאשר?" if lang == "he"
                else f"⚠️ {bash} is dangerous. Approve?")
        return {"result": warn, "need_approve": True, "bash_cmd": bash}

    # run bash
    try:
        output = subprocess.check_output(bash, shell=True,
                                         stderr=subprocess.STDOUT,
                                         encoding="utf8", timeout=12).strip()
        if not output:
            output = "בוצע בהצלחה." if lang == "he" else "Executed successfully."
    except subprocess.CalledProcessError as e:
        output = ("שגיאה:\n" if lang == "he" else "Error:\n") + e.output
    except Exception as e:
        output = str(e)

    # quota warning
    if any(w in output.lower() for w in ("quota", "rate limit", "blocked")):
        output += ("\n⚠️ ייתכן שנחסמת – החלף API ב-/api."
                   if lang == "he" else
                   "\n⚠️ You may be rate-limited – change API via /api.")

    insert_history(text, output, lang)
    return {"result": output, "bash_cmd": bash}

@app.get("/models")
async def models():
    return {"models": MODELS}

@app.post("/settings")
async def settings(req: Request):
    for k, v in (await req.json()).items():
        set_cfg(k, v)
    return {"result": "updated", "config": get_cfg()}

