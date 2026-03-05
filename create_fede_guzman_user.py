from app.database import engine
from sqlalchemy import text, create_engine
from passlib.context import CryptContext
from app.config import settings

# Configuración de hashing para que coincida con la aplicación
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_fede_user():
    # Intentar con la configuración por defecto
    engines_to_try = [engine]
    
    # Si falla, intentar con localhost
    localhost_url = f"postgresql://{settings.db_user}:{settings.db_password}@localhost:{settings.db_port}/{settings.db_name}"
    engines_to_try.append(create_engine(localhost_url))

    for current_engine in engines_to_try:
        try:
            email = "fedeguzman_vet@hotmail.com"
            password = "15533786"
            name = "Fede"
            surname = "Guzman"
            role = "apicultor" # Usuario normal
            
            # Hashear password
            hashed_password = pwd_context.hash(password)
            
            print(f"Intentando conexión con: {current_engine.url}")
            
            # Conexión directa
            with current_engine.connect() as conn:
                # Verificar si existe
                result = conn.execute(text("SELECT id FROM \"user\" WHERE email = :email"), {"email": email})
                if result.fetchone():
                    print(f"El usuario {email} ya existe.")
                    return

                query = text("""
                    INSERT INTO "user" (name, surname, email, password, role)
                    VALUES (:name, :surname, :email, :password, :role)
                """)
                
                conn.execute(query, {
                    "name": name, 
                    "surname": surname, 
                    "email": email, 
                    "password": hashed_password,
                    "role": role
                })
                conn.commit()
                
            print(f"Usuario creado exitosamente: {email}")
            print(f"Nombre: {name} {surname}")
            print(f"Rol: {role}")
            return # Éxito
            
        except Exception as e:
            print(f"Error con {current_engine.url}: {e}")

if __name__ == "__main__":
    create_fede_user()
