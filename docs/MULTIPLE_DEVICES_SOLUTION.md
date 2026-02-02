# Solución para Múltiples Dispositivos - Push Notifications

## Problema Actual

El sistema actual solo guarda **un token por usuario** en el campo `expoPushToken` de la tabla `user`. Esto significa:

1. ❌ Si un usuario se loguea en 2 dispositivos, solo se guarda el token del último
2. ❌ Las notificaciones solo llegan al último dispositivo que registró el token
3. ❌ Si el usuario cambia de dispositivo, pierde las notificaciones en el anterior

## Solución Propuesta

Crear una tabla separada para gestionar múltiples tokens por usuario.

### Opción 1: Tabla de Dispositivos (Recomendada)

```python
# app/models/device.py
class Device(Base):
    __tablename__ = "devices"
    
    id = Column(Integer, primary_key=True, index=True)
    userId = Column(Integer, ForeignKey("user.id"), nullable=False)
    expoPushToken = Column(String, nullable=False, unique=True)
    deviceName = Column(String, nullable=True)  # "iPhone 12", "Samsung Galaxy", etc.
    platform = Column(String, nullable=True)  # "ios", "android"
    lastActive = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    createdAt = Column(DateTime, server_default=func.current_timestamp())
    
    user = relationship("User", back_populates="devices")
```

### Cambios Necesarios:

1. **Modelo User**: Agregar relación con devices
2. **Servicio de Notificaciones**: Enviar a TODOS los tokens del usuario
3. **Endpoint push-token**: Registrar/actualizar token por dispositivo
4. **Endpoint para listar dispositivos**: Ver dispositivos activos del usuario

## Implementación Rápida (Sin cambiar modelo)

Si no quieres crear una nueva tabla ahora, puedes modificar el servicio para enviar a múltiples tokens almacenados en un campo JSON o array. Pero la solución con tabla es más robusta.




























