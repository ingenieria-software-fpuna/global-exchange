#!/bin/bash
echo "Levantando simulador de pasarela de pago..."
docker-compose up -d

echo "Simulador disponible en:"
echo "  API: http://localhost:3001"
echo "  Docs: http://localhost:3001/docs"
echo "  Admin: http://localhost:3001/admin"