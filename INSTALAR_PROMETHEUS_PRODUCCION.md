# Instalar Prometheus Client en Producción

## Opción 1: Usar el entorno virtual (Recomendado)

```bash
# Activar el entorno virtual
source /home/bija/projects/apicultura/apitool-fastapi/venv/bin/activate

# Instalar prometheus-client
pip install prometheus-client==0.19.0

# O instalar todas las dependencias desde requirements.txt
pip install -r /home/bija/projects/apicultura/apitool-fastapi/requirements.txt

# Desactivar el entorno virtual (opcional)
deactivate
```

## Opción 2: Usar pip del venv directamente (sin activar)

```bash
# Instalar usando el pip del venv directamente
/home/bija/projects/apicultura/apitool-fastapi/venv/bin/pip install prometheus-client==0.19.0
```

## Opción 3: Instalar todas las dependencias

```bash
# Activar el entorno virtual
source /home/bija/projects/apicultura/apitool-fastapi/venv/bin/activate

# Instalar todas las dependencias (asegura que todo esté actualizado)
pip install -r /home/bija/projects/apicultura/apitool-fastapi/requirements.txt

# Desactivar
deactivate
```

## Verificar instalación

```bash
# Activar el entorno virtual
source /home/bija/projects/apicultura/apitool-fastapi/venv/bin/activate

# Verificar que está instalado
pip list | grep prometheus

# O probar import
python -c "from prometheus_client import Counter; print('OK')"

# Desactivar
deactivate
```

## Reiniciar el servicio

Después de instalar:

```bash
sudo systemctl restart apitool.service
sudo systemctl status apitool.service
```

## Nota importante

**NO uses `sudo pip install`** ni `--break-system-packages` porque:
- Puede romper el sistema Python
- El servicio usa el entorno virtual, no el Python del sistema
- Las dependencias deben instalarse en el venv que usa gunicorn

