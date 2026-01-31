"""
Script para verificar las estadísticas de un usuario
"""
from app.database import SessionLocal
from app.services.user_service import UserService
from app.services.drum_service import DrumService
from app.services.apiary_service import ApiaryService

def check_user_stats(email: str):
    """Verifica las estadísticas de un usuario por email"""
    db = SessionLocal()
    try:
        # Buscar usuario
        user_service = UserService(db)
        user = user_service.get_user_by_email(email)
        
        if not user:
            print(f"[ERROR] Usuario con email '{email}' no encontrado")
            return
        
        print(f"\n{'='*70}")
        print(f"ESTADISTICAS DE USUARIO")
        print(f"{'='*70}")
        print(f"Nombre: {user.name} {user.surname}")
        print(f"Email: {user.email}")
        print(f"ID Usuario: {user.id}")
        print(f"Rol: {user.role}")
        print(f"{'='*70}\n")
        
        # Obtener estadísticas de tambores
        drum_service = DrumService(db)
        drum_stats = drum_service.get_stats(user.id)
        
        print(f"{'='*70}")
        print(f"ESTADISTICAS DE TAMBORES")
        print(f"{'='*70}")
        print(f"  Total de tambores: {drum_stats['total']}")
        print(f"  Vendidos: {drum_stats['sold']}")
        print(f"  No vendidos: {drum_stats['not_sold']}")
        print(f"  Tara total: {drum_stats['total_tare']} kg")
        print(f"  Peso total: {drum_stats['total_weight']} kg")
        print(f"  Peso neto: {drum_stats['net_weight']} kg")
        print(f"{'='*70}\n")
        
        # Obtener estadísticas de apiarios
        apiary_service = ApiaryService(db)
        apiary_count = apiary_service.count_apiaries_by_user_id(user.id)
        hive_count = apiary_service.count_hives_by_user_id(user.id)
        
        # Obtener todos los apiarios para calcular alzas cosechadas
        from app.models.apiary import Apiary
        from sqlalchemy import func
        apiaries = db.query(Apiary).filter(Apiary.userId == user.id).all()
        
        # Calcular alzas cosechadas
        total_box = sum(int(apiary.box or 0) for apiary in apiaries)
        total_boxMedium = sum(int(apiary.boxMedium or 0) for apiary in apiaries)
        total_boxSmall = sum(int(apiary.boxSmall or 0) for apiary in apiaries)
        total_alzas = total_box + total_boxMedium + total_boxSmall
        
        # Contar apiarios en modo harvesting
        from app.models.settings import Settings
        harvesting_count = db.query(Settings).join(Apiary).filter(
            Apiary.userId == user.id,
            Settings.harvesting == True
        ).count()
        
        print(f"{'='*70}")
        print(f"ESTADISTICAS DE APIARIOS")
        print(f"{'='*70}")
        print(f"  Total de apiarios: {apiary_count}")
        print(f"  Total de colmenas: {hive_count}")
        print(f"  Apiarios en cosecha (harvesting): {harvesting_count}")
        print(f"{'='*70}\n")
        
        print(f"{'='*70}")
        print(f"ALZAS COSECHADAS")
        print(f"{'='*70}")
        print(f"  Alzas grandes (box): {total_box}")
        print(f"  Alzas medianas (boxMedium): {total_boxMedium}")
        print(f"  Alzas pequeñas (boxSmall): {total_boxSmall}")
        print(f"  TOTAL ALZAS COSECHADAS: {total_alzas}")
        print(f"{'='*70}\n")
        
        # Resumen
        print(f"{'='*70}")
        print(f"RESUMEN")
        print(f"{'='*70}")
        has_drums = drum_stats['total'] > 0
        has_apiaries = apiary_count > 0
        has_alzas = total_alzas > 0
        
        print(f"  Tiene tambores: {'SI' if has_drums else 'NO'}")
        print(f"  Tiene apiarios: {'SI' if has_apiaries else 'NO'}")
        print(f"  Tiene alzas cosechadas: {'SI' if has_alzas else 'NO'} ({total_alzas} alzas)")
        print(f"  Tiene estadisticas: {'SI' if (has_drums or has_apiaries) else 'NO'}")
        print(f"{'='*70}\n")
        
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_user_stats("cristian@hoffer.com")

