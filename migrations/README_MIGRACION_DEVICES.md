# Migración: Campos Adicionales en Tabla Devices

## Descripción

Esta migración actualiza la tabla `devices` para soportar información completa del dispositivo según el documento `DEVICES_API.md`.

## Cambios Realizados

### Campos Agregados
- `modelName` (VARCHAR, nullable): Modelo específico del dispositivo
- `brand` (VARCHAR, nullable): Marca del dispositivo
- `manufacturer` (VARCHAR, nullable): Fabricante del dispositivo
- `osVersion` (VARCHAR, nullable): Versión del sistema operativo
- `deviceType` (VARCHAR, nullable): Tipo de dispositivo (PHONE, TABLET, DESKTOP, etc.)
- `appVersion` (VARCHAR, nullable): Versión de la aplicación
- `buildVersion` (VARCHAR, nullable): Número de build de la aplicación
- `updatedAt` (TIMESTAMP): Fecha de última actualización (auto-actualizado)

### Modificaciones a Campos Existentes
- `deviceName`: Ahora es NOT NULL (requerido)
- `platform`: Ahora es NOT NULL (requerido)
- `expoPushToken`: Ahora es nullable (opcional)

### Índices
- Se crea un índice único `idx_user_device_platform` en `(userId, deviceName, platform)`
- Se elimina el constraint unique de `expoPushToken` (ya que ahora puede haber múltiples dispositivos sin token)

### Triggers
- Se crea un trigger que actualiza automáticamente `updatedAt` cuando se modifica un registro

## Instrucciones de Ejecución

### 1. Backup de la Base de Datos
**IMPORTANTE**: Siempre hacer backup antes de ejecutar migraciones.

```bash
pg_dump -h localhost -U tu_usuario -d tu_base_de_datos > backup_antes_migracion_devices.sql
```

### 2. Ejecutar Migración

**Opción A: Desde psql**
```bash
psql -h localhost -U tu_usuario -d tu_base_de_datos -f migrations/add_device_fields.sql
```

**Opción B: Desde Python (usando SQLAlchemy)**
```python
from app.database import engine

with open('migrations/add_device_fields.sql', 'r') as f:
    sql = f.read()
    
with engine.connect() as conn:
    conn.execute(sql)
    conn.commit()
```

**Opción C: Desde pgAdmin o DBeaver**
- Abrir el archivo `migrations/add_device_fields.sql`
- Ejecutar el script completo

### 3. Verificar Migración

Ejecutar esta consulta para verificar que todos los campos fueron agregados:

```sql
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'devices' 
ORDER BY ordinal_position;
```

Verificar que el índice fue creado:

```sql
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'devices' 
AND indexname = 'idx_user_device_platform';
```

### 4. Verificar Trigger

```sql
SELECT trigger_name, event_manipulation, event_object_table
FROM information_schema.triggers
WHERE event_object_table = 'devices';
```

## Rollback

Si necesitas revertir los cambios, ejecuta:

```bash
psql -h localhost -U tu_usuario -d tu_base_de_datos -f migrations/rollback_device_fields.sql
```

**ADVERTENCIA**: El rollback eliminará todos los datos almacenados en los nuevos campos.

## Manejo de Datos Existentes

La migración maneja automáticamente:

1. **Dispositivos con `deviceName` NULL**: Se asigna 'Unknown Device'
2. **Dispositivos con `platform` NULL**: Se asigna 'unknown'
3. **Dispositivos existentes**: Se actualiza `updatedAt` con el valor de `createdAt` o la fecha actual

## Posibles Problemas y Soluciones

### Error: "duplicate key value violates unique constraint"
**Causa**: Ya existen dispositivos con la misma combinación `(userId, deviceName, platform)`

**Solución**: Antes de ejecutar la migración, identificar y limpiar duplicados:

```sql
-- Identificar duplicados
SELECT userId, deviceName, platform, COUNT(*) 
FROM devices 
GROUP BY userId, deviceName, platform 
HAVING COUNT(*) > 1;

-- Eliminar duplicados (mantener el más reciente)
DELETE FROM devices d1
USING devices d2
WHERE d1.id < d2.id
AND d1.userId = d2.userId
AND d1.deviceName = d2.deviceName
AND d1.platform = d2.platform;
```

### Error: "column already exists"
**Causa**: La migración ya fue ejecutada parcialmente

**Solución**: Verificar qué campos ya existen y comentar las líneas correspondientes en el script, o ejecutar el rollback primero.

### Error: "constraint does not exist"
**Causa**: El constraint `devices_expoPushToken_key` no existe en tu base de datos

**Solución**: Este error es seguro ignorar. El script usa `IF EXISTS` para manejar esto, pero si aún falla, simplemente comenta esa sección.

## Testing Post-Migración

Después de la migración, verificar que:

1. ✅ Los endpoints `POST /users/devices` y `PUT /users/devices` funcionan correctamente
2. ✅ El endpoint `GET /users/devices` retorna todos los nuevos campos
3. ✅ Se pueden crear dispositivos sin `pushToken`
4. ✅ Se pueden actualizar dispositivos existentes
5. ✅ El campo `updatedAt` se actualiza automáticamente

## Notas Adicionales

- La migración es **idempotente** (se puede ejecutar múltiples veces sin problemas)
- Los campos nuevos son **nullable**, por lo que no afectará datos existentes
- El índice único previene dispositivos duplicados por usuario
- El trigger asegura que `updatedAt` siempre esté actualizado

## Soporte

Si encuentras problemas durante la migración, verifica:
1. Los logs de PostgreSQL
2. Que tengas permisos suficientes (ALTER TABLE, CREATE INDEX, CREATE TRIGGER)
3. Que no haya transacciones abiertas bloqueando la tabla

