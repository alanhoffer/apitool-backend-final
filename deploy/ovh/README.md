# Deploy en OVH VPS

Esta carpeta deja preparado el reemplazo del backend en Vercel por un VPS en OVH con:

- `FastAPI` corriendo en Docker
- `PostgreSQL` en el mismo VPS
- `Nginx` como reverse proxy
- scheduler interno activo (`ENABLE_SCHEDULER=true`)
- almacenamiento local persistente para `uploads/`

## Arquitectura sugerida

- `Nginx` en el host del VPS, exponiendo `80/443`
- `apitool-api` en Docker escuchando solo en `127.0.0.1:3000`
- `apitool-db` en Docker sin exponer `5432` a Internet
- backups externos de la base y, si queres, de `uploads`

## Lo que migra desde Vercel

- La API completa
- Jobs productivos: en VPS ya no dependemos de `vercel.json`; los ejecuta APScheduler dentro de la API
- Legal/support/account deletion: siguen servidos por FastAPI
- Imagenes: si no usas `BLOB_READ_WRITE_TOKEN`, el backend cae a almacenamiento local en `/app/uploads`

## Archivos incluidos

- `docker-compose.prod.yml`: stack de produccion
- `.env.vps.example`: variables de entorno sugeridas
- `nginx/apitool.conf.example`: server block base
- `scripts/backup_db.sh`: backup rapido de Postgres

## Preparacion en el VPS

1. Instalar Docker, Docker Compose plugin y Nginx
2. Clonar el repo en el VPS
3. Copiar `.env.vps.example` a `.env.vps`
4. Completar secretos reales:
   - `JWT_SECRET`
   - `DB_PASSWORD`
   - `CRON_SECRET`
   - `WEATHER_API_KEY`
   - `OPENAI_API_KEY` si vas a usar IA/audio
   - `REVENUECAT_WEBHOOK_SECRET` si usas suscripciones
5. Ajustar:
   - `BASE_URL`
   - `CORS_ORIGINS`
   - `RATE_LIMIT_TRUSTED_PROXIES` si usas una topologia distinta

## Levantar el stack

Desde `deploy/ovh/`:

```bash
cp .env.vps.example .env.vps
docker compose -f docker-compose.prod.yml --env-file .env.vps up -d --build
docker compose -f docker-compose.prod.yml --env-file .env.vps ps
```

## Configurar Nginx

1. Copiar `nginx/apitool.conf.example` a `/etc/nginx/sites-available/apitool.conf`
2. Reemplazar `api.tu-dominio.com` por el dominio real
3. Crear el symlink:

```bash
sudo ln -s /etc/nginx/sites-available/apitool.conf /etc/nginx/sites-enabled/apitool.conf
sudo nginx -t
sudo systemctl reload nginx
```

## TLS / HTTPS

Con el dominio ya apuntando al VPS:

```bash
sudo apt-get update
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d api.tu-dominio.com
```

Despues de eso, actualiza `BASE_URL=https://api.tu-dominio.com/` en `.env.vps` y reinicia el stack:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.vps up -d
```

## Health checks utiles

```bash
curl http://127.0.0.1:3000/health
curl https://api.tu-dominio.com/health
docker compose -f docker-compose.prod.yml --env-file .env.vps logs -f api
docker compose -f docker-compose.prod.yml --env-file .env.vps logs -f db
```

## Base de datos

En esta arquitectura, la base queda dentro del mismo VPS. Para la escala actual del proyecto, esto es razonable y simplifica bastante la operacion.

Importante:

- no abras `5432` hacia Internet
- usa backups diarios
- monitorea uso de disco y RAM

## Backups

Con `.env.vps` cargado:

```bash
export $(grep -v '^#' .env.vps | xargs)
./scripts/backup_db.sh
```

## Cambio de dominio en la app mobile

La app ahora soporta `extra.apiBaseUrl` en [app.json](/C:/Users/anxio/OneDrive/Escritorio/APICULTURA/apitool-alpha-reactnative/app.json).

Para pasar de Vercel a OVH:

1. cambia `apiBaseUrl`
2. rebuild de Android
3. valida login, apiarios, imagenes, notificaciones y legal pages

## Checklist de corte desde Vercel

1. levantar VPS y validar `/health`
2. migrar variables de entorno
3. confirmar DB y datos
4. confirmar uploads o estrategia de imagenes
5. cambiar `apiBaseUrl` en mobile
6. redeploy/rebuild de la app
7. cambiar DNS
8. smoke test completo
9. dejar Vercel en standby unos dias antes de apagarlo del todo
