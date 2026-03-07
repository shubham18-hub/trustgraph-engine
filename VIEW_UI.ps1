# Simple script to open the beautiful UI
Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   Opening TrustGraph Beautiful UI...                     ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Get the full path to index.html
$htmlPath = Join-Path $PSScriptRoot "index.html"

if (Test-Path $htmlPath) {
    Write-Host "✓ Found index.html" -ForegroundColor Green
    Write-Host "✓ Opening in your default browser..." -ForegroundColor Green
    Write-Host ""
    
    # Open in default browser
    Start-Process $htmlPath
    
    Write-Host "╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║   ✓ UI Opened Successfully!                              ║" -ForegroundColor Green
    Write-Host "╚═══════════════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""
    Write-Host "The UI will try to connect to: http://localhost:8000" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "If you see connection errors in the demo section:" -ForegroundColor Yellow
    Write-Host "  1. Make sure your server is running" -ForegroundColor White
    Write-Host "  2. The UI will still look beautiful!" -ForegroundColor White
    Write-Host "  3. The demo section needs the backend API" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "✗ index.html not found!" -ForegroundColor Red
    Write-Host "Make sure you're in the correct directory" -ForegroundColor Yellow
}

Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
