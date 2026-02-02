-- Migración para agregar el campo 'tasks' a la tabla apiary_setting
-- Ejecutar como: psql -h 192.168.1.139 -U bija -d apitool1 -f migrations/add_tasks_field.sql

-- Agregar columna tasks si no existe
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'apiary_setting' 
        AND column_name = 'tasks'
    ) THEN
        ALTER TABLE apiary_setting 
        ADD COLUMN tasks TEXT NULL;
        
        RAISE NOTICE 'Columna tasks agregada exitosamente a apiary_setting';
    ELSE
        RAISE NOTICE 'La columna tasks ya existe en apiary_setting';
    END IF;
END $$;

-- Verificar que la columna fue creada
SELECT 
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns
WHERE table_name = 'apiary_setting' 
AND column_name = 'tasks';

