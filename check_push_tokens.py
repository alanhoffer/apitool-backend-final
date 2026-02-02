"""
Script para verificar qué usuarios tienen tokens de push notifications registrados
"""
from app.database import SessionLocal
from app.services.user_service import UserService

def check_push_tokens():
    """Muestra información sobre los tokens de push de los usuarios"""
    db = SessionLocal()
    try:
        user_service = UserService(db)
        
        # Obtener todos los usuarios (necesitamos hacer la query directamente)
        from app.models.user import User
        users = db.query(User).all()
        
        print(f"\n{'='*60}")
        print(f"TOKENS DE PUSH NOTIFICATIONS")
        print(f"{'='*60}\n")
        
        users_with_token = 0
        users_without_token = 0
        
        for user in users:
            has_token = user.expoPushToken is not None and user.expoPushToken != ""
            token_preview = ""
            
            if has_token:
                users_with_token += 1
                # Mostrar solo los primeros y últimos caracteres del token por seguridad
                token = user.expoPushToken
                if len(token) > 20:
                    token_preview = f"{token[:10]}...{token[-10:]}"
                else:
                    token_preview = token
            else:
                users_without_token += 1
                token_preview = "(sin token)"
            
            status = "[OK]" if has_token else "[NO TOKEN]"
            print(f"{status} {user.name} {user.surname} ({user.email})")
            print(f"      Token: {token_preview}")
            print(f"      ID: {user.id}, Rol: {user.role.value}")
            print()
        
        print(f"{'='*60}")
        print(f"Resumen:")
        print(f"  - Usuarios con token: {users_with_token}")
        print(f"  - Usuarios sin token: {users_without_token}")
        print(f"  - Total usuarios: {len(users)}")
        print(f"{'='*60}\n")
        
        # Explicación
        print("INFORMACION SOBRE PUSH NOTIFICATIONS:")
        print("-" * 60)
        print("1. El token se obtiene desde la app móvil (React Native/Expo)")
        print("2. La app debe enviar el token al backend usando: POST /users/push-token")
        print("3. Las notificaciones push solo se envían cuando:")
        print("   - El tipo de notificación es 'ALERT'")
        print("   - El usuario tiene un token registrado (expoPushToken)")
        print("4. Las notificaciones se envían a través de Expo Push Notification Service")
        print("5. Solo funcionan en dispositivos móviles (iOS/Android)")
        print("6. Para web, las notificaciones se muestran en la app, no como push")
        print("-" * 60)
        
    except Exception as e:
        print(f"[ERROR] Error al verificar tokens: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_push_tokens()





























