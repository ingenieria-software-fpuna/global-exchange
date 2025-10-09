# Levantar simulador con Docker Compose
Write-Host "Levantando simulador de pasarela de pago..." -ForegroundColor Green
docker-compose up -d

Write-Host "Simulador disponible en:" -ForegroundColor Yellow
Write-Host "  API: http://localhost:3001" -ForegroundColor Cyan
Write-Host "  Docs: http://localhost:3001/docs" -ForegroundColor Cyan
Write-Host "  Admin: http://localhost:3001/admin" -ForegroundColor Cyan