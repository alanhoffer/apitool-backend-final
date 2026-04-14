-- Migración: Crear tabla de suscripciones
-- Tiers: aprendiz (5 apiarios, sin IA), apicultor (20 apiarios, IA limitada), maestro (ilimitado, IA completa)

BEGIN;

CREATE TABLE IF NOT EXISTS subscription (
    id SERIAL PRIMARY KEY,
    "userId" INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    tier VARCHAR(20) NOT NULL DEFAULT 'aprendiz',
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    "revenuecatCustomerId" VARCHAR(255),
    "expiresAt" TIMESTAMP,
    "createdAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE ("userId")
);

CREATE INDEX IF NOT EXISTS idx_subscription_user_id ON subscription("userId");
CREATE INDEX IF NOT EXISTS idx_subscription_tier ON subscription(tier);

-- Insertar suscripción aprendiz para todos los usuarios existentes que no tengan una
INSERT INTO subscription ("userId", tier, status)
SELECT id, 'aprendiz', 'active'
FROM "user"
WHERE id NOT IN (SELECT "userId" FROM subscription);

COMMIT;
