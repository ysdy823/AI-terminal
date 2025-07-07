# TERMAI – Windows installer (PowerShell 7+)

Write-Host "==> בודק Python…"
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  Write-Warning "Python 3.8+ לא נמצא! התקן Python והרץ שוב."
  exit 1
}

Write-Host "==> יוצר ‎.venv‎ ומתקין תלותיות…"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r server/requirements.txt

Write-Host "`n==> הדבק API-KEY (OpenRouter/OpenAI):"
$api = Read-Host
echo "{`"API_KEY`":`"$api`"}" | Out-File -Encoding utf8 settings.json

Write-Host "`n==> קוד שפה (he/en/…):"
$lang = Read-Host

Write-Host "==> מריץ TERMAI…"
$client = ". .\.venv\Scripts\Activate.ps1; python client.py"
Start-Process powershell -NoExit -ArgumentList "-NoExit", "-Command", $client
