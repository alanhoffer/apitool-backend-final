-- Noticias de ejemplo para validar la sección "Noticias" del Home.
-- Ejecutar DESPUÉS de add_news_category_source.sql.
-- Son borrables: ver el DELETE al final.

INSERT INTO news (title, content, category, source, image, date) VALUES
('Cómo proteger tus colmenas del ácaro Varroa este otoño',
 'Guía práctica de tratamientos y monitoreo para reducir la carga de Varroa antes de la invernada.',
 'Sanidad', 'Revista Apícola', NULL, NOW() - INTERVAL '2 days'),
('Nueva normativa de etiquetado de miel 2026',
 'El boletín oficial publicó los nuevos requisitos de etiquetado para la comercialización de miel.',
 'Normativa', 'Boletín Oficial', NULL, NOW() - INTERVAL '5 days'),
('Buenas prácticas de alimentación invernal',
 'Recomendaciones sobre jarabes y suplementos para mantener colonias fuertes durante el invierno.',
 'Manejo', 'Apitool', NULL, NOW() - INTERVAL '8 days');

-- Rollback de estos ejemplos:
-- DELETE FROM news WHERE source IN ('Revista Apícola','Boletín Oficial','Apitool')
--   AND title IN (
--     'Cómo proteger tus colmenas del ácaro Varroa este otoño',
--     'Nueva normativa de etiquetado de miel 2026',
--     'Buenas prácticas de alimentación invernal');
