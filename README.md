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
- `CRON_SECRET`
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
La API ahora tambien devuelve `imageUrl` cuando ya conoce una URL publica, para que mobile/web eviten pasar por ese endpoint legado y no gasten invocaciones innecesarias.

Importante:

- En Vercel no conviene correr el scheduler interno de APScheduler; por eso debe quedar en `false`.
- `uploads/` no es persistente en Vercel. Si no hay `BLOB_READ_WRITE_TOKEN`, la API cae en almacenamiento local solo para desarrollo/testing.
- Los jobs HTTP se configuran desde [vercel.json](/C:/Users/anxio/OneDrive/Escritorio/APICULTURA/apitool-fastapi/vercel.json) y llaman a `GET /internal/cron/<job-name>`.
- Configura `CRON_SECRET` en el proyecto de Vercel. Vercel enviara `Authorization: Bearer <CRON_SECRET>` automaticamente al disparar el cron.
- Los horarios de `vercel.json` estan expresados en UTC. Si queres alinearlos con Paraguay, ajustalos cuando cambie tu ventana operativa.

## Deploy en OVH / VPS

Tambien deje preparada una ruta de migracion a VPS en [deploy/ovh/README.md](/C:/Users/anxio/OneDrive/Escritorio/APICULTURA/apitool-fastapi/deploy/ovh/README.md).

Incluye:

- `docker-compose.prod.yml`
- `.env.vps.example`
- configuracion base de `Nginx`
- backup rapido de Postgres

En VPS ya no hace falta depender de `vercel.json` para jobs: el scheduler interno vuelve a correr con `ENABLE_SCHEDULER=true`.

Antes de un corte a VPS o una base productiva vieja conviene aplicar tambien [migrations/add_performance_indexes.sql](/C:/Users/anxio/OneDrive/Escritorio/APICULTURA/apitool-fastapi/migrations/add_performance_indexes.sql). Igual deje los mismos indices en `ensure_runtime_schema_compatibility()` para que una base existente los cree de forma idempotente en el arranque.

## Jobs automaticos

Jobs productivos disponibles:

- `GET /internal/cron/apiary-maintenance`: descuenta alimento y baja un dia a los tratamientos automáticos.
- `GET /internal/cron/apiary-alerts`: crea alertas para apiarios con mas de 30 dias sin actividad.
- `GET /internal/cron/task-reminders`: genera recordatorios para tareas vencidas o que vencen dentro de 24 horas.
- `GET /internal/cron/subscription-reminders`: avisa cuando una suscripcion premium vence en 7, 3 o 1 dia.
- `GET /internal/cron/subscription-reconciliation`: marca como expiradas las suscripciones activas cuyo `expiresAt` ya paso.
- `GET /internal/cron/push-token-cleanup`: limpia tokens push invalidos y borra dispositivos viejos sin token.
- `GET /internal/cron/weekly-digest`: crea un resumen semanal con tareas pendientes, vencidas y apiarios desatendidos.
- `GET /internal/cron/daily`: endpoint manual de conveniencia que ejecuta el bloque diario principal en una sola llamada.

Plan sugerido en Vercel:

- `apiary-maintenance`: diario
- `apiary-alerts`: diario, unos minutos despues
- `task-reminders`: diario, por la mañana
- `subscription-reminders`: diario
- `subscription-reconciliation`: diario
- `push-token-cleanup`: semanal
- `weekly-digest`: semanal

Los jobs nuevos estan pensados para que la campana de notificaciones no dependa solo del abandono de apiarios.

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
- Existen jobs HTTP para Vercel y jobs locales equivalentes via APScheduler cuando `ENABLE_SCHEDULER=true`
- Los archivos se suben a `uploads/`
- Los tests usan SQLite en memoria

## Recomendaciones estacionales

El endpoint `GET /recommendations` ya devuelve recomendaciones segun la estacion actual del hemisferio sur por defecto. La logica vive en [app/services/recommendations_service.py](/C:/Users/anxio/OneDrive/Escritorio/APICULTURA/apitool-fastapi/app/services/recommendations_service.py).

Para llevarlo a nivel apiario se puede extender sin cambiar de arquitectura:

- inferir hemisferio por latitud del apiario
- mezclar estacion + clima actual + estado del apiario
- priorizar tips por contexto real, por ejemplo alimento bajo, tratamientos proximos a vencer o falta de visitas

La base para hacerlo ya existe; faltaria agregar un endpoint especifico por apiario y reglas de priorizacion.
