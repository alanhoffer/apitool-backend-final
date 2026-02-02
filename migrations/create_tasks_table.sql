-- Migración: Crear tabla de tareas (tasks)
-- Descripción: Tabla para almacenar tareas asociadas a usuarios y opcionalmente a apiarios.

BEGIN;

CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    completed BOOLEAN DEFAULT FALSE,
    due_date TIMESTAMP,
    user_id INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    apiary_id INTEGER REFERENCES apiary(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indices para búsqueda rápida
CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id);
CREATE INDEX IF NOT EXISTS idx_tasks_apiary_id ON tasks(apiary_id);
CREATE INDEX IF NOT EXISTS idx_tasks_completed ON tasks(completed);

-- Función para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_tasks_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para updated_at
DROP TRIGGER IF EXISTS trigger_update_tasks_updated_at ON tasks;
CREATE TRIGGER trigger_update_tasks_updated_at
    BEFORE UPDATE ON tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_tasks_updated_at();

COMMIT;
