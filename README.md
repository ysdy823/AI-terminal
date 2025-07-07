# TERMAI – Terminal AI v1.0
**טרמינל בינה מלאכותית רב-לשוני**  
Powered by **IS SH**

---

## 🚀 למה TERMAI?
| יכולת | תיאור |
|-------|-------|
| שפה טבעית → Bash | כתוב בעברית/אנגלית/… – TERMAI ממיר לפקודת bash אחת ומריץ. |
| הצגת הפקודה | תמיד מוצגת הפקודה באנגלית כדי ללמוד ממנה. |
| תרגום פלט | פלט bash מתורגם אוטומטית לשפת המשתמש (עברית ↔︎ אנגלית). |
| ספקי AI | OpenRouter (חינם), OpenAI GPT-4o, Google Gemini, Anthropic Claude, ידני. |
| מודלים מרובים | בחירת מודל /model — ברירת מחדל: המודל החזק הזמין. |
| קיצורי מקשים | **F1 / Ctrl-H** — עזרה זריזה. |
| פקודות עזר | `/help`, `/examples`, `/ai`, `/api`, `/showbash`, `/history` ועוד. |
| היסטוריה | נשמרת ב-SQLite + history.txt מקומי. |
| בטיחות | מזהה פקודות מסוכנות (`rm`, `sudo`…) ודורש אישור. |
| חוצה-פלטפורמות | סקריפט התקנה Linux / WSL, PowerShell Windows. |

---

## 🖥 התקנה מהירה

### Linux / WSL / Mac (bash)
```bash
git clone https://github.com/your-repo/termai.git
cd termai
chmod +x install_linux.sh
./install_linux.sh

