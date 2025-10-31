# Simulador de Pasarela de Pago

Este proyecto simula una pasarela de pago completa para pruebas de integración. Incluye API REST, base de datos postgres, webhooks, panel de administración y documentación completa.

### El simulador usa:
- **PostgreSQL 13.6** en puerto `5433` 
- **Usuario**: `simulador`, **Password**: `simulador123`
- **Base de datos**: `simulador_pagos`

## Características
- **API REST** con FastAPI para simular pagos
- **Múltiples métodos de pago**: tarjeta, transferencia, tarjeta credito local, billetera
- **Estados configurables**: éxito, fallo, pendiente
- **Webhooks** para notificaciones asíncronas
- **Panel de administración** web
- **Documentación interactiva** con Swagger
- **Soporte Docker** para deployment
## OJO
- Para las tarjetas y billetera rechaza si los ultimos 2 digitos son un numero primo
- Para transferencia rechaza si el comprobante tiene menos de 6 caracteres o si hay una secuencia de tres ceros 000

##  Levantar el simulador:

**Windows**

```
powershell -ExecutionPolicy Bypass -File .\run.ps1
```

**Bash:**
```bash
chmod +x run.sh
./run.sh
```

### Docker Compose directo
```
docker-compose up -d
```

###  Parar el simulador:

**Windows**
```
powershell -ExecutionPolicy Bypass -File .\stop.ps1
```

**Bash:**
```
./stop.sh
```

### Docker Compose directo
```
docker-compose down
```

### Parar y limpiar datos:

**Windows**
```
powershell -ExecutionPolicy Bypass -File .\clean.ps1
```

**Bash:**
```
./clean.sh
```

### Docker Compose directo
```
docker-compose down -v
```

Esto levanta:
- **PostgreSQL** en puerto 5433
- **Simulador FastAPI** en puerto 3001
- **Base de datos** `simulador_pagos` creada
- **Tablas creadas automáticamente**
## Uso
- **API**: `http://localhost:3001`
- **Documentación**: `http://localhost:3001/docs`
- **Admin Panel**: `http://localhost:3001/admin`

## Configuración
- **Simulador**: Puerto 3001 
- **PostgreSQL**: Puerto 5433 
- **Todo automatizado** con Docker Compose

## Documentación
- `INTEGRATION.md` - Ejemplos de uso API
