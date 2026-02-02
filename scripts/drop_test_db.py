#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para eliminar la base de datos de testing.
"""
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from app.config import settings

TEST_DB_NAME = "apitool1_test"
TEST_DB_HOST = settings.db_host
TEST_DB_PORT = settings.db_port
TEST_DB_USER = settings.db_user
TEST_DB_PASSWORD = settings.db_password

def drop_test_database():
    """Elimina la base de datos de testing."""
    try:
        # Conectar a PostgreSQL
        conn = psycopg2.connect(
            host=TEST_DB_HOST,
            port=TEST_DB_PORT,
            user=TEST_DB_USER,
            password=TEST_DB_PASSWORD,
            database="postgres"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Verificar si la base de datos existe
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (TEST_DB_NAME,)
        )
        exists = cursor.fetchone()
        
        if not exists:
            print(f"[INFO] La base de datos '{TEST_DB_NAME}' no existe.")
            cursor.close()
            conn.close()
            return True
        
        # Confirmar eliminación
        print(f"[WARN] Se eliminará la base de datos '{TEST_DB_NAME}'.")
        response = input("¿Estás seguro? (s/N): ")
        if response.lower() != 's':
            print("[INFO] Operación cancelada.")
            cursor.close()
            conn.close()
            return True
        
        # Terminar conexiones activas
        print("[INFO] Terminando conexiones activas...")
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
        print(f"[OK] Base de datos '{TEST_DB_NAME}' eliminada exitosamente.")
        
        cursor.close()
        conn.close()
        return True
        
    except psycopg2.Error as e:
        print(f"[ERROR] Error al eliminar la base de datos: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Error inesperado: {e}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("Eliminando base de datos de testing")
    print("=" * 60)
    print()
    
    if drop_test_database():
        print("[OK] Operación completada.")
        sys.exit(0)
    else:
        print("[ERROR] No se pudo eliminar la base de datos.")
        sys.exit(1)

