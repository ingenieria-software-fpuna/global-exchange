# Detener simulador y limpiar datos
Write-Host "Deteniendo simulador y limpiando datos..." -ForegroundColor Yellow
docker-compose down -v

Write-Host "Simulador detenido y datos limpiados correctamente." -ForegroundColor Green