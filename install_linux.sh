#!/usr/bin/env bash
# TERMAI Linux installer & launcher (no manual chmod needed)
set -e

echo "╭───────── TERMAI • Linux installer ─────────╮"
echo "│  Setup venv, install deps, launch TERMAI.   │"
echo "╰──────────────────────────────────────────────╯"

read -p "Continue? (Y/n): " go
go="${go,,}"
[[ "$go" == "n" ]] && { echo "Aborted."; exit 0; }

# --- get sudo upfront (single password prompt) ---
sudo -v  # keeps credentials fresh

# --- prerequisites ------------------------------
sudo apt-get update -y
sudo apt-get install -y python3 python3-venv python3-pip sqlite3 lsof

# --- virtual-env --------------------------------
[[ ! -d .venv ]] && python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r server/requirements.txt

# --- choose terminal ----------------------------
cd "$(dirname "$0")"
if command -v gnome-terminal &>/dev/null;   then TERM='gnome-terminal --title="TERMAI" --'
elif command -v xfce4-terminal &>/dev/null; then TERM='xfce4-terminal -T "TERMAI" --hold -e'
else                                            TERM='xterm -T "TERMAI" -hold -e'
fi

# --- launch -------------------------------------
$TERM bash -c '
  cd "'"$(pwd)"'";
  source .venv/bin/activate;
  # kill old server on 8000 if exists
  lsof -ti:8000 | xargs -r kill -9
  uvicorn server.server:app --port 8000 &  # server background
  sleep 2
  python3 client.py
'
