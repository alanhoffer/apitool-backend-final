-- Migración: Agregar campos adicionales a la tabla devices
-- Fecha: 2024-01-XX
-- Descripción: Agrega campos para información completa del dispositivo según DEVICES_API.md

BEGIN;

-- 1. Primero, actualizar registros existentes que puedan tener NULL en campos requeridos
-- Asignar valores por defecto si deviceName o platform son NULL
UPDATE devices 
SET "deviceName" = COALESCE("deviceName", 'Unknown Device')
WHERE "deviceName" IS NULL;

UPDATE devices 
SET "platform" = COALESCE("platform", 'unknown')
WHERE "platform" IS NULL;

-- 2. Agregar nuevos campos (todos nullable inicialmente)
ALTER TABLE devices 
ADD COLUMN IF NOT EXISTS "modelName" VARCHAR,
ADD COLUMN IF NOT EXISTS "brand" VARCHAR,
ADD COLUMN IF NOT EXISTS "manufacturer" VARCHAR,
ADD COLUMN IF NOT EXISTS "osVersion" VARCHAR,
ADD COLUMN IF NOT EXISTS "deviceType" VARCHAR,
ADD COLUMN IF NOT EXISTS "appVersion" VARCHAR,
ADD COLUMN IF NOT EXISTS "buildVersion" VARCHAR,
ADD COLUMN IF NOT EXISTS "updatedAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- 3. Agregar trigger para actualizar updatedAt automáticamente
CREATE OR REPLACE FUNCTION update_devices_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW."updatedAt" = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_devices_updated_at ON devices;
CREATE TRIGGER trigger_update_devices_updated_at
    BEFORE UPDATE ON devices
    FOR EACH ROW
    EXECUTE FUNCTION update_devices_updated_at();

-- 4. Modificar campos existentes para hacerlos NOT NULL
-- Primero asegurar que no haya NULLs
UPDATE devices SET "deviceName" = 'Unknown Device' WHERE "deviceName" IS NULL;
UPDATE devices SET "platform" = 'unknown' WHERE "platform" IS NULL;

-- Ahora hacer los campos NOT NULL
ALTER TABLE devices 
ALTER COLUMN "deviceName" SET NOT NULL,
ALTER COLUMN "platform" SET NOT NULL;

-- 5. Hacer expoPushToken nullable (ya debería serlo, pero por si acaso)
ALTER TABLE devices 
ALTER COLUMN "expoPushToken" DROP NOT NULL;

-- 6. Eliminar constraint unique de expoPushToken si existe
-- (ya que ahora puede haber múltiples dispositivos sin token)
-- Buscar el nombre real del constraint (PostgreSQL lo convierte a minúsculas)
DO $$ 
DECLARE
    constraint_name TEXT;
BEGIN
    SELECT conname INTO constraint_name
    FROM pg_constraint 
    WHERE conrelid = 'devices'::regclass
    AND contype = 'u'
    AND conkey::text LIKE '%expopushtoken%';
    
    IF constraint_name IS NOT NULL THEN
        EXECUTE format('ALTER TABLE devices DROP CONSTRAINT %I', constraint_name);
    END IF;
END $$;

-- 7. Crear índice único para (userId, deviceName, platform)
-- Primero eliminar si existe
DROP INDEX IF EXISTS idx_user_device_platform;

CREATE UNIQUE INDEX idx_user_device_platform 
ON devices ("userId", "deviceName", "platform");

-- 8. Actualizar updatedAt para registros existentes (solo si la columna existe)
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'devices' AND column_name = 'updatedAt'
    ) THEN
        UPDATE devices 
        SET "updatedAt" = COALESCE("updatedAt", "createdAt", CURRENT_TIMESTAMP)
        WHERE "updatedAt" IS NULL;
    END IF;
END $$;

COMMIT;

-- Verificación (ejecutar después de la migración para verificar)
-- SELECT 
--     column_name, 
--     data_type, 
--     is_nullable,
--     column_default
-- FROM information_schema.columns 
-- WHERE table_name = 'devices' 
-- ORDER BY ordinal_position;

