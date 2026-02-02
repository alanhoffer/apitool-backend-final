# Instalación de Prometheus Client en Producción

## Problema

La aplicación requiere `prometheus-client` para las métricas, pero puede funcionar sin él (las métricas estarán deshabilitadas).

## Solución Rápida

Instalar la dependencia en el servidor de producción:

```bash
# Activar el entorno virtual (si usas uno)
source /home/bija/projects/apicultura/apitool-fastapi/venv/bin/activate

# Instalar prometheus-client
pip install prometheus-client==0.19.0

# O instalar todas las dependencias desde requirements.txt
pip install -r requirements.txt
```

## Verificación

Después de instalar, reiniciar el servicio:

```bash
sudo systemctl restart apitool.service
sudo systemctl status apitool.service
```

## Estado Actual

- ✅ La aplicación puede iniciar **sin** `prometheus-client` (métricas deshabilitadas)
- ⚠️ Para habilitar métricas, instalar `prometheus-client`
- ✅ El endpoint `/metrics` retornará 503 si no está instalado

## Nota

La dependencia ya está en `requirements.txt`, así que si instalas todas las dependencias con `pip install -r requirements.txt`, se instalará automáticamente.

