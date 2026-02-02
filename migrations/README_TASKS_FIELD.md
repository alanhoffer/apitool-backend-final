# Migración: Agregar campo 'tasks' a apiary_setting

## Descripción

Esta migración agrega el campo `tasks` (TEXT, nullable) a la tabla `apiary_setting` para almacenar tareas en formato JSON.

## Ejecutar Migración

### Opción 1: Desde el servidor (recomendado)

```bash
cd /home/bija/projects/apicultura/apitool-fastapi
psql -h 192.168.1.139 -U bija -d apitool1 -f migrations/add_tasks_field.sql
```

### Opción 2: Desde línea de comandos directa

```bash
psql -h 192.168.1.139 -U bija -d apitool1 -c "ALTER TABLE apiary_setting ADD COLUMN IF NOT EXISTS tasks TEXT NULL;"
```

## Verificar Migración

```bash
psql -h 192.168.1.139 -U bija -d apitool1 -c "\d apiary_setting"
```

Deberías ver la columna `tasks` en la lista de columnas.

## Rollback (si es necesario)

```sql
ALTER TABLE apiary_setting DROP COLUMN IF EXISTS tasks;
```

## Nota

Esta migración es **idempotente** - puede ejecutarse múltiples veces sin causar errores.

