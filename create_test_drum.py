"""
Script para crear un tambor de prueba para el usuario admin@admin.com
"""
from app.database import SessionLocal
from app.services.user_service import UserService
from app.services.drum_service import DrumService
from app.schemas.drum import DrumCreate
from decimal import Decimal

def create_test_drum():
    """Crea un tambor de prueba para admin@admin.com"""
    db = SessionLocal()
    try:
        # Buscar usuario admin
        user_service = UserService(db)
        user = user_service.get_user_by_email("admin@admin.com")
        
        if not user:
            print("[ERROR] Usuario admin@admin.com no encontrado")
            return False
        
        print(f"[OK] Usuario encontrado: {user.name} {user.surname} (ID: {user.id})")
        
        # Crear tambor de prueba
        drum_service = DrumService(db)
        
        drum_data = DrumCreate(
            code="TAMBOR-TEST-001",
            tare=Decimal("15.5"),
            weight=Decimal("45.2")
        )
        
        drum = drum_service.create_drum(user.id, drum_data)
        
        print(f"\n[OK] Tambor de prueba creado exitosamente!")
        print(f"   ID: {drum.id}")
        print(f"   Codigo: {drum.code}")
        print(f"   Tara: {drum.tare} kg")
        print(f"   Peso Total: {drum.weight} kg")
        print(f"   Peso Neto: {float(drum.weight) - float(drum.tare)} kg")
        print(f"   Vendido: {drum.sold}")
        print(f"   Creado: {drum.createdAt}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Error al crear tambor: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("="*60)
    print("CREAR TAMBOR DE PRUEBA")
    print("="*60)
    print("\nCreando tambor de prueba para admin@admin.com...\n")
    
    create_test_drum()





























