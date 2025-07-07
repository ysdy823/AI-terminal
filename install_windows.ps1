# ------------------ TERMAI Windows installer ------------------
param()
Write-Host "==> Checking Python..."
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  Write-Warning "Python לא נמצא! התקן Python 3.8+ והרץ שוב."
  exit 1
}
Write-Host "==> Creating virtual-env (.venv)"
python -m venv .venv
.\.venv\Scripts\Activate.ps1

Write-Host "==> Installing requirements"
pip install -r server/requirements.txt

Write-Host "`n==> הזן API-KEY (משוכפל מ-OpenRouter / OpenAI):"
$api = Read-Host
echo "{`"API_KEY`":`"$api`"}" | Out-File -Encoding utf8 settings.json

Write-Host "`n==> באיזו שפה לעבוד? (he/en/fr/ru/zh/...):"
$lang = Read-Host

Write-Host "==> Running TERMAI..."
Start-Process powershell -NoExit -ArgumentList "-NoExit", "-Command", ". .\.venv\Scripts\Activate.ps1; python client.py"
