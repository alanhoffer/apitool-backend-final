import argparse
import os
import sys

from passlib.context import CryptContext
from sqlalchemy import text

from app.database import engine

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def build_parser():
    parser = argparse.ArgumentParser(
        description="Crea un usuario admin usando argumentos o variables de entorno.",
        epilog=(
            "Variables soportadas: ADMIN_USER_EMAIL, ADMIN_USER_PASSWORD, "
            "ADMIN_USER_FULL_NAME"
        ),
    )
    parser.add_argument("--email", help="Email del usuario admin.")
    parser.add_argument("--password", help="Password del usuario admin.")
    parser.add_argument("--full-name", help="Nombre completo del usuario admin.")
    return parser


def get_required_value(cli_value, env_name):
    return cli_value or os.getenv(env_name)


def split_full_name(full_name):
    parts = full_name.strip().split(" ", 1)
    name = parts[0]
    surname = parts[1] if len(parts) > 1 else ""
    return name, surname


def create_user(email, password, full_name):
    name, surname = split_full_name(full_name)

    try:
        with engine.connect() as conn:
            existing_user = conn.execute(
                text('SELECT id FROM "user" WHERE email = :email'),
                {"email": email},
            ).fetchone()
            if existing_user:
                print(f"El usuario {email} ya existe.")
                return True

            hashed_password = pwd_context.hash(password)
            insert_user = text(
                """
                INSERT INTO "user" (name, surname, email, password, role)
                VALUES (:name, :surname, :email, :password, 'admin')
                """
            )
            conn.execute(
                insert_user,
                {
                    "name": name,
                    "surname": surname,
                    "email": email,
                    "password": hashed_password,
                },
            )
            conn.commit()
    except Exception as exc:
        print(f"Error al crear usuario admin para {email}: {exc}")
        return False

    print(f"Usuario admin creado exitosamente para {email}.")
    return True


def main():
    parser = build_parser()
    args = parser.parse_args()

    email = get_required_value(args.email, "ADMIN_USER_EMAIL")
    password = get_required_value(args.password, "ADMIN_USER_PASSWORD")
    full_name = get_required_value(args.full_name, "ADMIN_USER_FULL_NAME")

    missing = []
    if not email:
        missing.append("--email o ADMIN_USER_EMAIL")
    if not password:
        missing.append("--password o ADMIN_USER_PASSWORD")
    if not full_name:
        missing.append("--full-name o ADMIN_USER_FULL_NAME")

    if missing:
        parser.error("Faltan datos requeridos: " + ", ".join(missing))

    return 0 if create_user(email=email, password=password, full_name=full_name) else 1


if __name__ == "__main__":
    sys.exit(main())
