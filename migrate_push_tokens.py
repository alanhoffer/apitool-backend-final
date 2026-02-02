"""
Script de migración para mover tokens de push existentes de user.expoPushToken
a la nueva tabla devices.

Este script:
1. Busca todos los usuarios con expoPushToken
2. Crea un registro en la tabla devices para cada token
3. Mantiene el token en user.expoPushToken para compatibilidad (opcional)
"""
from app.database import SessionLocal, engine, Base
from app.models.user import User
from app.models.device import Device
from datetime import datetime

def migrate_push_tokens():
    """Migra los tokens existentes a la nueva tabla devices."""
    db = SessionLocal()
    
    try:
        # Asegurar que la tabla devices existe
        print("Creando tabla devices si no existe...")
        Base.metadata.create_all(bind=engine, tables=[Device.__table__])
        print("Tabla devices lista.\n")
        
        # Buscar usuarios con tokens
        users_with_tokens = db.query(User).filter(
            User.expoPushToken.isnot(None),
            User.expoPushToken != ""
        ).all()
        
        print(f"Encontrados {len(users_with_tokens)} usuarios con tokens de push.\n")
        
        migrated_count = 0
        skipped_count = 0
        
        for user in users_with_tokens:
            token = user.expoPushToken
            
            # Verificar si el token ya existe en devices
            existing_device = db.query(Device).filter(
                Device.expoPushToken == token
            ).first()
            
            if existing_device:
                print(f"[SKIP] Token ya existe para usuario {user.email} (device_id: {existing_device.id})")
                skipped_count += 1
                continue
            
            # Crear nuevo dispositivo
            new_device = Device(
                userId=user.id,
                expoPushToken=token,
                deviceName=f"Migrated Device ({user.email})",
                platform=None,  # No sabemos la plataforma del token legacy
                createdAt=user.createdAt or datetime.now(),
                lastActive=datetime.now()
            )
            
            db.add(new_device)
            migrated_count += 1
            print(f"[OK] Token migrado para usuario {user.email} (user_id: {user.id})")
        
        # Commit de todos los cambios
        db.commit()
        
        print(f"\n{'='*60}")
        print(f"Migración completada:")
        print(f"  - Tokens migrados: {migrated_count}")
        print(f"  - Tokens ya existentes (skipped): {skipped_count}")
        print(f"  - Total procesados: {len(users_with_tokens)}")
        print(f"{'='*60}\n")
        
        # Mostrar resumen de dispositivos
        total_devices = db.query(Device).count()
        print(f"Total de dispositivos en la tabla: {total_devices}")
        
        # Opcional: Mostrar dispositivos por usuario
        print("\nDispositivos por usuario:")
        users_with_devices = db.query(User).join(Device).distinct().all()
        for user in users_with_devices:
            devices = db.query(Device).filter(Device.userId == user.id).all()
            print(f"  {user.email}: {len(devices)} dispositivo(s)")
            for device in devices:
                print(f"    - Device {device.id}: {device.deviceName or 'Sin nombre'}")
        
    except Exception as e:
        print(f"[ERROR] Error durante la migración: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("="*60)
    print("MIGRACIÓN DE TOKENS DE PUSH NOTIFICATIONS")
    print("="*60)
    print("\nEste script migrará los tokens existentes de user.expoPushToken")
    print("a la nueva tabla devices para soportar múltiples dispositivos.\n")
    
    migrate_push_tokens()





























