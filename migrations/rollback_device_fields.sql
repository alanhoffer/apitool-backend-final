-- Rollback: Revertir cambios en la tabla devices
-- Fecha: 2024-01-XX
-- ADVERTENCIA: Esta migración eliminará los nuevos campos y datos almacenados en ellos

BEGIN;

-- 1. Eliminar trigger
DROP TRIGGER IF EXISTS trigger_update_devices_updated_at ON devices;
DROP FUNCTION IF EXISTS update_devices_updated_at();

-- 2. Eliminar índice único
DROP INDEX IF EXISTS idx_user_device_platform;

-- 3. Eliminar nuevos campos
ALTER TABLE devices 
DROP COLUMN IF EXISTS modelName,
DROP COLUMN IF EXISTS brand,
DROP COLUMN IF EXISTS manufacturer,
DROP COLUMN IF EXISTS osVersion,
DROP COLUMN IF EXISTS deviceType,
DROP COLUMN IF EXISTS appVersion,
DROP COLUMN IF EXISTS buildVersion,
DROP COLUMN IF EXISTS updatedAt;

-- 4. Restaurar constraint unique en expoPushToken (si se necesita)
-- NOTA: Esto puede fallar si hay tokens duplicados
-- ALTER TABLE devices 
-- ADD CONSTRAINT devices_expoPushToken_key UNIQUE (expoPushToken);

-- 5. Hacer expoPushToken NOT NULL nuevamente (si se necesita)
-- ALTER TABLE devices 
-- ALTER COLUMN expoPushToken SET NOT NULL;

-- 6. Permitir NULL en deviceName y platform nuevamente
ALTER TABLE devices 
ALTER COLUMN deviceName DROP NOT NULL,
ALTER COLUMN platform DROP NOT NULL;

COMMIT;

