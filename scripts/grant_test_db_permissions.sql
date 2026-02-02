-- Script para otorgar permisos al usuario bija en la base de datos de testing
-- Ejecutar como superusuario: psql -h 192.168.1.139 -U postgres -d apitool1_test -f scripts/grant_test_db_permissions.sql

-- Conceder permisos en el schema public
GRANT ALL ON SCHEMA public TO bija;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO bija;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO bija;

-- Hacer al usuario dueño del schema (opcional, pero más permisivo)
-- ALTER SCHEMA public OWNER TO bija;

SELECT 'Permisos otorgados exitosamente al usuario bija' AS message;

