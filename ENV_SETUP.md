# Configuracion de Variables de Entorno

## Paso recomendado

1. Copia `.env.example` a `.env`
2. Reemplaza todos los placeholders antes de arrancar la API

```env
APP_ENV=development
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=change-me
DB_NAME=apitool1
JWT_SECRET=replace-with-a-long-random-secret
JWT_ALGORITHM=HS256
JWT_EXPIRATION_DAYS=365
BCRYPT_SALT_ROUNDS=10
WEATHER_API_KEY=replace-with-your-weather-api-key
CORS_ORIGINS=*
BASE_URL=http://localhost:3000/
LOG_LEVEL=INFO
JSON_LOGGING=false
```

## Reglas importantes

1. `JWT_SECRET`
- Es obligatorio fuera de testing.
- Usa al menos 32 caracteres aleatorios.

2. `DB_PASSWORD`
- `change-me` es solo placeholder.
- No lo uses en entornos reales.

3. `WEATHER_API_KEY`
- Si no esta definida, `/weather` devolvera `503`.

4. `TESTING=1`
- Activa un secret JWT fijo de testing y evita romper la suite automatizada.

5. `CORS_ORIGINS`
- Usa `*` solo en desarrollo local.
- En produccion define dominios explicitos separados por coma.

## Generar un JWT_SECRET

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```
