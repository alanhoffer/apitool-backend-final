"""
Script para obtener el token de push notifications del usuario admin
"""
from app.database import SessionLocal
from app.services.user_service import UserService

def get_admin_token():
    """Obtiene el token de push del usuario admin"""
    db = SessionLocal()
    try:
        user_service = UserService(db)
        user = user_service.get_user_by_email("admin@admin.com")
        
        if not user:
            print("[ERROR] Usuario admin@admin.com no encontrado")
            return
        
        print(f"\n{'='*60}")
        print(f"TOKEN DE PUSH NOTIFICATIONS - ADMIN")
        print(f"{'='*60}\n")
        print(f"Usuario: {user.name} {user.surname}")
        print(f"Email: {user.email}")
        print(f"ID: {user.id}")
        print(f"Rol: {user.role.value}")
        print(f"\nToken de Push Notifications:")
        print(f"{'-'*60}")
        
        if user.expoPushToken:
            print(f"Token completo: {user.expoPushToken}")
            print(f"\nFormato del token:")
            print(f"  - Tipo: Expo Push Token")
            print(f"  - Longitud: {len(user.expoPushToken)} caracteres")
            print(f"  - Prefijo: ExponentPushToken[...]")
            print(f"\nEste token se usa para enviar notificaciones push")
            print(f"a dispositivos móviles a través del servicio de Expo.")
        else:
            print("(sin token registrado)")
            print("\nPara registrar un token, la app móvil debe enviarlo usando:")
            print("POST /users/push-token")
            print("Body: { 'token': 'ExponentPushToken[...]' }")
        
        print(f"{'-'*60}\n")
        
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    get_admin_token()





























