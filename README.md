# API Tool - FastAPI

Migración del proyecto NestJS a FastAPI.

## Instalación

1. Crear un entorno virtual:
```bash
python -m venv venv
```

2. Activar el entorno virtual:
- Windows: `venv\Scripts\activate`
- Linux/Mac: `source venv/bin/activate`

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

## Configuración

Crear un archivo `.env` en la raíz del proyecto con las siguientes variables (opcional, ya están en config.py como valores por defecto):

```
DB_HOST=192.168.1.149
DB_PORT=5432
DB_USER=bija
DB_PASSWORD=15441109Gordo.
DB_NAME=apitool1
WEATHER_API_KEY=3389c5ddfc124bf4a1c00055242909
```

## Ejecución

```bash
uvicorn app.main:app --reload --port 3000
```

El servidor estará disponible en `http://localhost:3000`

## Testing

Para ejecutar los tests:

```bash
# Ejecutar todos los tests
pytest

# Ejecutar tests con cobertura
pytest --cov=app --cov-report=html

# Ejecutar tests específicos
pytest tests/services/test_user_service.py

# Ejecutar tests en modo verbose
pytest -v
```

Los reportes de cobertura se generarán en `htmlcov/index.html`

## Documentación

Una vez que el servidor esté corriendo, puedes acceder a:
- Swagger UI: `http://localhost:3000/docs`
- ReDoc: `http://localhost:3000/redoc`

## Estructura del Proyecto

```
fastapi-project/
├── app/
│   ├── __init__.py
│   ├── main.py              # Punto de entrada de la aplicación
│   ├── config.py            # Configuración
│   ├── database.py          # Configuración de base de datos
│   ├── constants.py         # Constantes
│   ├── dependencies.py      # Dependencias (guards, autenticación)
│   ├── cron.py              # Tareas programadas
│   ├── models/              # Modelos SQLAlchemy (entidades)
│   ├── schemas/             # Schemas Pydantic (DTOs)
│   ├── routers/             # Routers (controladores)
│   └── services/            # Servicios (lógica de negocio)
├── tests/                   # Tests
│   ├── conftest.py          # Configuración de pytest y fixtures
│   ├── services/            # Tests de servicios
│   ├── routers/             # Tests de endpoints
│   ├── test_integration.py  # Tests de integración
│   └── test_main.py         # Tests del main
├── uploads/                 # Archivos subidos
├── requirements.txt
├── pytest.ini               # Configuración de pytest
└── README.md
```

## Endpoints Principales

- `/auth/login` - Iniciar sesión
- `/auth/register` - Registrarse
- `/auth/profile` - Perfil del usuario autenticado
- `/users` - Obtener usuario actual
- `/apiarys` - CRUD de apiarios
- `/news` - CRUD de noticias
- `/weather` - Obtener información del clima

## Notas

- La autenticación utiliza JWT tokens
- Los tokens expiran después de 365 días
- Las tareas cron se ejecutan diariamente a medianoche
- Los archivos se suben a la carpeta `uploads/`
- Los tests utilizan una base de datos SQLite en memoria para aislamiento

## Tests

El proyecto incluye una suite completa de tests:

- **Tests de Servicios**: Validan la lógica de negocio
- **Tests de Routers**: Validan los endpoints HTTP
- **Tests de Integración**: Validan flujos completos
- **Fixtures**: Datos de prueba reutilizables

Para ejecutar los tests con cobertura:
```bash
pytest --cov=app --cov-report=html
```
