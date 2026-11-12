# Detect active Wi-Fi IPv4 dynamically
$lanIp = (Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias "Wi-Fi*" -ErrorAction SilentlyContinue | Select-Object -ExpandProperty IPAddress -First 1)
if (-not $lanIp) {
    $lanIp = "127.0.0.1"
}

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "         KEP PRINTGRID - FULL STACK SERVER LAUNCHER" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host " [✓] Laptop Browser URL   : http://localhost:8080/" -ForegroundColor Green
Write-Host " [✓] Customer Upload URL  : http://localhost:8080/shop/KEP10001/" -ForegroundColor Green
Write-Host " [✓] Live Camera Scanner  : http://localhost:8080/scanner/" -ForegroundColor Green
Write-Host " [✓] Mobile Phone / QR URL : http://${lanIp}:8080/shop/KEP10001/" -ForegroundColor Yellow
Write-Host " [✓] Shop Owner Dashboard  : http://localhost:8080/dashboard/" -ForegroundColor Magenta
Write-Host ""
Write-Host "Starting Django server on 0.0.0.0:8080 (Press Ctrl+C to stop)..." -ForegroundColor White
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

python manage.py runserver 0.0.0.0:8080
