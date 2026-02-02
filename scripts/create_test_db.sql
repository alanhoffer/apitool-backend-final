-- Script SQL para crear la base de datos de testing
-- Ejecutar como superusuario de PostgreSQL
-- Ejemplo: psql -h 192.168.1.139 -U postgres -f scripts/create_test_db.sql

-- Crear la base de datos (si no existe)
CREATE DATABASE apitool1_test;

-- Conceder permisos al usuario
GRANT ALL PRIVILEGES ON DATABASE apitool1_test TO bija;

-- Mensaje de confirmación
SELECT 'Base de datos apitool1_test creada exitosamente' AS message;

