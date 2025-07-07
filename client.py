import requests
import readline
import sys
import os
import time
import random
import webbrowser
import json

SERVER_URL = "http://localhost:8000"
HISTORY_FILE = "history.txt"
CONFIG_FILE = "settings.json"
USER_LANG = "en"
USER_MODEL = None
USER_API = None

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    CYAN = '\033[96m'
    SPECIAL = '\033[38;5;51m'  # טורקיז זוהר

def print_logo():
    logo = r'''
╭───────────────────────────╮
│   ████████╗███████╗███╗   │
│   ╚══██╔══╝██╔════╝████╗  │
│      ██║   █████╗  ██╔██╗ │
│      ██║   ██╔══╝  ██║╚██╗│
│      ██║   ███████╗██║ ╚██│
│      ╚═╝   ╚══════╝╚═╝  ╚═╝
│  _____  _______  __  __   │
│ |_   _||__   __||  \/  |  │
│   | |     | |   | \  / |  │
│   | |     | |   | |\/| |  │
│  _| |_    | |   | |  | |  │
│ |_____|   |_|   |_|  |_|  │
│                           │
│   TERMAI: Terminal AI     │
╰───────────────────────────╯
             ⎯⎯⎯⎯⎯
      Powered by IS SH
    '''
    print(bcolors.SPECIAL + logo + bcolors.ENDC)

# ----------  Helpers for config ----------
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)

# ----------  On-boarding ----------
def onboarding():
    global USER_LANG, USER_MODEL, USER_API
    print_logo()
    cfg = load_config()
    # אם יש קובץ הגדרות מלא – לא לשאול שוב
    if all(k in cfg for k in ["API_KEY", "LANG", "MODEL", "API_PROVIDER"]):
        USER_LANG = cfg["LANG"]
        USER_MODEL = cfg["MODEL"]
        USER_API = cfg["API_PROVIDER"]
        print(bcolors.OKGREEN + f"TERMAI ready!  [{USER_LANG}, {USER_MODEL}, {USER_API}]" + bcolors.ENDC)
        print_help()
        return

    # 1. שפה
    print(bcolors.CYAN + "\nChoose language / בחר שפה  (en/he/fr/ru/ar):" + bcolors.ENDC)
    USER_LANG = input("Code (default en): ").strip().lower() or "en"
    if len(USER_LANG) != 2:
        USER_LANG = "en"
    print(bcolors.OKGREEN + f"Working in language: {USER_LANG}" + bcolors.ENDC)

    # 2. ספק API
    print(bcolors.HEADER + "\n=== Choose AI provider ===" + bcolors.ENDC)
    print(bcolors.OKBLUE + "1: OpenRouter (free tier)\n2: OpenAI GPT\n3: Google/Anthropic\n4: Manual" + bcolors.ENDC)
    opt = input("Choice [1]: ").strip()
    USER_API = {"2": "openai", "3": "google", "4": "manual"}.get(opt, "openrouter")
    if USER_API == "openai":
        url = "https://platform.openai.com/api-keys"
    elif USER_API == "google":
        url = "https://aistudio.google.com/app/apikey"
    elif USER_API == "manual":
        url = ""
    else:
        url = "https://openrouter.ai/"
    if url and input("Open signup page? (y/n): ").lower() == "y":
        webbrowser.open(url)

    # 3. API-KEY
    api_key = input("Paste your API key: ").strip()

    # 4. מודל – נבחר אוטומטית (אפשר להחליף אחר-כך)
    models = get_model_list()
    priority = ["openai/gpt-4o", "cohere/command-r", "google/gemma-7b-it", "mistralai/mistral-7b-instruct"]
    USER_MODEL = next((m for m in priority if m in models), models[0] if models else "cohere/command-r")
    print(bcolors.OKGREEN + f"Using model: {USER_MODEL}" + bcolors.ENDC)

    # שמירה והעברה לשרת
    cfg.update({"API_KEY": api_key, "LANG": USER_LANG, "MODEL": USER_MODEL, "API_PROVIDER": USER_API})
    save_config(cfg)
    try:
        requests.post(SERVER_URL + "/settings", json=cfg, timeout=5)
    except Exception:
        pass
    print_help()

# ----------  Utils ----------
def get_model_list():
    try:
        return requests.get(SERVER_URL + "/models", timeout=3).json().get("models", [])
    except Exception:
        return []

def print_help():
    examples = {
        "he": [
            ("צור תיקיה בשם בדיקה", "mkdir bidka"),
            ("הצג קבצים בתיקיה הנוכחית", "ls"),
            ("מחק קובץ בשם test.txt", "rm test.txt"),
        ],
        "en": [
            ("Create a folder named test", "mkdir test"),
            ("List files in current directory", "ls"),
            ("Delete file test.txt", "rm test.txt"),
        ],
    }.get(USER_LANG, [])
    print(bcolors.SPECIAL + "\n== Quick examples ==" + bcolors.ENDC)
    for ex, bash in examples:
        print(f"{bcolors.OKBLUE}{ex}{bcolors.ENDC}  ->  {bash}")
    print(bcolors.OKGREEN + """
/help       show this help
/examples   random example
/ai <q>     ask AI without executing
/model      change model
/api        change API key/provider
/showbash   show last bash command
/history    local history
/exit       quit
""" + bcolors.ENDC)

def translate_output(text):
    if USER_LANG == "he" and not any('\u0590' <= c <= '\u05EA' for c in text):
        try:
            data = {"command": f"/ai translate to Hebrew:\n{text}", "lang": USER_LANG}
            requests.post(SERVER_URL + "/run_command", json=data, timeout=8)
        except Exception:
            pass
    return text

# ----------  Main loop ----------
LAST_BASH = ""

def handle_response(result):
    global LAST_BASH
    out = result.get("result", "")
    bash_cmd = result.get("bash_cmd")
    if bash_cmd:
        LAST_BASH = bash_cmd
        print(bcolors.CYAN + f"\n[Bash]: {bash_cmd}" + bcolors.ENDC)
    print(translate_output(out))

def main():
    onboarding()
    while True:
        try:
            cmd = input(bcolors.BOLD + "TERMAI >>> " + bcolors.ENDC).strip()
            if cmd in ("/exit", "exit", "quit"):
                break
            if cmd == "/showbash":
                print(bcolors.CYAN + f"Last bash: {LAST_BASH}" + bcolors.ENDC); continue
            if cmd == "/help": print_help(); continue
            # Send to server
            data = {"command": cmd, "lang": USER_LANG, "model": USER_MODEL}
            res = requests.post(SERVER_URL + "/run_command", json=data, timeout=30).json()
            handle_response(res)
            if res.get("need_approve"):
                if input("Proceed? (y/n): ").lower() == "y":
                    data["force"] = True
                    res = requests.post(SERVER_URL + "/run_command", json=data, timeout=30).json()
                    handle_response(res)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(bcolors.FAIL + f"Error: {e}" + bcolors.ENDC)

if __name__ == "__main__":
    main()

