"""
Script para listar los tambores de un usuario
"""
from app.database import SessionLocal
from app.services.user_service import UserService
from app.services.drum_service import DrumService

def list_user_drums(email: str):
    """Lista los tambores de un usuario por email"""
    db = SessionLocal()
    try:
        # Buscar usuario
        user_service = UserService(db)
        user = user_service.get_user_by_email(email)
        
        if not user:
            print(f"[ERROR] Usuario con email '{email}' no encontrado")
            return
        
        print(f"\n{'='*60}")
        print(f"TAMBORES DE {user.name.upper()} {user.surname.upper()}")
        print(f"Email: {user.email} (ID: {user.id})")
        print(f"{'='*60}\n")
        
        # Obtener tambores
        drum_service = DrumService(db)
        drums, total = drum_service.get_drums(user.id)
        
        if total == 0:
            print("No hay tambores registrados para este usuario.")
            return
        
        print(f"Total de tambores: {total}\n")
        
        for drum in drums:
            net_weight = float(drum.weight) - float(drum.tare)
            sold_status = "VENDIDO" if drum.sold else "NO VENDIDO"
            
            print(f"ID: {drum.id}")
            print(f"  Codigo: {drum.code}")
            print(f"  Tara: {drum.tare} kg")
            print(f"  Peso Total: {drum.weight} kg")
            print(f"  Peso Neto: {net_weight:.2f} kg")
            print(f"  Estado: {sold_status}")
            print(f"  Creado: {drum.createdAt}")
            print()
        
        # Obtener estadísticas
        stats = drum_service.get_stats(user.id)
        print(f"{'='*60}")
        print(f"ESTADISTICAS:")
        print(f"  Total: {stats['total']}")
        print(f"  Vendidos: {stats['sold']}")
        print(f"  No Vendidos: {stats['not_sold']}")
        print(f"  Tara Total: {stats['total_tare']} kg")
        print(f"  Peso Total: {stats['total_weight']} kg")
        print(f"  Peso Neto: {stats['net_weight']} kg")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    list_user_drums("admin@admin.com")





























