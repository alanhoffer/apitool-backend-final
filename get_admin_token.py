"""
Script para consultar el token de push notifications de un usuario sin
exponer el secreto completo por defecto.
"""

import argparse

from app.database import SessionLocal
from app.services.user_service import UserService


def build_parser():
    parser = argparse.ArgumentParser(
        description="Consulta el token de push de un usuario y lo enmascara por defecto.",
    )
    parser.add_argument(
        "--email",
        default="admin@admin.com",
        help="Email del usuario a consultar. Default: admin@admin.com",
    )
    parser.add_argument(
        "--show-full-token",
        action="store_true",
        help="Muestra el token completo. Usar solo si realmente hace falta.",
    )
    return parser


def mask_secret(secret, visible_prefix=10, visible_suffix=6):
    if not secret:
        return "(sin token registrado)"
    if len(secret) <= visible_prefix + visible_suffix:
        return "*" * len(secret)
    return f"{secret[:visible_prefix]}...{secret[-visible_suffix:]}"


def get_admin_token(email, show_full_token=False):
    db = SessionLocal()
    try:
        user_service = UserService(db)
        user = user_service.get_user_by_email(email)

        if not user:
            print(f"[ERROR] Usuario {email} no encontrado.")
            return False

        print(f"\n{'=' * 60}")
        print("TOKEN DE PUSH NOTIFICATIONS")
        print(f"{'=' * 60}\n")
        print(f"Usuario: {user.name} {user.surname}")
        print(f"Email: {user.email}")
        print(f"ID: {user.id}")
        print(f"Rol: {user.role.value}")
        print(f"\nToken enmascarado: {mask_secret(user.expoPushToken)}")

        if user.expoPushToken:
            print(f"Longitud: {len(user.expoPushToken)} caracteres")
            if show_full_token:
                print("\n[ADVERTENCIA] Mostrando token completo por pedido explicito:")
                print(user.expoPushToken)
        else:
            print("\nPara registrar un token, la app movil debe enviarlo usando:")
            print("POST /users/push-token")
            print("Body: { 'token': 'ExponentPushToken[...]' }")

        print(f"\n{'-' * 60}\n")
        return True
    except Exception as exc:
        print(f"[ERROR] Error al consultar token: {exc}")
        return False
    finally:
        db.close()


def main():
    args = build_parser().parse_args()
    return 0 if get_admin_token(args.email, args.show_full_token) else 1


if __name__ == "__main__":
    raise SystemExit(main())
