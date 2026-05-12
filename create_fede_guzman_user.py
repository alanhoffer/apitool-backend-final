import argparse
import os
import sys

from passlib.context import CryptContext
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

from app.config import settings
from app.database import engine

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def build_parser():
    parser = argparse.ArgumentParser(
        description="Crea un usuario apicultor usando argumentos o variables de entorno.",
        epilog=(
            "Variables soportadas: FEDE_USER_EMAIL, FEDE_USER_PASSWORD, "
            "FEDE_USER_NAME, FEDE_USER_SURNAME, FEDE_USER_ROLE"
        ),
    )
    parser.add_argument("--email", help="Email del usuario.")
    parser.add_argument("--password", help="Password del usuario.")
    parser.add_argument("--name", help="Nombre del usuario.")
    parser.add_argument("--surname", help="Apellido del usuario.")
    parser.add_argument(
        "--role",
        help="Rol del usuario. Si no se informa, usa 'apicultor'.",
    )
    parser.add_argument(
        "--no-localhost-fallback",
        action="store_true",
        help="Evita el intento adicional usando localhost.",
    )
    return parser


def get_value(cli_value, env_name, default=None):
    return cli_value or os.getenv(env_name) or default


def redact_message(message, secrets):
    redacted = str(message)
    for secret in secrets:
        if secret:
            redacted = redacted.replace(secret, "***")
    return redacted


def build_engines(skip_localhost_fallback):
    engines_to_try = [("conexion configurada", engine)]

    if skip_localhost_fallback:
        return engines_to_try

    localhost_url = URL.create(
        "postgresql",
        username=settings.db_user,
        password=settings.db_password,
        host="localhost",
        port=settings.db_port,
        database=settings.db_name,
    )
    engines_to_try.append(("fallback localhost", create_engine(localhost_url)))
    return engines_to_try


def create_user(email, password, name, surname, role, skip_localhost_fallback):
    hashed_password = pwd_context.hash(password)
    secrets = [settings.db_password, password]

    for label, current_engine in build_engines(skip_localhost_fallback):
        try:
            print(f"Intentando crear usuario usando {label}...")
            with current_engine.connect() as conn:
                existing_user = conn.execute(
                    text('SELECT id FROM "user" WHERE email = :email'),
                    {"email": email},
                ).fetchone()
                if existing_user:
                    print(f"El usuario {email} ya existe.")
                    return True

                insert_user = text(
                    """
                    INSERT INTO "user" (name, surname, email, password, role)
                    VALUES (:name, :surname, :email, :password, :role)
                    """
                )
                conn.execute(
                    insert_user,
                    {
                        "name": name,
                        "surname": surname,
                        "email": email,
                        "password": hashed_password,
                        "role": role,
                    },
                )
                conn.commit()

            print(f"Usuario creado exitosamente: {email}")
            print(f"Nombre: {name} {surname}")
            print(f"Rol: {role}")
            return True
        except Exception as exc:
            print(
                "Error usando {label}: {error}".format(
                    label=label,
                    error=redact_message(exc, secrets),
                )
            )

    return False


def main():
    parser = build_parser()
    args = parser.parse_args()

    email = get_value(args.email, "FEDE_USER_EMAIL")
    password = get_value(args.password, "FEDE_USER_PASSWORD")
    name = get_value(args.name, "FEDE_USER_NAME")
    surname = get_value(args.surname, "FEDE_USER_SURNAME")
    role = get_value(args.role, "FEDE_USER_ROLE", "apicultor")

    missing = []
    if not email:
        missing.append("--email o FEDE_USER_EMAIL")
    if not password:
        missing.append("--password o FEDE_USER_PASSWORD")
    if not name:
        missing.append("--name o FEDE_USER_NAME")
    if not surname:
        missing.append("--surname o FEDE_USER_SURNAME")

    if missing:
        parser.error("Faltan datos requeridos: " + ", ".join(missing))

    success = create_user(
        email=email,
        password=password,
        name=name,
        surname=surname,
        role=role,
        skip_localhost_fallback=args.no_localhost_fallback,
    )
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
