from app.database import engine
from sqlalchemy import text

def import_apiaries():
    try:
        # 1. Conexión directa
        with engine.connect() as conn:
            # Obtener ID del usuario
            result = conn.execute(text("SELECT id FROM \"user\" WHERE email = 'cristian@hoffer.com'"))
            user_row = result.fetchone()
            
            if not user_row:
                print("Error: El usuario cristian@hoffer.com no existe.")
                return

            user_id = user_row[0]
            print(f"Importando apiarios para User ID: {user_id}")

            # 2. Lista de datos
            raw_data = [
                ("Los ciervos", 42),
                ("La limpia", 45),
                ("La mascota Barranca", 39),
                ("Lo chian fondo", 14),
                ("Tres hermanos", 3),
                ("Claverie casco", 39),
                ("Lo nechini bebida", 40),
                ("La celina carmen", 32),
                ("Ramiro nehuen", 3),
                ("melon", 24),
                ("Piedra medio", 35)
            ]

            count = 0
            for name, hives in raw_data:
                # Verificar existencia
                check = conn.execute(text("SELECT id FROM apiary WHERE \"userId\" = :uid AND name = :name"), 
                                   {"uid": user_id, "name": name})
                if check.fetchone():
                    print(f"Saltando {name} (ya existe)")
                    continue

                # Insertar Apiario
                # Nota: Insertamos solo los campos necesarios, el resto asumimos default de la DB o null
                ins_apiary = text("""
                    INSERT INTO apiary (name, "userId", hives, status, image, honey, levudex, sugar, "createdAt", "updatedAt")
                    VALUES (:name, :uid, :hives, 'normal', 'apiary-default.png', 0, 0, 0, NOW(), NOW())
                    RETURNING id
                """)
                res = conn.execute(ins_apiary, {"name": name, "uid": user_id, "hives": hives})
                apiary_id = res.fetchone()[0]

                # Insertar Settings
                ins_settings = text("""
                    INSERT INTO apiary_setting ("apiaryId", "apiaryUserId", honey, levudex, sugar, box, "boxMedium", "boxSmall", "tOxalic", "tAmitraz", "tFlumetrine", "tFence", "tComment", transhumance, harvesting)
                    VALUES (:aid, :uid, true, true, true, true, true, true, true, true, true, true, true, true, false)
                """)
                conn.execute(ins_settings, {"aid": apiary_id, "uid": user_id})
                
                conn.commit()
                count += 1
                print(f"Creado: {name}")

            print(f"\nProceso finalizado. {count} apiarios importados.")

    except Exception as e:
        print(f"Error durante la importación: {e}")

if __name__ == "__main__":
    import_apiaries()
