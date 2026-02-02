#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para verificar qué imagen tiene un apiario específico.
"""
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.apiary import Apiary
from app.models.user import User
from pathlib import Path

def check_apiary_image(apiary_name: str, user_email: str):
    """Verifica qué imagen tiene un apiario."""
    db = SessionLocal()
    try:
        # Buscar usuario
        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            print(f"[ERROR] Usuario '{user_email}' no encontrado")
            return
        
        print(f"[INFO] Usuario encontrado: {user.name} {user.surname} (ID: {user.id})")
        
        # Buscar apiario
        apiary = db.query(Apiary).filter(
            Apiary.name == apiary_name,
            Apiary.userId == user.id
        ).first()
        
        if not apiary:
            print(f"[ERROR] Apiario '{apiary_name}' no encontrado para el usuario {user_email}")
            return
        
        print(f"\n[INFO] Apiario encontrado:")
        print(f"     ID: {apiary.id}")
        print(f"     Nombre: {apiary.name}")
        print(f"     Imagen en BD: '{apiary.image}'")
        
        # Verificar si el archivo existe
        UPLOAD_DIR = Path("uploads")
        image_path = UPLOAD_DIR / apiary.image
        
        print(f"\n[INFO] Verificando archivo:")
        print(f"     Ruta completa: {image_path.absolute()}")
        print(f"     Existe: {image_path.exists()}")
        
        if image_path.exists():
            file_size = image_path.stat().st_size
            print(f"     Tamaño: {file_size} bytes ({file_size / 1024:.2f} KB)")
        else:
            print(f"     [ADVERTENCIA] ARCHIVO NO EXISTE")
            print(f"     El apiario tiene '{apiary.image}' en la BD pero el archivo no existe en uploads/")
            
            # Verificar si es la imagen por defecto
            if apiary.image == "apiary-default.png":
                print(f"\n     [INFO] Este es el valor por defecto.")
                print(f"     Si el archivo existe en produccion, esta bien.")
                print(f"     Si no existe, necesitas crear 'uploads/apiary-default.png'")
        
        # Listar archivos en uploads
        print(f"\n[INFO] Archivos en uploads/:")
        if UPLOAD_DIR.exists():
            files = list(UPLOAD_DIR.glob("*"))
            if files:
                for f in files:
                    print(f"     - {f.name} ({f.stat().st_size} bytes)")
            else:
                print(f"     (directorio vacío)")
        else:
            print(f"     (directorio no existe)")
            
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Verificar imagen de un apiario')
    parser.add_argument('apiary_name', help='Nombre del apiario')
    parser.add_argument('--email', default='admin@admin.com', help='Email del usuario (default: admin@admin.com)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("VERIFICAR IMAGEN DE APIARIO")
    print("=" * 60)
    print(f"Apiario: {args.apiary_name}")
    print(f"Usuario: {args.email}")
    print()
    
    check_apiary_image(args.apiary_name, args.email)
    
    print()
    print("=" * 60)

