# ================================================
# PropOS — Windows PowerShell Startup Script
# ================================================
# Usage:
#   .\start_propos.ps1
#
# For Task Scheduler auto-restart:
#   Action: powershell.exe
#   Arguments: -ExecutionPolicy Bypass -File "C:\Users\Administrator\Desktop\PropOS\start_propos.ps1"
#   Start in: C:\Users\Administrator\Desktop\PropOS
# ================================================

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  PropOS — Multi-Account Prop Trading OS" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

Set-Location $ProjectRoot

# Create data directory if missing
if (-not (Test-Path "data")) {
    New-Item -ItemType Directory -Path "data" | Out-Null
}

# Activate virtualenv
$VenvActivate = Join-Path $ProjectRoot "venv\Scripts\Activate.ps1"
if (Test-Path $VenvActivate) {
    & $VenvActivate
} else {
    Write-Host "ERROR: Virtual environment not found. Run: python -m venv venv" -ForegroundColor Red
    exit 1
}

# Set Python path
$env:PYTHONPATH = "."

# Auto-restart loop
$RestartDelay = 10  # seconds
$MaxRestarts = 5
$RestartCount = 0

while ($RestartCount -lt $MaxRestarts) {
    Write-Host ""
    Write-Host "Starting PropOS backend (attempt $($RestartCount + 1))..." -ForegroundColor Green
    Write-Host ""

    try {
        python -m backend.main
    } catch {
        Write-Host "PropOS crashed: $_" -ForegroundColor Red
    }

    $RestartCount++
    if ($RestartCount -lt $MaxRestarts) {
        Write-Host ""
        Write-Host "PropOS stopped. Restarting in $RestartDelay seconds... (attempt $RestartCount/$MaxRestarts)" -ForegroundColor Yellow
        Start-Sleep -Seconds $RestartDelay
    }
}

Write-Host ""
Write-Host "PropOS has exceeded max restart attempts ($MaxRestarts). Manual intervention required." -ForegroundColor Red
Write-Host "Press any key to exit."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
