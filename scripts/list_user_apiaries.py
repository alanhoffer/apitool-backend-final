#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para listar todos los apiarios de un usuario.
"""
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.apiary import Apiary
from app.models.user import User

def list_user_apiaries(user_email: str):
    """Lista todos los apiarios de un usuario."""
    db = SessionLocal()
    try:
        # Buscar usuario
        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            print(f"[ERROR] Usuario '{user_email}' no encontrado")
            return
        
        print(f"[INFO] Usuario: {user.name} {user.surname} (ID: {user.id})")
        
        # Buscar apiarios
        apiaries = db.query(Apiary).filter(Apiary.userId == user.id).all()
        
        if not apiaries:
            print(f"\n[INFO] El usuario no tiene apiarios")
            return
        
        print(f"\n[INFO] Apiarios encontrados ({len(apiaries)}):")
        print("-" * 80)
        for apiary in apiaries:
            print(f"ID: {apiary.id:3d} | Nombre: {apiary.name:30s} | Imagen: {apiary.image}")
        print("-" * 80)
            
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Listar apiarios de un usuario')
    parser.add_argument('--email', default='admin@admin.com', help='Email del usuario (default: admin@admin.com)')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("LISTAR APIARIOS DE USUARIO")
    print("=" * 80)
    print(f"Usuario: {args.email}")
    print()
    
    list_user_apiaries(args.email)
    
    print()
    print("=" * 80)

