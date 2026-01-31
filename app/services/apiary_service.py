from sqlalchemy.orm import Session
from app.models.apiary import Apiary
from app.models.settings import Settings
from app.models.history import History
from app.schemas.apiary import CreateApiary, UpdateApiary, ApiaryResponse
from app.schemas.settings import CreateSettings
from app.services.settings_service import SettingsService
from app.services.history_service import HistoryService
from typing import Optional, List
import json
from decimal import Decimal
from fastapi import UploadFile, HTTPException, status
import uuid
from pathlib import Path
import magic
from PIL import Image
import io

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

class ApiaryService:
    def __init__(self, db: Session):
        self.db = db
        self.settings_service = SettingsService(db)
        self.history_service = HistoryService(db)
    
    def get_all_by_user_id(self, user_id: int) -> List[ApiaryResponse]:
        from sqlalchemy.orm import joinedload
        apiaries = self.db.query(Apiary).options(
            joinedload(Apiary.settings)
        ).filter(
            Apiary.userId == user_id
        ).all()
        
        result = []
        for apiary in apiaries:
            from app.schemas.settings import SettingsResponse
            settings_response = None
            if apiary.settings:
                settings_response = SettingsResponse(
                    id=apiary.settings.id,
                    apiaryId=apiary.settings.apiaryId,
                    apiaryUserId=apiary.settings.apiaryUserId,
                    honey=apiary.settings.honey,
                    levudex=apiary.settings.levudex,
                    sugar=apiary.settings.sugar,
                    box=apiary.settings.box,
                    boxMedium=apiary.settings.boxMedium,
                    boxSmall=apiary.settings.boxSmall,
                    tOxalic=apiary.settings.tOxalic,
                    tAmitraz=apiary.settings.tAmitraz,
                    tFlumetrine=apiary.settings.tFlumetrine,
                    tFence=apiary.settings.tFence,
                    tComment=apiary.settings.tComment,
                    transhumance=apiary.settings.transhumance,
                    harvesting=apiary.settings.harvesting
                )
            
            apiary_dto = ApiaryResponse(
                _id=apiary.id,
                _name=apiary.name,
                _hives=apiary.hives,
                _status=apiary.status,
                _image=apiary.image,
                _honey=apiary.honey or Decimal(0),
                _levudex=apiary.levudex or Decimal(0),
                _sugar=apiary.sugar or Decimal(0),
                _box=apiary.box,
                _boxMedium=apiary.boxMedium,
                _boxSmall=apiary.boxSmall,
                _tOxalic=apiary.tOxalic,
                _tAmitraz=apiary.tAmitraz,
                _tFlumetrine=apiary.tFlumetrine,
                _tFence=apiary.tFence,
                _tComment=apiary.tComment,
                _transhumance=apiary.transhumance,
                _settings=settings_response,
                _updatedAt=apiary.updatedAt
            )
            result.append(apiary_dto)
        
        return result
    
    def get_apiary(self, apiary_id: int) -> Optional[Apiary]:
        from sqlalchemy.orm import joinedload
        return self.db.query(Apiary).options(
            joinedload(Apiary.settings)
        ).filter(Apiary.id == apiary_id).first()
    
    async def _process_image(self, file: UploadFile) -> str:
        """
        Valida, redimensiona y guarda una imagen optimizada.
        Retorna el nombre del archivo guardado.
        """
        # 1. Leer contenido
        content = await file.read()
        
        # 2. Validar tipo real (Magic numbers)
        # magic.from_buffer lee los bytes iniciales para detectar el tipo real
        mime = magic.from_buffer(content, mime=True)
        if mime not in ["image/jpeg", "image/png", "image/gif", "image/webp"]:
             raise HTTPException(
                 status_code=status.HTTP_400_BAD_REQUEST, 
                 detail=f"Invalid image file type: {mime}. Allowed: jpeg, png, gif, webp"
             )
        
        try:
            # 3. Procesar con Pillow
            image = Image.open(io.BytesIO(content))
            
            # Convertir a RGB si tiene transparencia (para guardar como JPEG)
            if image.mode in ("RGBA", "P"):
                image = image.convert("RGB")
                
            # 4. Redimensionar si es muy grande (max 1024px lado mayor)
            # thumbnail mantiene el aspect ratio
            max_size = (1024, 1024)
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # 5. Generar nombre y guardar
            # Estandarizamos a .jpg para consistencia
            filename = f"{uuid.uuid4()}.jpg" 
            file_path = UPLOAD_DIR / filename
            
            # Guardar optimizado (quality=85 es un buen balance peso/calidad)
            image.save(file_path, "JPEG", quality=85, optimize=True)
            
            return filename
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error processing image: {str(e)}"
            )

    async def create_apiary(self, user_id: int, apiary_data: CreateApiary, file: Optional[UploadFile] = None) -> Apiary:
        settings_data = json.loads(apiary_data.settings or '{}')
        
        if file:
            apiary_data.image = await self._process_image(file)
        else:
            apiary_data.image = "apiary-default.png"

        new_apiary = Apiary(
            userId=user_id,
            name=apiary_data.name,
            hives=apiary_data.hives,
            status=apiary_data.status,
            image=apiary_data.image,
            honey=apiary_data.honey,
            levudex=apiary_data.levudex,
            sugar=apiary_data.sugar,
            box=apiary_data.box,
            boxMedium=apiary_data.boxMedium,
            boxSmall=apiary_data.boxSmall,
            tOxalic=apiary_data.tOxalic,
            tAmitraz=apiary_data.tAmitraz,
            tFlumetrine=apiary_data.tFlumetrine,
            tFence=apiary_data.tFence,
            tComment=apiary_data.tComment,
            transhumance=apiary_data.transhumance
        )
        
        self.db.add(new_apiary)
        self.db.commit()
        self.db.refresh(new_apiary)
        
        settings = Settings(
            apiaryId=new_apiary.id,
            apiaryUserId=user_id,
            **settings_data
        )
        self.db.add(settings)
        self.db.commit()
        
        return new_apiary
    
    def delete_apiary(self, apiary_id: int) -> bool:
        apiary = self.db.query(Apiary).filter(Apiary.id == apiary_id).first()
        if not apiary:
            return False
        
        self.db.delete(apiary)
        self.db.commit()
        return True
    
    async def update_apiary(self, apiary_id: int, apiary_data: UpdateApiary, file: Optional[UploadFile] = None) -> Optional[Apiary]:
        apiary = self.db.query(Apiary).filter(Apiary.id == apiary_id).first()
        if not apiary:
            return None
        
        if file:
            apiary_data.image = await self._process_image(file)

        # Create a copy of the old values for history
        old_values = {
            'name': apiary.name,
            'hives': apiary.hives,
            'status': apiary.status,
            'image': apiary.image,
            'honey': apiary.honey,
            'levudex': apiary.levudex,
            'sugar': apiary.sugar,
            'box': apiary.box,
            'boxMedium': apiary.boxMedium,
            'boxSmall': apiary.boxSmall,
            'tOxalic': apiary.tOxalic,
            'tAmitraz': apiary.tAmitraz,
            'tFlumetrine': apiary.tFlumetrine,
            'tFence': apiary.tFence,
            'tComment': apiary.tComment,
            'transhumance': apiary.transhumance
        }
        
        update_data = apiary_data.dict(exclude_unset=True, exclude_none=True)
        for key, value in update_data.items():
            setattr(apiary, key, value)
        
        self.db.commit()
        self.db.refresh(apiary)
        
        # Create a temporary old_apiary object for history logging
        from types import SimpleNamespace
        old_apiary = SimpleNamespace(**old_values, id=apiary.id, userId=apiary.userId)
        
        self.history_service.log_changes(old_apiary, apiary)
        
        return apiary
    
    def get_all_history(self, apiary_id: int) -> List[History]:
        return self.db.query(History).filter(History.apiaryId == apiary_id).all()
    
    def count_apiaries_by_user_id(self, user_id: int) -> int:
        return self.db.query(Apiary).filter(Apiary.userId == user_id).count()
    
    def count_hives_by_user_id(self, user_id: int) -> int:
        from sqlalchemy import func
        return self.db.query(func.sum(Apiary.hives)).filter(Apiary.userId == user_id).scalar() or 0
    
    def get_box_stats(self, user_id: int) -> dict:
        """Obtiene estadísticas de alzas cosechadas para un usuario."""
        from sqlalchemy import func
        result = self.db.query(
            func.sum(Apiary.box).label('total_box'),
            func.sum(Apiary.boxMedium).label('total_boxMedium'),
            func.sum(Apiary.boxSmall).label('total_boxSmall')
        ).filter(Apiary.userId == user_id).first()
        
        total_box = int(result.total_box or 0)
        total_boxMedium = int(result.total_boxMedium or 0)
        total_boxSmall = int(result.total_boxSmall or 0)
        total_alzas = total_box + total_boxMedium + total_boxSmall
        
        return {
            "box": total_box,
            "boxMedium": total_boxMedium,
            "boxSmall": total_boxSmall,
            "total": total_alzas
        }
    
    def count_harvesting_apiaries(self, user_id: int) -> int:
        """Cuenta apiarios que están en modo cosecha (harvesting = True)."""
        from app.models.settings import Settings
        return self.db.query(Apiary).join(Settings).filter(
            Apiary.userId == user_id,
            Settings.harvesting == True
        ).count()
    
    def count_harvested_apiaries(self, user_id: int) -> int:
        """Cuenta apiarios que tienen alzas cosechadas (box > 0 OR boxMedium > 0 OR boxSmall > 0)."""
        from sqlalchemy import or_
        return self.db.query(Apiary).filter(
            Apiary.userId == user_id,
            or_(
                Apiary.box > 0,
                Apiary.boxMedium > 0,
                Apiary.boxSmall > 0
            )
        ).count()

    def count_hives_in_harvested_apiaries(self, user_id: int) -> int:
        """Suma colmenas (hives) solo en apiarios con alzas cosechadas."""
        from sqlalchemy import func, or_
        return self.db.query(func.sum(Apiary.hives)).filter(
            Apiary.userId == user_id,
            or_(
                Apiary.box > 0,
                Apiary.boxMedium > 0,
                Apiary.boxSmall > 0
            )
        ).scalar() or 0

    def get_harvested_totals_by_apiary(self, apiary_id: int) -> dict:
        apiary = self.db.query(Apiary).filter(Apiary.id == apiary_id).first()
        if not apiary:
            return {}

        box = int(apiary.box or 0)
        box_medium = int(apiary.boxMedium or 0)
        box_small = int(apiary.boxSmall or 0)

        return {
            "box": box,
            "boxMedium": box_medium,
            "boxSmall": box_small,
            "total": box + box_medium + box_small
        }

    def _parse_history_int(self, value: Optional[str]) -> int:
        try:
            return int(float(value)) if value not in (None, "") else 0
        except (TypeError, ValueError):
            return 0

    def _get_harvested_today_changes(self, user_id: int) -> dict:
        from sqlalchemy import func
        fields = ["box", "boxMedium", "boxSmall"]
        history_rows = self.db.query(History).filter(
            History.userId == user_id,
            History.field.in_(fields),
            func.date(History.changeDate) == func.current_date()
        ).order_by(History.changeDate.desc()).all()

        apiary_ids = set()
        box = 0
        box_medium = 0
        box_small = 0
        seen = set()

        for row in history_rows:
            key = (row.apiaryId, row.field)
            if key in seen:
                continue

            value = self._parse_history_int(row.newValue)
            if row.field == "box":
                box += value
            elif row.field == "boxMedium":
                box_medium += value
            elif row.field == "boxSmall":
                box_small += value

            apiary_ids.add(row.apiaryId)
            seen.add(key)

        return {
            "apiaryIds": apiary_ids,
            "box": box,
            "boxMedium": box_medium,
            "boxSmall": box_small,
            "total": box + box_medium + box_small
        }

    def count_harvested_today_apiaries_and_hives(self, user_id: int) -> dict:
        from sqlalchemy import func
        data = self._get_harvested_today_changes(user_id)
        apiary_ids = data["apiaryIds"]
        apiary_count = len(apiary_ids)

        if not apiary_ids:
            hive_count = 0
        else:
            hive_count = self.db.query(func.sum(Apiary.hives)).filter(
                Apiary.userId == user_id,
                Apiary.id.in_(apiary_ids)
            ).scalar() or 0

        return {
            "apiaryCount": apiary_count,
            "hiveCount": hive_count
        }

    def get_harvested_today_box_stats(self, user_id: int) -> dict:
        data = self._get_harvested_today_changes(user_id)
        return {
            "box": data["box"],
            "boxMedium": data["boxMedium"],
            "boxSmall": data["boxSmall"],
            "total": data["total"]
        }
    
    def subtract_food(self):
        # Preserve updatedAt when subtracting food automatically
        # The stored procedure might update updatedAt, so we save and restore it
        from sqlalchemy import text
        
        # Save current updatedAt values for all apiaries
        self.db.execute(text("DROP TABLE IF EXISTS apiary_updated_at_backup"))
        self.db.commit()
        
        save_query = text("""
            CREATE TEMP TABLE apiary_updated_at_backup AS
            SELECT id, "updatedAt" FROM apiary
        """)
        self.db.execute(save_query)
        self.db.commit()
        
        # Execute the stored procedure
        self.db.execute(text("CALL SubtractFood()"))
        self.db.commit()
        
        # Restore updatedAt values
        restore_query = text("""
            UPDATE apiary 
            SET "updatedAt" = backup."updatedAt"
            FROM apiary_updated_at_backup AS backup
            WHERE apiary.id = backup.id
        """)
        self.db.execute(restore_query)
        self.db.commit()
        
        # Clean up temp table
        self.db.execute(text("DROP TABLE IF EXISTS apiary_updated_at_backup"))
        self.db.commit()
    
    def subtract_one_day_treatment(self, treatment_type: str):
        # Preserve updatedAt when subtracting treatment days automatically
        # The stored procedure might update updatedAt, so we save and restore it
        from sqlalchemy import text
        
        # Save current updatedAt values for all apiaries
        self.db.execute(text("DROP TABLE IF EXISTS apiary_updated_at_backup"))
        self.db.commit()
        
        save_query = text("""
            CREATE TEMP TABLE apiary_updated_at_backup AS
            SELECT id, "updatedAt" FROM apiary
        """)
        self.db.execute(save_query)
        self.db.commit()
        
        # Execute the stored procedure
        self.db.execute(text("CALL SubtractOneDayTreatment(:treatment_type)"), {"treatment_type": treatment_type})
        self.db.commit()
        
        # Restore updatedAt values
        restore_query = text("""
            UPDATE apiary 
            SET "updatedAt" = backup."updatedAt"
            FROM apiary_updated_at_backup AS backup
            WHERE apiary.id = backup.id
        """)
        self.db.execute(restore_query)
        self.db.commit()
        
        # Clean up temp table
        self.db.execute(text("DROP TABLE IF EXISTS apiary_updated_at_backup"))
        self.db.commit()
