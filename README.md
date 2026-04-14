# API Tool - FastAPI

Migracion del proyecto NestJS a FastAPI.

## Instalacion

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

## Configuracion

1. Copiar [` .env.example`](/C:/Users/anxio/OneDrive/Escritorio/APICULTURA/apitool-fastapi/.env.example) a `.env`
2. Completar las variables reales antes de correr la API

Variables minimas recomendadas:

```env
APP_ENV=development
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=change-me
DB_NAME=apitool1
JWT_SECRET=replace-with-a-long-random-secret
WEATHER_API_KEY=replace-with-your-weather-api-key
BASE_URL=http://localhost:3000/
```

Notas:
- `JWT_SECRET` ya no se genera aleatoriamente en runtime fuera de testing.
- `WEATHER_API_KEY` es opcional, pero `/weather` respondera `503` si no esta configurada.
- `TESTING=1` usa un secret fijo de testing para no romper la suite automatizada.

## Ejecucion

```bash
uvicorn app.main:app --reload --port 3000
```

El servidor estara disponible en `http://localhost:3000`

## Testing

```bash
pytest
pytest --cov=app --cov-report=html
pytest tests/services/test_user_service.py
pytest -v
```

Los reportes de cobertura se generan en `htmlcov/index.html`

## Documentacion

- Swagger UI: `http://localhost:3000/docs`
- ReDoc: `http://localhost:3000/redoc`

## Deploy en Vercel

El repo incluye `vercel.json` y `api/index.py` para exponer la app FastAPI en Vercel.

Si tu proyecto de Vercel ya esta conectado a GitHub, el flujo normal es:

1. Hacer commit de los cambios que quieras publicar
2. Ejecutar `git push origin main`
3. Esperar el deploy automatico de Vercel

Si el proyecto no esta conectado al repo, podes desplegar manualmente con CLI:

```bash
vercel
vercel --prod
```

Variables minimas recomendadas en Vercel:

- `APP_ENV=production`
- `DB_HOST`
- `DB_PORT`
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME`
- `JWT_SECRET`
- `CORS_ORIGINS`
- `BASE_URL`
- `WEATHER_API_KEY` si usas `/weather`
- `OPENAI_API_KEY` si usas audio/IA
- `ENABLE_SCHEDULER=false`
- `BLOB_READ_WRITE_TOKEN`

Para imagenes de apiarios con Vercel Blob:

1. Crear un Blob store publico desde el proyecto
2. Verificar que Vercel agregue `BLOB_READ_WRITE_TOKEN`
3. Redeployar
4. Si ya tenes imagenes locales previas, migrarlas con:

```bash
python scripts/migrate_apiary_images_to_blob.py
```

Las imagenes nuevas se guardan en Vercel Blob bajo `apiarys/...` y el endpoint legado `/apiarys/profile/image/...` redirige a la URL publica del blob.

Importante:

- En Vercel no conviene correr el scheduler interno de APScheduler; por eso debe quedar en `false`.
- `uploads/` no es persistente en Vercel. Si no hay `BLOB_READ_WRITE_TOKEN`, la API cae en almacenamiento local solo para desarrollo/testing.

## Endpoints principales

- `/auth/login`
- `/auth/register`
- `/auth/profile`
- `/users`
- `/apiarys`
- `/news`
- `/weather`

## Notas

- La autenticacion usa JWT
- Los tokens expiran despues de 365 dias
- Las tareas cron se ejecutan diariamente a medianoche
- Los archivos se suben a `uploads/`
- Los tests usan SQLite en memoria
