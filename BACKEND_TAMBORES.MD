# Guía Backend - Gestión de Tambores Escaneados

## 📋 Tabla de Contenidos
1. [Estructura de Base de Datos](#estructura-de-base-de-datos)
2. [Endpoints de la API](#endpoints-de-la-api)
3. [Estructura de Datos](#estructura-de-datos)
4. [Ejemplos de Implementación](#ejemplos-de-implementación)
5. [Integración Frontend](#integración-frontend)

---

## 🗄️ Estructura de Base de Datos

### Tabla: `drums` (Tambores)

**Nota**: Esta estructura está adaptada para FastAPI + PostgreSQL + SQLAlchemy, usando Integer para IDs (siguiendo la convención del proyecto).

```sql
CREATE TABLE drums (
    id SERIAL PRIMARY KEY,
    userId INTEGER NOT NULL,
    code VARCHAR(100) NOT NULL,
    tare NUMERIC(10, 2) NOT NULL,
    weight NUMERIC(10, 2) NOT NULL,
    sold BOOLEAN DEFAULT FALSE,
    createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_user FOREIGN KEY (userId) REFERENCES "user"(id) ON DELETE CASCADE
);

CREATE INDEX idx_drums_user_id ON drums(userId);
CREATE INDEX idx_drums_code ON drums(code);
CREATE INDEX idx_drums_sold ON drums(sold);
CREATE INDEX idx_drums_created_at ON drums(createdAt);
```

**Alternativa con UUID (si prefieres UUIDs):**
```sql
CREATE TABLE drums (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    userId INTEGER NOT NULL,
    code VARCHAR(100) NOT NULL,
    tare NUMERIC(10, 2) NOT NULL,
    weight NUMERIC(10, 2) NOT NULL,
    sold BOOLEAN DEFAULT FALSE,
    createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_user FOREIGN KEY (userId) REFERENCES "user"(id) ON DELETE CASCADE
);
```

### Campos Explicados:
- **id**: Identificador único del tambor (Integer auto-incremental o UUID según preferencia)
- **userId**: ID del usuario propietario (Integer, referencia a `user.id`)
- **code**: Código del tambor (código de barras escaneado)
- **tare**: Peso de la tara en kilogramos (NUMERIC 10,2)
- **weight**: Peso total en kilogramos (NUMERIC 10,2)
- **sold**: Indica si el tambor fue vendido (default: false)
- **createdAt**: Fecha de creación (TIMESTAMP)
- **updatedAt**: Fecha de última actualización (TIMESTAMP)

### Índices:
- `idx_drums_user_id`: Para búsquedas rápidas por usuario
- `idx_drums_code`: Para búsquedas por código
- `idx_drums_sold`: Para filtrar tambores vendidos
- `idx_drums_created_at`: Para ordenar por fecha

---

## 🔌 Endpoints de la API

### Base URL
```
http://localhost:8000/api  # Desarrollo
https://tu-api.com/api     # Producción
```

### Autenticación
Todos los endpoints requieren autenticación mediante token JWT en el header:
```
Authorization: Bearer <token>
```

---

### 1. Crear Tambor
**POST** `/drums`

Crea un nuevo tambor escaneado.

**Request Body:**
```json
{
  "code": "TAMBOR-001",
  "tare": 15.5,
  "weight": 45.2
}
```

**Response 201 Created:**
```json
{
  "id": 1,
  "userId": 2,
  "code": "TAMBOR-001",
  "tare": 15.5,
  "weight": 45.2,
  "sold": false,
  "createdAt": "2024-01-15T10:30:00Z",
  "updatedAt": "2024-01-15T10:30:00Z"
}
```

**Errores:**
- `400 Bad Request`: Datos inválidos
- `401 Unauthorized`: Token inválido o expirado
- `409 Conflict`: Código duplicado (opcional, si quieres validar duplicados)

---

### 2. Obtener Todos los Tambores
**GET** `/drums?sold=false&page=1&limit=50`

Obtiene la lista de tambores del usuario autenticado.

**Query Parameters:**
- `sold` (boolean, opcional): Filtrar por tambores vendidos
  - `false` o sin parámetro: Solo tambores no vendidos
  - `true`: Solo tambores vendidos
- `page` (int, opcional): Número de página (default: 1)
- `limit` (int, opcional): Cantidad de resultados por página (default: 50)

**Response 200 OK:**
```json
{
  "data": [
    {
      "id": 1,
      "userId": 2,
      "code": "TAMBOR-001",
      "tare": 15.5,
      "weight": 45.2,
      "sold": false,
      "createdAt": "2024-01-15T10:30:00Z",
      "updatedAt": "2024-01-15T10:30:00Z"
    },
    {
      "id": 2,
      "userId": 2,
      "code": "TAMBOR-002",
      "tare": 18.3,
      "weight": 52.7,
      "sold": false,
      "createdAt": "2024-01-15T11:00:00Z",
      "updatedAt": "2024-01-15T11:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 2,
    "totalPages": 1
  }
}
```

---

### 3. Obtener Tambor por ID
**GET** `/drums/{id}`

Obtiene un tambor específico por su ID.

**Response 200 OK:**
```json
{
  "id": 1,
  "userId": 2,
  "code": "TAMBOR-001",
  "tare": 15.5,
  "weight": 45.2,
  "sold": false,
  "createdAt": "2024-01-15T10:30:00Z",
  "updatedAt": "2024-01-15T10:30:00Z"
}
```

**Errores:**
- `404 Not Found`: Tambor no encontrado
- `403 Forbidden`: El tambor no pertenece al usuario

---

### 4. Actualizar Tambor
**PUT** `/drums/{id}`

Actualiza un tambor existente.

**Request Body:**
```json
{
  "code": "TAMBOR-001-UPDATED",
  "tare": 16.0,
  "weight": 46.5,
  "sold": false
}
```

**Response 200 OK:**
```json
{
  "id": 1,
  "userId": 2,
  "code": "TAMBOR-001-UPDATED",
  "tare": 16.0,
  "weight": 46.5,
  "sold": false,
  "createdAt": "2024-01-15T10:30:00Z",
  "updatedAt": "2024-01-15T12:00:00Z"
}
```

---

### 5. Marcar Tambor como Vendido
**PATCH** `/drums/{id}/sold`

Marca un tambor como vendido o no vendido.

**Request Body:**
```json
{
  "sold": true
}
```

**Response 200 OK:**
```json
{
  "id": 1,
  "userId": 2,
  "code": "TAMBOR-001",
  "tare": 15.5,
  "weight": 45.2,
  "sold": true,
  "createdAt": "2024-01-15T10:30:00Z",
  "updatedAt": "2024-01-15T12:30:00Z"
}
```

---

### 6. Eliminar Tambor
**DELETE** `/drums/{id}`

Elimina un tambor específico.

**Response 200 OK:**
```json
{
  "message": "Tambor eliminado correctamente"
}
```

**Errores:**
- `404 Not Found`: Tambor no encontrado
- `403 Forbidden`: El tambor no pertenece al usuario

---

### 7. Eliminar Todos los Tambores
**DELETE** `/drums`

Elimina todos los tambores del usuario autenticado.

**Query Parameters:**
- `sold` (boolean, opcional): Si se especifica, solo elimina tambores vendidos o no vendidos
  - `true`: Solo elimina tambores vendidos
  - `false`: Solo elimina tambores no vendidos
  - Sin parámetro: Elimina todos

**Response 200 OK:**
```json
{
  "message": "Se eliminaron 5 tambores correctamente",
  "deleted_count": 5
}
```

---

### 8. Obtener Estadísticas
**GET** `/drums/stats`

Obtiene estadísticas agregadas de los tambores del usuario.

**Response 200 OK:**
```json
{
  "total": 10,
  "sold": 3,
  "not_sold": 7,
  "total_tare": 165.5,
  "total_weight": 485.2,
  "net_weight": 319.7
}
```

**Cálculos:**
- `total`: Total de tambores
- `sold`: Cantidad de tambores vendidos
- `not_sold`: Cantidad de tambores no vendidos
- `total_tare`: Suma de todas las taras
- `total_weight`: Suma de todos los pesos
- `net_weight`: Peso neto (total_weight - total_tare)

---

## 📊 Estructura de Datos

### Modelo de Tambor (Drum)
```typescript
interface Drum {
  id: number;  // Integer (o string si usas UUID)
  userId: number;
  code: string;
  tare: number;
  weight: number;
  sold: boolean;
  createdAt: string; // ISO 8601
  updatedAt: string; // ISO 8601
}
```

### Request - Crear Tambor
```typescript
interface CreateDrumRequest {
  code: string;
  tare: number;
  weight: number;
}
```

### Request - Actualizar Tambor
```typescript
interface UpdateDrumRequest {
  code?: string;
  tare?: number;
  weight?: number;
  sold?: boolean;
}
```

### Response - Lista de Tambores
```typescript
interface DrumsListResponse {
  data: Drum[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;  // camelCase
  };
}
```

---

## 💻 Ejemplos de Implementación

### FastAPI + PostgreSQL + SQLAlchemy (Recomendado para este proyecto)

#### Modelo (app/models/drum.py)
```python
from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Drum(Base):
    __tablename__ = "drums"
    
    id = Column(Integer, primary_key=True, index=True)
    userId = Column(Integer, ForeignKey("user.id"), nullable=False, index=True)
    code = Column(String(100), nullable=False, index=True)
    tare = Column(Numeric(10, 2), nullable=False)
    weight = Column(Numeric(10, 2), nullable=False)
    sold = Column(Boolean, default=False, index=True)
    createdAt = Column(DateTime, server_default=func.current_timestamp(), index=True)
    updatedAt = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    user = relationship("User", back_populates="drums")
    
    __table_args__ = (
        Index('idx_drums_user_id', 'userId'),
        Index('idx_drums_code', 'code'),
        Index('idx_drums_sold', 'sold'),
        Index('idx_drums_created_at', 'createdAt'),
    )
```

#### Schema (app/schemas/drum.py)
```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal

class DrumBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=100)
    tare: Decimal = Field(..., gt=0, decimal_places=2)
    weight: Decimal = Field(..., gt=0, decimal_places=2)

class DrumCreate(DrumBase):
    pass

class DrumUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=100)
    tare: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    weight: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    sold: Optional[bool] = None

class DrumResponse(DrumBase):
    id: int
    userId: int
    sold: bool
    createdAt: datetime
    updatedAt: datetime
    
    class Config:
        from_attributes = True

class DrumsListResponse(BaseModel):
    data: list[DrumResponse]
    pagination: dict

class DrumStats(BaseModel):
    total: int
    sold: int
    not_sold: int
    total_tare: Decimal
    total_weight: Decimal
    net_weight: Decimal
```

#### Servicio (app/services/drum_service.py)
```python
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.models.drum import Drum
from app.schemas.drum import DrumCreate, DrumUpdate
from typing import List, Optional
from decimal import Decimal

class DrumService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_drum(self, user_id: int, drum_data: DrumCreate) -> Drum:
        drum = Drum(
            userId=user_id,
            code=drum_data.code,
            tare=drum_data.tare,
            weight=drum_data.weight
        )
        self.db.add(drum)
        self.db.commit()
        self.db.refresh(drum)
        return drum
    
    def get_drums(
        self, 
        user_id: int, 
        sold: Optional[bool] = None,
        page: int = 1,
        limit: int = 50
    ) -> tuple[List[Drum], int]:
        query = self.db.query(Drum).filter(Drum.userId == user_id)
        
        if sold is not None:
            query = query.filter(Drum.sold == sold)
        
        total = query.count()
        offset = (page - 1) * limit
        
        drums = query.order_by(Drum.createdAt.desc()).offset(offset).limit(limit).all()
        return drums, total
    
    def get_drum_by_id(self, drum_id: int, user_id: int) -> Optional[Drum]:
        return self.db.query(Drum).filter(
            and_(Drum.id == drum_id, Drum.userId == user_id)
        ).first()
    
    def update_drum(self, drum_id: int, user_id: int, updates: DrumUpdate) -> Optional[Drum]:
        drum = self.get_drum_by_id(drum_id, user_id)
        if not drum:
            return None
        
        update_data = updates.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(drum, key, value)
        
        self.db.commit()
        self.db.refresh(drum)
        return drum
    
    def mark_as_sold(self, drum_id: int, user_id: int, sold: bool) -> Optional[Drum]:
        return self.update_drum(drum_id, user_id, DrumUpdate(sold=sold))
    
    def delete_drum(self, drum_id: int, user_id: int) -> bool:
        drum = self.get_drum_by_id(drum_id, user_id)
        if not drum:
            return False
        
        self.db.delete(drum)
        self.db.commit()
        return True
    
    def delete_all_drums(self, user_id: int, sold: Optional[bool] = None) -> int:
        query = self.db.query(Drum).filter(Drum.userId == user_id)
        
        if sold is not None:
            query = query.filter(Drum.sold == sold)
        
        count = query.count()
        query.delete(synchronize_session=False)
        self.db.commit()
        return count
    
    def get_stats(self, user_id: int) -> dict:
        result = self.db.query(
            func.count(Drum.id).label('total'),
            func.sum(func.cast(Drum.sold, Integer)).label('sold'),
            func.sum(func.cast(~Drum.sold, Integer)).label('not_sold'),
            func.sum(Drum.tare).label('total_tare'),
            func.sum(Drum.weight).label('total_weight')
        ).filter(Drum.userId == user_id).first()
        
        total_tare = float(result.total_tare or 0)
        total_weight = float(result.total_weight or 0)
        net_weight = total_weight - total_tare
        
        return {
            "total": result.total or 0,
            "sold": int(result.sold or 0),
            "not_sold": int(result.not_sold or 0),
            "total_tare": Decimal(str(total_tare)),
            "total_weight": Decimal(str(total_weight)),
            "net_weight": Decimal(str(net_weight))
        }
```

#### Router (app/routers/drum.py)
```python
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.services.drum_service import DrumService
from app.schemas.drum import (
    DrumCreate, DrumUpdate, DrumResponse, 
    DrumsListResponse, DrumStats
)
from typing import Optional

router = APIRouter(prefix="/drums", tags=["drums"])

@router.post("", response_model=DrumResponse, status_code=status.HTTP_201_CREATED)
async def create_drum(
    drum_data: DrumCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = DrumService(db)
    return service.create_drum(current_user.id, drum_data)

@router.get("", response_model=DrumsListResponse)
async def get_drums(
    sold: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = DrumService(db)
    drums, total = service.get_drums(current_user.id, sold, page, limit)
    
    return {
        "data": drums,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": total,
            "totalPages": (total + limit - 1) // limit
        }
    }

@router.get("/stats", response_model=DrumStats)
async def get_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = DrumService(db)
    return service.get_stats(current_user.id)

@router.get("/{id}", response_model=DrumResponse)
async def get_drum(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = DrumService(db)
    drum = service.get_drum_by_id(id, current_user.id)
    if not drum:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tambor no encontrado"
        )
    return drum

@router.put("/{id}", response_model=DrumResponse)
async def update_drum(
    id: int,
    updates: DrumUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = DrumService(db)
    drum = service.update_drum(id, current_user.id, updates)
    if not drum:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tambor no encontrado"
        )
    return drum

@router.patch("/{id}/sold", response_model=DrumResponse)
async def mark_as_sold(
    id: int,
    sold: bool,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = DrumService(db)
    drum = service.mark_as_sold(id, current_user.id, sold)
    if not drum:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tambor no encontrado"
        )
    return drum

@router.delete("/{id}")
async def delete_drum(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = DrumService(db)
    if not service.delete_drum(id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tambor no encontrado"
        )
    return {"message": "Tambor eliminado correctamente"}

@router.delete("")
async def delete_all_drums(
    sold: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = DrumService(db)
    deleted_count = service.delete_all_drums(current_user.id, sold)
    return {
        "message": f"Se eliminaron {deleted_count} tambores correctamente",
        "deleted_count": deleted_count
    }
```

#### Actualizar app/main.py
```python
# Agregar el router de drums
from app.routers import drum_router

app.include_router(drum_router)
```

#### Actualizar app/models/user.py
```python
# Agregar relación con drums
drums = relationship("Drum", back_populates="user", cascade="all, delete-orphan")
```

---

### Node.js + Express + MySQL

#### Modelo (models/drum.js)
```javascript
const db = require('../config/database');

class Drum {
  static async create(userId, drumData) {
    const { code, tare, weight } = drumData;
    const id = require('uuid').v4();
    
    const query = `
      INSERT INTO drums (id, user_id, code, tare, weight)
      VALUES (?, ?, ?, ?, ?)
    `;
    
    await db.execute(query, [id, userId, code, tare, weight]);
    return this.findById(id, userId);
  }

  static async findByUserId(userId, filters = {}) {
    let query = 'SELECT * FROM drums WHERE user_id = ?';
    const params = [userId];
    
    if (filters.sold !== undefined) {
      query += ' AND sold = ?';
      params.push(filters.sold);
    }
    
    query += ' ORDER BY created_at DESC';
    
    if (filters.limit) {
      query += ' LIMIT ?';
      params.push(filters.limit);
      
      if (filters.offset) {
        query += ' OFFSET ?';
        params.push(filters.offset);
      }
    }
    
    const [rows] = await db.execute(query, params);
    return rows;
  }

  static async findById(id, userId) {
    const query = 'SELECT * FROM drums WHERE id = ? AND user_id = ?';
    const [rows] = await db.execute(query, [id, userId]);
    return rows[0] || null;
  }

  static async update(id, userId, updates) {
    const fields = [];
    const values = [];
    
    Object.keys(updates).forEach(key => {
      if (updates[key] !== undefined) {
        fields.push(`${key} = ?`);
        values.push(updates[key]);
      }
    });
    
    if (fields.length === 0) return null;
    
    values.push(id, userId);
    const query = `
      UPDATE drums 
      SET ${fields.join(', ')}, updated_at = CURRENT_TIMESTAMP
      WHERE id = ? AND user_id = ?
    `;
    
    await db.execute(query, values);
    return this.findById(id, userId);
  }

  static async delete(id, userId) {
    const query = 'DELETE FROM drums WHERE id = ? AND user_id = ?';
    const [result] = await db.execute(query, [id, userId]);
    return result.affectedRows > 0;
  }

  static async deleteAll(userId, sold = null) {
    let query = 'DELETE FROM drums WHERE user_id = ?';
    const params = [userId];
    
    if (sold !== null) {
      query += ' AND sold = ?';
      params.push(sold);
    }
    
    const [result] = await db.execute(query, params);
    return result.affectedRows;
  }

  static async getStats(userId) {
    const query = `
      SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN sold = 1 THEN 1 ELSE 0 END) as sold,
        SUM(CASE WHEN sold = 0 THEN 1 ELSE 0 END) as not_sold,
        SUM(tare) as total_tare,
        SUM(weight) as total_weight,
        SUM(weight - tare) as net_weight
      FROM drums
      WHERE user_id = ?
    `;
    
    const [rows] = await db.execute(query, [userId]);
    return rows[0];
  }
}

module.exports = Drum;
```

#### Controlador (controllers/drumController.js)
```javascript
const Drum = require('../models/drum');

exports.create = async (req, res) => {
  try {
    const { code, tare, weight } = req.body;
    const userId = req.user.id; // Del middleware de autenticación
    
    // Validaciones
    if (!code || !tare || !weight) {
      return res.status(400).json({ error: 'Faltan campos requeridos' });
    }
    
    if (tare <= 0 || weight <= 0) {
      return res.status(400).json({ error: 'Tara y peso deben ser mayores a 0' });
    }
    
    const drum = await Drum.create(userId, { code, tare, weight });
    res.status(201).json(drum);
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Error al crear tambor' });
  }
};

exports.getAll = async (req, res) => {
  try {
    const userId = req.user.id;
    const { sold, page = 1, limit = 50 } = req.query;
    
    const filters = {};
    if (sold !== undefined) {
      filters.sold = sold === 'true';
    }
    
    const offset = (parseInt(page) - 1) * parseInt(limit);
    filters.limit = parseInt(limit);
    filters.offset = offset;
    
    const drums = await Drum.findByUserId(userId, filters);
    const total = await Drum.countByUserId(userId, sold !== undefined ? { sold: sold === 'true' } : {});
    
    res.json({
      data: drums,
      pagination: {
        page: parseInt(page),
        limit: parseInt(limit),
        total,
        total_pages: Math.ceil(total / parseInt(limit))
      }
    });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Error al obtener tambores' });
  }
};

exports.getById = async (req, res) => {
  try {
    const { id } = req.params;
    const userId = req.user.id;
    
    const drum = await Drum.findById(id, userId);
    if (!drum) {
      return res.status(404).json({ error: 'Tambor no encontrado' });
    }
    
    res.json(drum);
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Error al obtener tambor' });
  }
};

exports.update = async (req, res) => {
  try {
    const { id } = req.params;
    const userId = req.user.id;
    const updates = req.body;
    
    const drum = await Drum.findById(id, userId);
    if (!drum) {
      return res.status(404).json({ error: 'Tambor no encontrado' });
    }
    
    const updated = await Drum.update(id, userId, updates);
    res.json(updated);
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Error al actualizar tambor' });
  }
};

exports.markAsSold = async (req, res) => {
  try {
    const { id } = req.params;
    const { sold } = req.body;
    const userId = req.user.id;
    
    const drum = await Drum.findById(id, userId);
    if (!drum) {
      return res.status(404).json({ error: 'Tambor no encontrado' });
    }
    
    const updated = await Drum.update(id, userId, { sold });
    res.json(updated);
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Error al actualizar estado' });
  }
};

exports.delete = async (req, res) => {
  try {
    const { id } = req.params;
    const userId = req.user.id;
    
    const deleted = await Drum.delete(id, userId);
    if (!deleted) {
      return res.status(404).json({ error: 'Tambor no encontrado' });
    }
    
    res.json({ message: 'Tambor eliminado correctamente' });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Error al eliminar tambor' });
  }
};

exports.deleteAll = async (req, res) => {
  try {
    const userId = req.user.id;
    const { sold } = req.query;
    
    let soldFilter = null;
    if (sold !== undefined) {
      soldFilter = sold === 'true';
    }
    
    const deletedCount = await Drum.deleteAll(userId, soldFilter);
    res.json({
      message: `Se eliminaron ${deletedCount} tambores correctamente`,
      deleted_count: deletedCount
    });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Error al eliminar tambores' });
  }
};

exports.getStats = async (req, res) => {
  try {
    const userId = req.user.id;
    const stats = await Drum.getStats(userId);
    res.json(stats);
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Error al obtener estadísticas' });
  }
};
```

#### Rutas (routes/drums.js)
```javascript
const express = require('express');
const router = express.Router();
const drumController = require('../controllers/drumController');
const authMiddleware = require('../middleware/auth');

// Todas las rutas requieren autenticación
router.use(authMiddleware);

router.post('/', drumController.create);
router.get('/', drumController.getAll);
router.get('/stats', drumController.getStats);
router.get('/:id', drumController.getById);
router.put('/:id', drumController.update);
router.patch('/:id/sold', drumController.markAsSold);
router.delete('/:id', drumController.delete);
router.delete('/', drumController.deleteAll);

module.exports = router;
```

---

### Python + Flask + SQLAlchemy

#### Modelo (models/drum.py)
```python
from sqlalchemy import Column, String, Numeric, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

class Drum(db.Model):
    __tablename__ = 'drums'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False)
    code = Column(String(100), nullable=False)
    tare = Column(Numeric(10, 2), nullable=False)
    weight = Column(Numeric(10, 2), nullable=False)
    sold = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship('User', backref='drums')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'code': self.code,
            'tare': float(self.tare),
            'weight': float(self.weight),
            'sold': self.sold,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
```

#### Controlador (controllers/drum_controller.py)
```python
from flask import Blueprint, request, jsonify
from models.drum import Drum
from middleware.auth import token_required
from sqlalchemy import func

drums_bp = Blueprint('drums', __name__)

@drums_bp.route('/drums', methods=['POST'])
@token_required
def create_drum(current_user):
    data = request.get_json()
    
    if not all(k in data for k in ['code', 'tare', 'weight']):
        return jsonify({'error': 'Faltan campos requeridos'}), 400
    
    drum = Drum(
        user_id=current_user.id,
        code=data['code'],
        tare=data['tare'],
        weight=data['weight']
    )
    
    db.session.add(drum)
    db.session.commit()
    
    return jsonify(drum.to_dict()), 201

@drums_bp.route('/drums', methods=['GET'])
@token_required
def get_drums(current_user):
    sold = request.args.get('sold')
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 50))
    
    query = Drum.query.filter_by(user_id=current_user.id)
    
    if sold is not None:
        query = query.filter_by(sold=(sold.lower() == 'true'))
    
    total = query.count()
    drums = query.order_by(Drum.created_at.desc()).paginate(
        page=page, per_page=limit, error_out=False
    )
    
    return jsonify({
        'data': [drum.to_dict() for drum in drums.items],
        'pagination': {
            'page': page,
            'limit': limit,
            'total': total,
            'total_pages': drums.pages
        }
    }), 200
```

---

## 🔗 Integración Frontend

### Módulo API (modules/API/Drums.tsx)
```typescript
import apiClient from '../client';

export interface Drum {
  id: number;  // o string si usas UUID
  userId: number;
  code: string;
  tare: number;
  weight: number;
  sold: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface CreateDrumRequest {
  code: string;
  tare: number;
  weight: number;
}

export interface DrumsListResponse {
  data: Drum[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;  // camelCase
  };
}

export interface DrumsStats {
  total: number;
  sold: number;
  not_sold: number;
  total_tare: number;
  total_weight: number;
  net_weight: number;
}

export const createDrum = async (data: CreateDrumRequest): Promise<Drum> => {
  const response = await apiClient.post('/drums', data);
  return response.data;
};

export const getDrums = async (params?: {
  sold?: boolean;
  page?: number;
  limit?: number;
}): Promise<DrumsListResponse> => {
  const response = await apiClient.get('/drums', { params });
  return response.data;
};

export const getDrumById = async (id: string): Promise<Drum> => {
  const response = await apiClient.get(`/drums/${id}`);
  return response.data;
};

export const updateDrum = async (
  id: string,
  data: Partial<CreateDrumRequest>
): Promise<Drum> => {
  const response = await apiClient.put(`/drums/${id}`, data);
  return response.data;
};

export const markDrumAsSold = async (
  id: string,
  sold: boolean
): Promise<Drum> => {
  const response = await apiClient.patch(`/drums/${id}/sold`, { sold });
  return response.data;
};

export const deleteDrum = async (id: string): Promise<void> => {
  await apiClient.delete(`/drums/${id}`);
};

export const deleteAllDrums = async (sold?: boolean): Promise<{ deleted_count: number }> => {
  const params = sold !== undefined ? { sold } : {};
  const response = await apiClient.delete('/drums', { params });
  return response.data;
};

export const getDrumsStats = async (): Promise<DrumsStats> => {
  const response = await apiClient.get('/drums/stats');
  return response.data;
};
```

---

## ✅ Checklist de Implementación

- [ ] Crear tabla `drums` en la base de datos
- [ ] Implementar modelo/entidad Drum
- [ ] Crear controlador con todos los métodos
- [ ] Configurar rutas de la API
- [ ] Agregar middleware de autenticación
- [ ] Implementar validaciones de datos
- [ ] Agregar manejo de errores
- [ ] Probar todos los endpoints
- [ ] Actualizar frontend para usar la API
- [ ] Migrar datos de AsyncStorage a la base de datos (si aplica)

---

## 🔒 Consideraciones de Seguridad

1. **Autenticación**: Todos los endpoints deben verificar el token JWT
2. **Autorización**: Los usuarios solo pueden acceder a sus propios tambores
3. **Validación**: Validar todos los datos de entrada
4. **Sanitización**: Limpiar datos antes de guardarlos
5. **Rate Limiting**: Implementar límites de requests por usuario
6. **Logging**: Registrar todas las operaciones importantes

---

## 📝 Notas Adicionales

- Los códigos de tambor pueden duplicarse entre usuarios diferentes
- Considera agregar un campo `deletedAt` para soft deletes
- Puedes agregar más campos como `location`, `notes`, etc.
- Considera agregar un endpoint para buscar tambores por código
- Implementa caché si esperas muchas consultas

---

## ⚠️ Cambios Importantes para FastAPI

Esta guía ha sido adaptada para el proyecto actual que usa **FastAPI + PostgreSQL + SQLAlchemy**:

### 1. **Tipos de Datos**
- ✅ **IDs**: Cambiados de UUID strings a `Integer` (siguiendo la convención del proyecto)
- ✅ **Decimales**: Usa `NUMERIC(10, 2)` en PostgreSQL
- ✅ **Timestamps**: Usa `func.current_timestamp()` de SQLAlchemy

### 2. **Convención de Nombres**
- ✅ **camelCase**: Usa `userId`, `createdAt`, `updatedAt` en lugar de `user_id`, `created_at`
- ✅ **Tabla**: `drums` (minúsculas, plural)
- ✅ **Campos**: `userId` (camelCase) en lugar de `user_id` (snake_case)

### 3. **Base de Datos**
- ✅ **PostgreSQL**: En lugar de MySQL
- ✅ **Índices**: Sintaxis de PostgreSQL
- ✅ **Foreign Keys**: Referencia a `"user"` (con comillas porque es palabra reservada)

### 4. **Implementación FastAPI**
- ✅ **Modelo SQLAlchemy**: Con `Base` y `relationship()`
- ✅ **Schemas Pydantic**: Para validación y serialización
- ✅ **Servicio**: Lógica de negocio separada
- ✅ **Router**: Con dependencias de autenticación (`get_current_user`)
- ✅ **Endpoints**: Formato FastAPI (`{id}` en lugar de `:id`)

### 5. **Ejemplo Completo Agregado**
- ✅ Modelo completo en `app/models/drum.py`
- ✅ Schemas en `app/schemas/drum.py`
- ✅ Servicio en `app/services/drum_service.py`
- ✅ Router en `app/routers/drum.py`
- ✅ Instrucciones para integrar en `app/main.py`

### 6. **Respuestas de API Actualizadas**
- ✅ Todos los ejemplos de JSON usan `camelCase`
- ✅ IDs son números enteros
- ✅ `totalPages` en lugar de `total_pages`

---

## 🔧 Resumen de Correcciones Aplicadas

| Aspecto | Antes | Después |
|---------|-------|---------|
| Tipo de ID | UUID string | Integer |
| Naming | snake_case | camelCase |
| BD | MySQL | PostgreSQL |
| Framework | Express/Flask | FastAPI |
| Endpoints | `/drums/:id` | `/drums/{id}` |
| Timestamps | `created_at` | `createdAt` |
| Foreign Key | `user_id` | `userId` |

La guía ahora está completamente adaptada para tu stack tecnológico actual. 🚀
