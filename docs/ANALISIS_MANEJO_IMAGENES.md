# Análisis del Manejo de Imágenes

## ✅ LO QUE ESTÁ BIEN

### 1. **Validación de Tipo de Archivo**
- ✅ Usa `python-magic` para validar el tipo real del archivo (no confía en la extensión)
- ✅ Valida MIME types: `image/jpeg`, `image/png`, `image/gif`, `image/webp`
- ✅ Rechaza archivos que no son imágenes reales

### 2. **Validación de Tamaño**
- ✅ Limita tamaño máximo a 10MB antes de procesar
- ✅ Valida que el archivo no esté vacío

### 3. **Procesamiento y Optimización**
- ✅ Redimensiona imágenes grandes a máximo 1024px (mantiene aspect ratio)
- ✅ Convierte todo a JPEG para consistencia
- ✅ Usa calidad 85 (buen balance peso/calidad)
- ✅ Optimiza con `optimize=True`
- ✅ Convierte RGBA/P a RGB (maneja transparencia correctamente)

### 4. **Nombres de Archivo**
- ✅ Usa UUID para evitar colisiones
- ✅ Estandariza extensión a `.jpg`

### 5. **Manejo de Errores**
- ✅ Captura excepciones durante procesamiento
- ✅ Retorna errores HTTP apropiados

---

## ⚠️ PROBLEMAS CRÍTICOS

### 1. **NO SE ELIMINAN IMÁGENES ANTIGUAS** 🔴

**Problema:** Cuando se actualiza o elimina un apiary, las imágenes antiguas quedan en el servidor.

**Código actual:**
```python
# update_apiary - línea 221-222
if file:
    apiary_data.image = await self._process_image(file)
    # ❌ No elimina apiary.image anterior

# delete_apiary - línea 203-214
def delete_apiary(self, apiary_id: int) -> bool:
    apiary = self.db.query(Apiary).filter(Apiary.id == apiary_id).first()
    self.db.delete(apiary)
    # ❌ No elimina el archivo de imagen
```

**Impacto:**
- El directorio `uploads/` crece indefinidamente
- Desperdicio de espacio en disco
- Posible problema de seguridad (archivos huérfanos)

**Solución necesaria:**
```python
def _delete_image_file(self, filename: str) -> None:
    """Elimina un archivo de imagen si existe y no es la imagen por defecto."""
    if filename and filename != "apiary-default.png":
        file_path = UPLOAD_DIR / filename
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception as e:
                # Log error pero no fallar la operación principal
                logger.warning(f"Failed to delete image {filename}: {e}")
```

### 2. **ENDPOINT DE IMAGEN SIN AUTENTICACIÓN** 🔴

**Problema:** Cualquiera puede acceder a las imágenes si conoce el nombre del archivo.

**Código actual:**
```python
# línea 263-271
@router.get("/profile/image/{id}")
async def get_file(id: str):
    # ❌ No requiere autenticación
    # ❌ No verifica ownership
    file_path = UPLOAD_DIR / id
    return FileResponse(file_path, media_type="image/jpeg")
```

**Impacto:**
- Cualquiera puede ver imágenes de otros usuarios
- Problema de privacidad
- Posible enumeración de archivos

**Solución necesaria:**
```python
@router.get("/profile/image/{id}")
async def get_file(
    id: str,
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    # Validar que el archivo pertenece a un apiary del usuario
    apiary_service = ApiaryService(db)
    user_id = int(payload.get("sub"))
    
    # Buscar apiary que tenga esta imagen
    apiary = db.query(Apiary).filter(
        Apiary.image == id,
        Apiary.userId == user_id
    ).first()
    
    if not apiary:
        raise HTTPException(status_code=404, detail="Image not found")
    
    file_path = UPLOAD_DIR / id
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(file_path, media_type="image/jpeg")
```

### 3. **VULNERABILIDAD PATH TRAVERSAL** 🔴

**Problema:** El parámetro `id` se usa directamente sin validar formato.

**Código actual:**
```python
@router.get("/profile/image/{id}")
async def get_file(id: str):
    file_path = UPLOAD_DIR / id  # ❌ No valida que id sea UUID válido
```

**Ataque posible:**
```
GET /apiarys/profile/image/../../../etc/passwd
GET /apiarys/profile/image/../../.env
```

**Solución:**
```python
import re

UUID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.jpg$', re.IGNORECASE)

@router.get("/profile/image/{id}")
async def get_file(id: str):
    # Validar formato UUID
    if not UUID_PATTERN.match(id) and id != "apiary-default.png":
        raise HTTPException(status_code=400, detail="Invalid image ID")
    
    file_path = UPLOAD_DIR / id
    # Path.resolve() previene path traversal
    resolved_path = file_path.resolve()
    upload_dir_resolved = UPLOAD_DIR.resolve()
    
    # Asegurar que el archivo está dentro del directorio uploads
    if not str(resolved_path).startswith(str(upload_dir_resolved)):
        raise HTTPException(status_code=403, detail="Access denied")
```

### 4. **NO HAY VALIDACIÓN DE IMAGEN POR DEFECTO** 🟠

**Problema:** Se usa `"apiary-default.png"` pero no se valida que exista.

**Código actual:**
```python
# línea 159
apiary_data.image = "apiary-default.png"
```

**Solución:**
```python
DEFAULT_IMAGE = "apiary-default.png"

def _ensure_default_image_exists(self):
    """Verifica que la imagen por defecto existe."""
    default_path = UPLOAD_DIR / DEFAULT_IMAGE
    if not default_path.exists():
        # Crear imagen por defecto o lanzar error
        logger.warning(f"Default image {DEFAULT_IMAGE} not found")
```

