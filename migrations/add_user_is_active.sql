-- Agrega is_active a usuarios (para activar/desactivar cuentas desde el panel admin).
-- Aditiva, default TRUE (las cuentas existentes quedan activas).
ALTER TABLE "user" ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;

-- Rollback: ALTER TABLE "user" DROP COLUMN IF EXISTS is_active;
