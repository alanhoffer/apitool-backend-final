#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para crear y configurar una base de datos de testing.
"""
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from app.config import settings

# Configuración de la DB de testing
TEST_DB_NAME = "apitool1_test"
TEST_DB_HOST = settings.db_host
TEST_DB_PORT = settings.db_port
TEST_DB_USER = settings.db_user
TEST_DB_PASSWORD = settings.db_password

def create_test_database():
    """Crea la base de datos de testing."""
    try:
        # Conectar a PostgreSQL (sin especificar base de datos)
        conn = psycopg2.connect(
            host=TEST_DB_HOST,
            port=TEST_DB_PORT,
            user=TEST_DB_USER,
            password=TEST_DB_PASSWORD,
            database="postgres"  # Conectar a la DB por defecto
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Verificar si la base de datos ya existe
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (TEST_DB_NAME,)
        )
        exists = cursor.fetchone()
        
        if exists:
            print(f"[INFO] La base de datos '{TEST_DB_NAME}' ya existe.")
            response = input("¿Deseas eliminarla y recrearla? (s/N): ")
            if response.lower() == 's':
                # Terminar conexiones activas
                cursor.execute(
                    f"""
                    SELECT pg_terminate_backend(pg_stat_activity.pid)
                    FROM pg_stat_activity
                    WHERE pg_stat_activity.datname = '{TEST_DB_NAME}'
                    AND pid <> pg_backend_pid();
                    """
                )
                # Eliminar la base de datos
                cursor.execute(f'DROP DATABASE "{TEST_DB_NAME}";')
                print(f"[OK] Base de datos '{TEST_DB_NAME}' eliminada.")
            else:
                print("[INFO] Manteniendo la base de datos existente.")
                cursor.close()
                conn.close()
                return True
        
        # Intentar crear la base de datos
        try:
            cursor.execute(f'CREATE DATABASE "{TEST_DB_NAME}";')
            print(f"[OK] Base de datos '{TEST_DB_NAME}' creada exitosamente.")
        except psycopg2.errors.InsufficientPrivilege:
            print(f"[ERROR] No tienes permisos para crear bases de datos.")
            print(f"[INFO] Ejecuta manualmente como superusuario:")
            print(f"      psql -h {TEST_DB_HOST} -U postgres -f scripts/create_test_db.sql")
            print(f"      O ejecuta: CREATE DATABASE {TEST_DB_NAME};")
            cursor.close()
            conn.close()
            return False
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.Error as e:
        if "permission denied" in str(e).lower() or "insufficient" in str(e).lower():
            print(f"[ERROR] No tienes permisos para crear bases de datos.")
            print(f"[INFO] Ejecuta manualmente como superusuario:")
            print(f"      psql -h {TEST_DB_HOST} -U postgres -f scripts/create_test_db.sql")
            print(f"      O ejecuta: CREATE DATABASE {TEST_DB_NAME};")
        else:
            print(f"[ERROR] Error al crear la base de datos: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Error inesperado: {e}")
        return False

def run_migrations():
    """Ejecuta las migraciones en la base de datos de testing."""
    from app.database import create_engine
    from sqlalchemy import text
    import os
    
    # Crear engine para la DB de testing
    test_db_url = f"postgresql://{TEST_DB_USER}:{TEST_DB_PASSWORD}@{TEST_DB_HOST}:{TEST_DB_PORT}/{TEST_DB_NAME}"
    engine = create_engine(test_db_url)
    
    # Ejecutar migraciones
    migration_files = [
        'migrations/add_device_fields.sql'
    ]
    
    for migration_file in migration_files:
        if not os.path.exists(migration_file):
            print(f"[WARN] Archivo de migración no encontrado: {migration_file}")
            continue
        
        print(f"[INFO] Ejecutando migración: {migration_file}")
        try:
            with open(migration_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            with engine.connect() as conn:
                conn.execute(text(sql_content))
                conn.commit()
            print(f"[OK] Migración '{migration_file}' ejecutada exitosamente.")
        except Exception as e:
            print(f"[ERROR] Error al ejecutar migración '{migration_file}': {e}")
            return False
    
    return True

def create_tables():
    """Crea las tablas usando SQLAlchemy models."""
    from app.database import Base, create_engine
    
    test_db_url = f"postgresql://{TEST_DB_USER}:{TEST_DB_PASSWORD}@{TEST_DB_HOST}:{TEST_DB_PORT}/{TEST_DB_NAME}"
    engine = create_engine(test_db_url)
    
    print("[INFO] Creando tablas desde modelos SQLAlchemy...")
    try:
        # Importar todos los modelos para que SQLAlchemy los registre
        from app.models import user, apiary, device, settings, history, news, notification, recommendations, drum
        
        Base.metadata.create_all(bind=engine)
        print("[OK] Tablas creadas exitosamente.")
        return True
    except Exception as e:
        print(f"[ERROR] Error al crear tablas: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("Configurando base de datos de testing")
    print("=" * 60)
    print(f"Host: {TEST_DB_HOST}:{TEST_DB_PORT}")
    print(f"Usuario: {TEST_DB_USER}")
    print(f"Base de datos: {TEST_DB_NAME}")
    print("=" * 60)
    print()
    
    # Paso 1: Intentar crear la base de datos
    db_created = create_test_database()
    
    if not db_created:
        # Verificar si la DB ya existe
        try:
            conn = psycopg2.connect(
                host=TEST_DB_HOST,
                port=TEST_DB_PORT,
                user=TEST_DB_USER,
                password=TEST_DB_PASSWORD,
                database=TEST_DB_NAME
            )
            conn.close()
            print(f"[INFO] La base de datos '{TEST_DB_NAME}' ya existe. Continuando...")
        except psycopg2.OperationalError:
            print()
            print("=" * 60)
            print("ACCION REQUERIDA: Crear la base de datos manualmente")
            print("=" * 60)
            print()
            print("El usuario no tiene permisos para crear bases de datos.")
            print("Ejecuta uno de estos comandos como superusuario:")
            print()
            print(f"  psql -h {TEST_DB_HOST} -U postgres -c 'CREATE DATABASE {TEST_DB_NAME};'")
            print()
            print("O ejecuta el script SQL:")
            print(f"  psql -h {TEST_DB_HOST} -U postgres -f scripts/create_test_db.sql")
            print()
            print("Luego ejecuta este script nuevamente para crear las tablas.")
            print()
            sys.exit(1)
    
    print()
    
    # Paso 2: Crear las tablas
    if not create_tables():
        print("[ERROR] No se pudieron crear las tablas.")
        sys.exit(1)
    
    print()
    
    # Paso 3: Ejecutar migraciones
    if not run_migrations():
        print("[ERROR] No se pudieron ejecutar las migraciones.")
        sys.exit(1)
    
    print()
    print("=" * 60)
    print("[OK] Base de datos de testing configurada exitosamente!")
    print("=" * 60)
    print()
    print("Para usar la DB de testing, configura las variables de entorno:")
    print(f"  export DB_NAME={TEST_DB_NAME}")
    print()
    print("O crea un archivo .env.test con:")
    print(f"  DB_NAME={TEST_DB_NAME}")
    print()

