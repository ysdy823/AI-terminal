<#
 .SYNOPSIS
    TERMAI – Windows installer & launcher (PowerShell 7+).

 .NOTES
    • יוצר virtual-env בתיקיה .venv  
    • מתקין תלויות מתוך server\requirements.txt  
    • מפעיל שני חלונות PowerShell:
        1. uvicorn server  (רקע)
        2. client.py       (ממשק)
#>

Write-Host "`n=== TERMAI Windows installer ===`n" -ForegroundColor Cyan
$resp = Read-Host "Continue? (y/n)"
if ($resp -ne "y") { exit }

# ---------- Python & venv ----------
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python not found in PATH – install Python 3 first." -ForegroundColor Red
    exit 1
}
python -m venv .venv
& .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r server\requirements.txt

# ---------- paths ----------
$root = Get-Location
$serverCmd = "cd $root; .\.venv\Scripts\Activate.ps1; uvicorn server.server:app --port 8000"
$clientCmd = "cd $root; .\.venv\Scripts\Activate.ps1; python client.py"

# ---------- launch ----------
Start-Process powershell -WindowStyle Minimized -ArgumentList "-NoExit", "-Command", $serverCmd
Start-Sleep -Seconds 2
Start-Process powershell -NoExit -ArgumentList "-NoExit", "-Command", $clientCmd

