from app.database import engine
from sqlalchemy import text
from passlib.context import CryptContext

# Configuración de hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_user():
    try:
        email = "cristian@hoffer.com"
        password = "15634435"
        full_name = "cristian hoffer"
        
        # Separar nombre y apellido
        parts = full_name.split(" ", 1)
        name = parts[0]
        surname = parts[1] if len(parts) > 1 else ""
        
        # Hashear password
        hashed_password = pwd_context.hash(password)
        
        # Conexión directa
        with engine.connect() as conn:
            # Verificar si existe
            result = conn.execute(text("SELECT id FROM \"user\" WHERE email = :email"), {"email": email})
            if result.fetchone():
                print(f"El usuario {email} ya existe.")
                return

            # Insertar con SQL crudo, forzando el rol como string 'admin'
            # Nota: Usamos 'admin' en minúscula porque es lo que probablemente espera el enum de postgres
            query = text("""
                INSERT INTO "user" (name, surname, email, password, role)
                VALUES (:name, :surname, :email, :password, 'admin')
            """)
            
            conn.execute(query, {
                "name": name, 
                "surname": surname, 
                "email": email, 
                "password": hashed_password
            })
            conn.commit()
            
        print(f"Usuario creado exitosamente: {email}")
        
    except Exception as e:
        print(f"Error al crear usuario: {e}")

if __name__ == "__main__":
    create_user()
