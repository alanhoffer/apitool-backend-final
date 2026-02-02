#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para crear una notificación de prueba para un usuario.
"""
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.services.notification_service import NotificationService
from app.services.user_service import UserService
from app.schemas.notification import NotificationCreate

def create_notification_for_user(email: str, title: str = None, message: str = None):
    """Crea una notificación para un usuario por email."""
    db = SessionLocal()
    try:
        # Buscar usuario por email
        user_service = UserService(db)
        user = user_service.get_user_by_email(email)
        
        if not user:
            print(f"[ERROR] Usuario con email '{email}' no encontrado")
            return False
        
        print(f"[INFO] Usuario encontrado: {user.name} {user.surname} (ID: {user.id})")
        
        # Crear notificación
        notification_service = NotificationService(db)
        
        notification_data = NotificationCreate(
            userId=user.id,
            title=title or "Notificación de Prueba",
            message=message or "Esta es una notificación de prueba para verificar que el sistema funciona correctamente.",
            type="INFO"
        )
        
        notification = notification_service.create_notification(
            notification_data,
            push_data={"test": True, "notificationId": None}  # Se actualizará después
        )
        
        # Actualizar push_data con el ID real
        if notification:
            print(f"[OK] Notificación creada exitosamente")
            print(f"     ID: {notification.id}")
            print(f"     Título: {notification.title}")
            print(f"     Mensaje: {notification.message}")
            print(f"     Tipo: {notification.type}")
            print(f"     Leída: {notification.isRead}")
            print(f"     Fecha: {notification.createdAt}")
            
            # Intentar enviar push notification
            print(f"\n[INFO] Intentando enviar push notification...")
            notification_service.send_push_notification(
                user.id,
                notification.title,
                notification.message,
                data={"notificationId": notification.id, "test": True}
            )
            
            return True
        else:
            print(f"[ERROR] No se pudo crear la notificación")
            return False
            
    except Exception as e:
        print(f"[ERROR] Error al crear notificación: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Crear notificación de prueba para un usuario')
    parser.add_argument('email', nargs='?', default='admin@admin.com', help='Email del usuario (default: admin@admin.com)')
    parser.add_argument('--title', help='Título de la notificación')
    parser.add_argument('--message', help='Mensaje de la notificación')
    parser.add_argument('--type', default='INFO', choices=['INFO', 'ALERT', 'WARNING'], help='Tipo de notificación')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("CREAR NOTIFICACIÓN DE PRUEBA")
    print("=" * 60)
    print(f"Email: {args.email}")
    print()
    
    # Si se especifica tipo, actualizar el schema
    if args.type != 'INFO':
        from app.schemas.notification import NotificationCreate
        # Crear notificación con el tipo especificado
        db = SessionLocal()
        try:
            user_service = UserService(db)
            user = user_service.get_user_by_email(args.email)
            
            if not user:
                print(f"[ERROR] Usuario con email '{args.email}' no encontrado")
                sys.exit(1)
            
            notification_service = NotificationService(db)
            notification_data = NotificationCreate(
                userId=user.id,
                title=args.title or f"Notificación de Prueba ({args.type})",
                message=args.message or f"Esta es una notificación de prueba tipo {args.type}.",
                type=args.type
            )
            
            notification = notification_service.create_notification(notification_data)
            print(f"[OK] Notificación creada: ID {notification.id}")
            
            if args.type == "ALERT":
                print("[INFO] Enviando push notification (tipo ALERT)...")
                notification_service.send_push_notification(
                    user.id,
                    notification.title,
                    notification.message
                )
        finally:
            db.close()
    else:
        create_notification_for_user(args.email, args.title, args.message)
    
    print()
    print("=" * 60)
    print("COMPLETADO")
    print("=" * 60)

