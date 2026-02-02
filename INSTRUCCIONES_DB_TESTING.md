# Instrucciones para Crear Base de Datos de Testing

## Situación Actual

El usuario `bija` no tiene permisos para crear bases de datos. Necesitas ejecutar el comando como superusuario (`postgres`).

## Opción 1: Crear la DB Manualmente (Recomendado)

### Paso 1: Conectar como superusuario

```bash
psql -h 192.168.1.139 -U postgres
```

Cuando te pida la contraseña, ingresa la contraseña del usuario `postgres`.

### Paso 2: Crear la base de datos

```sql
CREATE DATABASE apitool1_test;
```

### Paso 3: Conceder permisos al usuario bija

```sql
GRANT ALL PRIVILEGES ON DATABASE apitool1_test TO bija;
```

### Paso 4: Salir de psql

```sql
\q
```

### Paso 5: Ejecutar el script Python para crear tablas y migraciones

```bash
python scripts/create_test_db.py
```

Este script ahora solo creará las tablas y ejecutará las migraciones (ya que la DB ya existe).

---

## Opción 2: Usar el Script SQL

Si prefieres usar un script SQL:

```bash
psql -h 192.168.1.139 -U postgres -f scripts/create_test_db.sql
```

Luego ejecuta:

```bash
python scripts/create_test_db.py
```

---

## Opción 3: Pedir Permisos al Administrador

Si quieres que el usuario `bija` pueda crear bases de datos en el futuro, el administrador puede ejecutar:

```sql
ALTER USER bija CREATEDB;
```

---

## Verificar que la DB fue Creada

```bash
psql -h 192.168.1.139 -U bija -d apitool1_test -c "\dt"
```

Deberías ver las tablas creadas.

---

## Usar la DB de Testing

Una vez creada, puedes configurar las variables de entorno:

### Windows PowerShell:
```powershell
$env:DB_NAME="apitool1_test"
pytest
```

### Linux/Mac:
```bash
export DB_NAME=apitool1_test
pytest
```

O crear un archivo `.env.test` con:
```
DB_NAME=apitool1_test
```

---

## Eliminar la DB de Testing (si es necesario)

```bash
psql -h 192.168.1.139 -U postgres -c "DROP DATABASE apitool1_test;"
```

O usar el script:
```bash
python scripts/drop_test_db.py
```