### 5. **NO HAY LÍMITE DE ESPACIO EN DISCO** 🟠

**Problema:** El directorio puede crecer indefinidamente.

**Solución:**
- Implementar limpieza periódica de archivos huérfanos
- Monitorear tamaño del directorio
- Alertar cuando se acerque al límite

### 6. **NO HAY BACKUP DE IMÁGENES** 🟡

**Problema:** Si se pierde el directorio, se pierden todas las imágenes.

**Solución:**
- Usar servicio de almacenamiento externo (S3, Cloud Storage)
- O implementar backup periódico

### 7. **ALMACENAMIENTO LOCAL** 🟡

**Problema:** Imágenes almacenadas en el servidor, no escalable.

**Solución:**
- Considerar migrar a S3 o similar para producción
- Permite CDN, mejor performance, escalabilidad

---

## 📋 CHECKLIST DE MEJORAS

### 🔴 Crítico (Hacer ahora)
- [ ] Eliminar imágenes antiguas al actualizar
- [ ] Eliminar imágenes al eliminar apiary
- [ ] Agregar autenticación a endpoint de imágenes
- [ ] Prevenir path traversal
- [ ] Validar formato UUID en endpoint de imágenes

### 🟠 Importante (Próxima semana)
- [ ] Validar existencia de imagen por defecto
- [ ] Implementar limpieza de archivos huérfanos
- [ ] Agregar logging de operaciones de imágenes
- [ ] Monitorear tamaño del directorio

### 🟡 Mejoras (Próximo mes)
- [ ] Migrar a almacenamiento externo (S3)
- [ ] Implementar CDN para imágenes
- [ ] Agregar múltiples tamaños (thumbnail, medium, large)
- [ ] Implementar compresión más agresiva

---

## 🔧 CÓDIGO MEJORADO SUGERIDO

### Helper para eliminar imágenes
```python
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def delete_image_file(filename: str) -> bool:
    """
    Elimina un archivo de imagen si existe.
    Retorna True si se eliminó, False si no existía.
    """
    if not filename or filename == "apiary-default.png":
        return False
    
    file_path = UPLOAD_DIR / filename
    if file_path.exists():
        try:
            file_path.unlink()
            logger.info(f"Deleted image file: {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete image {filename}: {e}")
            return False
    return False
```

### Endpoint de imagen seguro
```python
import re
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user_payload
from app.models.apiary import Apiary

router = APIRouter(prefix="/apiarys", tags=["apiarys"])

UUID_PATTERN = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.jpg$',
    re.IGNORECASE
)

@router.get("/profile/image/{id}")
async def get_apiary_image(
    id: str,
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    """
    Obtiene la imagen de un apiary.
    Requiere autenticación y verifica ownership.
    """
    user_id = int(payload.get("sub"))
    
    # Validar formato (UUID.jpg o default)
    if id != "apiary-default.png" and not UUID_PATTERN.match(id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image ID format"
        )
    
    # Si es imagen por defecto, servirla directamente
    if id == "apiary-default.png":
        file_path = UPLOAD_DIR / id
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Default image not found"
            )
        return FileResponse(file_path, media_type="image/jpeg")
    
    # Verificar que la imagen pertenece a un apiary del usuario
    apiary = db.query(Apiary).filter(
        Apiary.image == id,
        Apiary.userId == user_id
    ).first()
    
    if not apiary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found or access denied"
        )
    
    # Prevenir path traversal
    file_path = UPLOAD_DIR / id
    resolved_path = file_path.resolve()
    upload_dir_resolved = UPLOAD_DIR.resolve()
    
    if not str(resolved_path).startswith(str(upload_dir_resolved)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    return FileResponse(file_path, media_type="image/jpeg")
```

### Actualizar delete_apiary
```python
def delete_apiary(self, apiary_id: int) -> bool:
    apiary = self.db.query(Apiary).filter(Apiary.id == apiary_id).first()
    if not apiary:
        return False
    
    # Guardar nombre de imagen antes de eliminar
    image_filename = apiary.image
    
    self.db.delete(apiary)
    try:
        self.db.commit()
        # Eliminar archivo de imagen después de commit exitoso
        if image_filename:
            delete_image_file(image_filename)
        return True
    except Exception:
        self.db.rollback()
        raise
```

### Actualizar update_apiary
```python
async def update_apiary(self, apiary_id: int, apiary_data: UpdateApiary, file: Optional[UploadFile] = None) -> Optional[Apiary]:
    apiary = self.db.query(Apiary).filter(Apiary.id == apiary_id).first()
    if not apiary:
        return None
    
    old_image_filename = None
    
    if file:
        old_image_filename = apiary.image  # Guardar nombre anterior
        apiary_data.image = await self._process_image(file)
    
    # ... resto del código ...
    
    try:
        self.db.commit()
        self.db.refresh(apiary)
        
        # Eliminar imagen anterior después de commit exitoso
        if old_image_filename:
            delete_image_file(old_image_filename)
            
    except Exception:
        self.db.rollback()
        raise
    
    return apiary
```

---

## 📊 RESUMEN

### Estado Actual: ⚠️ **NECESITA MEJORAS**

**Aspectos positivos:**
- ✅ Validación de tipo y tamaño
- ✅ Optimización de imágenes
- ✅ Nombres únicos (UUID)

**Problemas críticos:**
- 🔴 No elimina imágenes antiguas
- 🔴 Endpoint sin autenticación
- 🔴 Vulnerable a path traversal

**Recomendación:** Implementar las mejoras críticas antes de producción.


