-- Tabla de guías (gestionables desde el panel admin).
-- Normalmente la crea create_all() al iniciar; este script es respaldo/manual.

CREATE TABLE IF NOT EXISTS guide (
    id          SERIAL PRIMARY KEY,
    title       VARCHAR(150) NOT NULL,
    description VARCHAR(500),
    content     TEXT NOT NULL,
    category    VARCHAR(60),
    "readTime"  VARCHAR(20),
    icon        VARCHAR(60),
    color       VARCHAR(20),
    featured    BOOLEAN DEFAULT FALSE,
    date        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Rollback: DROP TABLE IF EXISTS guide;
