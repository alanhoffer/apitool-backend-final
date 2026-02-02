# Documentación de Tareas (Tasks)

## Descripción
Se ha implementado un sistema completo de gestión de tareas que permite a los usuarios crear, leer, actualizar y eliminar tareas. Las tareas pueden ser generales o estar asociadas a un apiario específico.

## Modelo de Datos (Base de Datos)

Tabla `tasks`:
- `id`: PK (Integer)
- `title`: Título de la tarea (String, requerido)
- `description`: Descripción detallada (Text, opcional)
- `completed`: Estado de la tarea (Boolean, default: false)
- `due_date`: Fecha de vencimiento (Timestamp, opcional)
- `user_id`: ID del usuario propietario (FK, requerido)
- `apiary_id`: ID del apiario asociado (FK, opcional)
- `created_at`: Fecha de creación
- `updated_at`: Fecha de última actualización

## Endpoints de la API

Base URL: `/tasks`

### 1. Crear Tarea
**POST** `/tasks`
Body:
```json
{
  "title": "Revisar colmena 5",
  "description": "Verificar presencia de reina",
  "due_date": "2024-05-20T10:00:00",
  "apiary_id": 123
}
```

### 2. Listar Tareas
**GET** `/tasks`
Parámetros (Query Params):
- `page`: Número de página (default: 1)
- `limit`: Resultados por página (default: 50)
- `apiary_id`: Filtrar por apiario específico
- `completed`: Filtrar por estado (true/false)

Ejemplo: `/tasks?completed=false&apiary_id=123`

### 3. Obtener Tarea
**GET** `/tasks/{id}`

### 4. Actualizar Tarea
**PUT** `/tasks/{id}`
Body (campos opcionales):
```json
{
  "completed": true,
  "description": "Nueva descripción"
}
```

### 5. Eliminar Tarea
**DELETE** `/tasks/{id}`

## Instalación / Migración

1. Ejecutar el script SQL de migración en la base de datos:
   ```bash
   psql -h <host> -U <user> -d <db> -f migrations/create_tasks_table.sql
   ```
   
2. O reiniciar el servidor API, ya que `main.py` intenta crear las tablas automáticamente si no existen (gracias a SQLAlchemy `create_all`).

## Frontend Integration Tips

- Utilizar el endpoint `GET /tasks` para poblar la lista.
- Permitir filtrar por completadas/pendientes.
- Si se está en la vista de un apiario, filtrar por `apiary_id`.
- Usar `PUT` para marcar como completada (checkbox).
