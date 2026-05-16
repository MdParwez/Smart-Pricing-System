$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendPath = Join-Path $projectRoot "backend"
$frontendPath = Join-Path $projectRoot "frontend"

$backendCommand = "Set-Location -LiteralPath '$backendPath'; .\venv\Scripts\Activate.ps1; python main.py"
$frontendCommand = "Set-Location -LiteralPath '$frontendPath'; npm.cmd start"

Start-Process powershell -ArgumentList "-NoExit -ExecutionPolicy Bypass -Command `"$backendCommand`""
Start-Process powershell -ArgumentList "-NoExit -ExecutionPolicy Bypass -Command `"$frontendCommand`""

Write-Host ""
Write-Host "Flight Fare Dashboard is starting..."
Write-Host "Backend:  http://localhost:8000"
Write-Host "Frontend: http://localhost:3000"
Write-Host ""
