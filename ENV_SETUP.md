# Configuración de Variables de Entorno

## Archivo .env

Crea un archivo `.env` en la raíz del proyecto con las siguientes variables:

```env
# Database Configuration
DB_HOST=192.168.1.139
DB_PORT=5432
DB_USER=bija
DB_PASSWORD=your_password_here
DB_NAME=apitool1

# JWT Configuration (IMPORTANT: Change this in production!)
JWT_SECRET=your_secret_key_here_minimum_32_characters
JWT_ALGORITHM=HS256
JWT_EXPIRATION_DAYS=365

# Bcrypt
BCRYPT_SALT_ROUNDS=10

# Weather API
WEATHER_API_KEY=your_weather_api_key_here

# CORS Configuration
# For production, specify allowed origins separated by commas
# Example: CORS_ORIGINS=https://example.com,https://app.example.com
# Use * for development only (not recommended for production)
CORS_ORIGINS=*

# Base URL
BASE_URL=http://apitoolbackend.ddns.net:5173/

# Logging Configuration
LOG_LEVEL=INFO
JSON_LOGGING=false
```

## Notas Importantes

1. **JWT_SECRET**: 
   - En producción, DEBE ser un string aleatorio y seguro de al menos 32 caracteres
   - Puedes generar uno con: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
   - Si no se configura, se generará uno automáticamente (solo para desarrollo)

2. **CORS_ORIGINS**:
   - En desarrollo puedes usar `*` para permitir todos los orígenes
   - En producción, especifica los orígenes permitidos separados por comas
   - Ejemplo: `CORS_ORIGINS=https://app.example.com,https://admin.example.com`

3. **Logging**:
   - `LOG_LEVEL`: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
   - `JSON_LOGGING`: Si usar formato JSON estructurado (`true`/`false`)
   - Para producción, considera usar `JSON_LOGGING=true` para mejor integración con sistemas de logging

4. **Seguridad**:
   - NUNCA commitees el archivo `.env` al repositorio
   - El archivo `.env` ya está en `.gitignore`
   - Usa diferentes valores para desarrollo y producción

## Generar JWT_SECRET

Para generar un JWT_SECRET seguro:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

O usando OpenSSL:

```bash
openssl rand -hex 32
```

