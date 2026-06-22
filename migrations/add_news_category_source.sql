-- Migración: agrega categoría y fuente a las noticias (aditiva, reversible).
-- Las columnas son NULLABLE, por lo que no rompe filas ni el servidor desplegado
-- con el modelo anterior (SQLAlchemy ignora columnas no mapeadas).

ALTER TABLE news ADD COLUMN IF NOT EXISTS category VARCHAR(50);
ALTER TABLE news ADD COLUMN IF NOT EXISTS source   VARCHAR(100);

-- Rollback:
-- ALTER TABLE news DROP COLUMN IF EXISTS category;
-- ALTER TABLE news DROP COLUMN IF EXISTS source;
