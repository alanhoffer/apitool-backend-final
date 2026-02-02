# Configuración de Base de Datos de Testing

## Descripción

Esta guía explica cómo crear y configurar una base de datos de testing separada para ejecutar tests sin afectar la base de datos de producción.

## Requisitos

- PostgreSQL instalado y corriendo
- Acceso a la base de datos PostgreSQL con permisos para crear bases de datos
- Python 3.8+

## Crear Base de Datos de Testing

### Opción 1: Usando SQL como Superusuario (Recomendado)

Si no tienes permisos para crear bases de datos, ejecuta como superusuario:

```bash
# Conectar como postgres (superusuario)
psql -h 192.168.1.139 -U postgres

# O ejecutar el script SQL directamente
psql -h 192.168.1.139 -U postgres -f scripts/create_test_db.sql
```

Luego ejecuta el script Python para crear las tablas y migraciones:

```bash
python scripts/create_test_db.py
```

### Opción 2: Usando el Script Automático

Si tienes permisos para crear bases de datos:

```bash
python scripts/create_test_db.py
```

Este script:
1. Crea la base de datos `apitool1_test`
2. Crea todas las tablas desde los modelos SQLAlchemy
3. Ejecuta las migraciones necesarias

### Opción 3: Manualmente con psql

```bash
# Conectar a PostgreSQL
psql -h 192.168.1.139 -U bija -d postgres

# Crear la base de datos
CREATE DATABASE apitool1_test;

# Salir
\q
```

Luego ejecutar las migraciones:

```bash
# Configurar variable de entorno
export DB_NAME=apitool1_test

# Ejecutar migraciones
python scripts/create_test_db.py
```

## Configurar Variables de Entorno para Testing

### Opción 1: Archivo .env.test

1. Copiar el archivo de ejemplo:
```bash
cp .env.test.example .env.test
```

2. Editar `.env.test` con tus valores:
```env
DB_NAME=apitool1_test
DB_HOST=192.168.1.139
DB_PORT=5432
DB_USER=bija
DB_PASSWORD=tu_password
```

3. Cargar las variables antes de ejecutar tests:
```bash
# En Linux/Mac
export $(cat .env.test | xargs)
pytest

# En Windows PowerShell
Get-Content .env.test | ForEach-Object {
    if ($_ -match '^([^#][^=]+)=(.*)$') {
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2], 'Process')
    }
}
pytest
```

### Opción 2: Variables de Entorno Directas

```bash
# Linux/Mac
export DB_NAME=apitool1_test
pytest

# Windows PowerShell
$env:DB_NAME="apitool1_test"
pytest
```

### Opción 3: Modificar conftest.py

Puedes modificar `tests/conftest.py` para usar automáticamente la DB de testing:

```python
import os
os.environ['DB_NAME'] = 'apitool1_test'
```

## Ejecutar Tests

Una vez configurada la DB de testing:

```bash
# Ejecutar todos los tests
pytest

# Ejecutar tests específicos
pytest tests/test_auth.py

# Con verbose
pytest -v

# Con coverage
pytest --cov=app tests/
```

## Limpiar Base de Datos de Testing

### Opción 1: Script Automático

```bash
python scripts/drop_test_db.py
```

### Opción 2: Manualmente

```bash
psql -h 192.168.1.139 -U bija -d postgres

DROP DATABASE apitool1_test;
```

## Fixtures de Testing

El archivo `tests/conftest.py` puede configurarse para:

1. **Usar DB de testing automáticamente**:
```python
import os
import pytest
from app.database import engine, Base

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Configura la DB de testing antes de todos los tests."""
    os.environ['DB_NAME'] = 'apitool1_test'
    # Crear tablas
    Base.metadata.create_all(bind=engine)
    yield
    # Limpiar después de todos los tests
    Base.metadata.drop_all(bind=engine)
```

2. **Transacciones por test**:
```python
@pytest.fixture
def db_session():
    """Crea una sesión de DB con rollback automático."""
    from app.database import SessionLocal
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()
```

## Mejores Prácticas

1. **Nunca usar la DB de producción para tests**
   - Siempre usar una DB separada
   - Verificar que `DB_NAME` apunte a `apitool1_test`

2. **Limpiar datos entre tests**
   - Usar transacciones con rollback
   - O limpiar tablas específicas en fixtures

3. **Datos de prueba consistentes**
   - Usar fixtures para crear datos de prueba
   - Mantener datos de prueba en `tests/fixtures/`

4. **Aislamiento de tests**
   - Cada test debe ser independiente
   - No depender del orden de ejecución

## Troubleshooting

### Error: "database does not exist"
- Verificar que la DB de testing fue creada
- Ejecutar `python scripts/create_test_db.py`

### Error: "permission denied"
- Verificar que el usuario tiene permisos para crear bases de datos
- O crear la DB manualmente como superusuario

### Error: "table already exists"
- La DB puede tener datos de ejecuciones anteriores
- Considerar recrear la DB: `python scripts/drop_test_db.py && python scripts/create_test_db.py`

### Tests lentos
- Usar transacciones en lugar de commits reales
- Usar `pytest-xdist` para ejecutar tests en paralelo

## Integración Continua (CI)

Para CI/CD, puedes configurar:

```yaml
# .github/workflows/test.yml
- name: Create test database
  run: |
    python scripts/create_test_db.py
    
- name: Run tests
  run: |
    pytest --cov=app tests/
```

## Notas Adicionales

- La DB de testing se crea con el mismo esquema que producción
- Las migraciones se ejecutan automáticamente
- Los datos de testing se pueden limpiar fácilmente
- No afecta la base de datos de producción

