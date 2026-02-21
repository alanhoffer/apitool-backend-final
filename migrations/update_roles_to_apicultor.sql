-- Actualizar los usuarios existentes que tienen el rol 'user' al nuevo rol 'apicultor'
UPDATE user
SET role = 'apicultor'
WHERE role = 'user';
