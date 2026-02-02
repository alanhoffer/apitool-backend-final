# Múltiples Dispositivos - Explicación y Solución

## 🔴 Situación Actual

**Problema**: El sistema solo guarda **UN token por usuario** en `user.expoPushToken`

**Consecuencias**:
- Si el usuario se loguea en el **Dispositivo A** → se guarda token A
- Si luego se loguea en el **Dispositivo B** → se **sobrescribe** con token B
- ❌ Las notificaciones **solo llegan al último dispositivo** (Dispositivo B)
- ❌ El Dispositivo A **deja de recibir notificaciones**

## ✅ Solución: Tabla de Dispositivos

Crear una tabla separada para gestionar múltiples tokens por usuario.

### 1. Nuevo Modelo: Device

```python
# app/models/device.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Device(Base):
    __tablename__ = "devices"
    
    id = Column(Integer, primary_key=True, index=True)
    userId = Column(Integer, ForeignKey("user.id"), nullable=False)
    expoPushToken = Column(String, nullable=False, unique=True)
    deviceName = Column(String, nullable=True)  # "iPhone 12", "Samsung Galaxy"
    platform = Column(String, nullable=True)  # "ios", "android"
    lastActive = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    createdAt = Column(DateTime, server_default=func.current_timestamp())
    
    user = relationship("User", back_populates="devices")
```

### 2. Actualizar Modelo User

```python
# Agregar relación en app/models/user.py
devices = relationship("Device", back_populates="user", cascade="all, delete-orphan")
```

### 3. Actualizar Servicio de Notificaciones

```python
def send_push_notification(self, user_id: int, title: str, message: str, data: dict = None):
    """Envía push a TODOS los dispositivos del usuario"""
    user = self.db.query(User).filter(User.id == user_id).first()
    if not user:
        return
    
    # Obtener todos los tokens del usuario
    devices = self.db.query(Device).filter(Device.userId == user_id).all()
    
    if not devices:
        print(f"Usuario {user_id} no tiene dispositivos registrados")
        return
    
    # Enviar a cada dispositivo
    for device in devices:
        try:
            push_message = PushMessage(
                to=device.expoPushToken,
                sound="default",
                title=title,
                body=message,
                priority="high",
                channel_id="default",
                data=data or {}
            )
            response = PushClient().publish(push_message)
            print(f"Push enviada a dispositivo {device.id} ({device.deviceName}): {response.status}")
        except Exception as e:
            print(f"Error enviando a dispositivo {device.id}: {e}")
```

### 4. Actualizar Endpoint push-token

```python
@router.post("/push-token")
async def register_device_token(
    token_data: PushTokenUpdate,
    device_name: str = None,  # Opcional
    platform: str = None,     # Opcional
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Buscar si el token ya existe
    existing_device = db.query(Device).filter(
        Device.expoPushToken == token_data.token
    ).first()
    
    if existing_device:
        # Actualizar último uso
        existing_device.lastActive = datetime.now()
        db.commit()
        return {"message": "Token actualizado"}
    
    # Crear nuevo dispositivo
    new_device = Device(
        userId=current_user.id,
        expoPushToken=token_data.token,
        deviceName=device_name,
        platform=platform
    )
    db.add(new_device)
    db.commit()
    
    return {"message": "Dispositivo registrado exitosamente"}
```

## 📊 Ventajas de esta Solución

✅ Un usuario puede tener múltiples dispositivos registrados
✅ Las notificaciones llegan a **TODOS** los dispositivos
✅ Se puede rastrear qué dispositivos tiene cada usuario
✅ Se puede eliminar dispositivos antiguos/inactivos
✅ Se puede ver cuándo fue la última vez que un dispositivo estuvo activo

## 🚀 Implementación Rápida (Sin cambiar modelo)

Si prefieres una solución más rápida sin crear nueva tabla, puedes:

1. Cambiar `expoPushToken` a un campo JSON que almacene un array de tokens
2. Modificar el servicio para enviar a todos los tokens del array

Pero la solución con tabla es más robusta y escalable.




























