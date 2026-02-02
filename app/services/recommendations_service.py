from sqlalchemy.orm import Session
from app.models.recommendations import SeasonalTip
from app.schemas.recommendations import SeasonalTipCreate
from app.utils.cache import cached
from typing import List
from datetime import datetime

class RecommendationsService:
    def __init__(self, db: Session):
        self.db = db

    def get_current_season(self, month: int, hemisphere: str = "South") -> str:
        if hemisphere == "South":
            if month in [9, 10, 11]: return "Primavera"
            if month in [12, 1, 2]: return "Verano"
            if month in [3, 4, 5]: return "Otoño"
            return "Invierno"
        else: # North
            if month in [3, 4, 5]: return "Primavera"
            if month in [6, 7, 8]: return "Verano"
            if month in [9, 10, 11]: return "Otoño"
            return "Invierno"

    @cached(ttl=3600, key_prefix="recommendations")  # Cache por 1 hora
    def get_recommendations(self, hemisphere: str = "South") -> dict:
        current_month = datetime.now().month
        season_name = self.get_current_season(current_month, hemisphere)
        
        # Mapeo de nombre legible a clave de base de datos si fuera necesario
        # En DB usaremos: spring, summer, autumn, winter
        season_key_map = {
            "Primavera": "spring",
            "Verano": "summer",
            "Otoño": "autumn",
            "Invierno": "winter"
        }
        season_key = season_key_map.get(season_name)

        # Buscar tips que:
        # 1. Estén activos
        # 2. Sean para el hemisferio correcto
        # 3. Coincidan con la estación O incluyan el mes actual en 'months'
        
        query = self.db.query(SeasonalTip).filter(
            SeasonalTip.isActive == True,
            SeasonalTip.hemisphere == hemisphere
        )
        
        # Filtro en memoria para lógica compleja de "months" vs "season"
        # O hacerlo en query: (season == X) OR (months LIKE '%M%')
        # Haremos una query más amplia y filtraremos en python para precisión
        all_tips = query.all()
        
        filtered_tips = []
        for tip in all_tips:
            is_match = False
            # Coincidencia por mes específico
            if tip.months:
                if str(current_month) in tip.months.split(','):
                    is_match = True
            # Coincidencia por estación (si no hay restricción de mes)
            elif tip.season == season_key:
                is_match = True
                
            if is_match:
                filtered_tips.append(tip)

        return {
            "current_season": season_name,
            "current_month": current_month,
            "tips": filtered_tips
        }

    def create_tip(self, tip: SeasonalTipCreate) -> SeasonalTip:
        db_tip = SeasonalTip(**tip.dict())
        self.db.add(db_tip)
        self.db.commit()
        self.db.refresh(db_tip)
        return db_tip

