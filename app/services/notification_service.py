from sqlalchemy.orm import Session
from app.models.notification import Notification
from app.models.apiary import Apiary
from app.models.user import User
from app.models.device import Device
from app.schemas.notification import NotificationCreate
from typing import List
from datetime import datetime, timedelta
from exponent_server_sdk import PushClient, PushMessage

class NotificationService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_notifications(self, user_id: int, unread_only: bool = False) -> List[Notification]:
        query = self.db.query(Notification).filter(Notification.userId == user_id)
        if unread_only:
            query = query.filter(Notification.isRead == False)
        return query.order_by(Notification.createdAt.desc()).all()

    def send_push_notification(self, user_id: int, title: str, message: str, data: dict = None):
        """
        Envía una notificación push real a través de Expo a TODOS los dispositivos del usuario.
        
        Args:
            user_id: ID del usuario
            title: Título de la notificación
            message: Cuerpo del mensaje
            data: Datos adicionales para la notificación (opcional)
        """
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                print(f"Usuario {user_id} no encontrado")
                return
            
            # Obtener todos los dispositivos del usuario
            devices = self.db.query(Device).filter(Device.userId == user_id).all()
            
            # Si no hay dispositivos registrados, intentar usar el token legacy (compatibilidad)
            if not devices and user.expoPushToken:
                print(f"[LEGACY] Usando token legacy para usuario {user_id}")
                # Crear un objeto simple con los atributos necesarios
                class LegacyDevice:
                    def __init__(self, token):
                        self.expoPushToken = token
                        self.id = None
                        self.deviceName = 'Legacy Device'
                devices = [LegacyDevice(user.expoPushToken)]
            
            if not devices:
                print(f"Usuario {user_id} no tiene dispositivos registrados")
                return
            
            # Enviar a cada dispositivo
            push_client = PushClient()
            success_count = 0
            error_count = 0
            
            for device in devices:
                try:
                    # Construir el mensaje con el formato requerido
                    # Nota: El SDK usa snake_case pero se serializa a camelCase en JSON
                    # Formato JSON final: {to, sound, title, body, priority, channelId, data}
                    push_message = PushMessage(
                        to=device.expoPushToken,
                        sound="default",
                        title=title,
                        body=message,
                        priority="high",  # OBLIGATORIO - Sin esto NO aparecerá
                        channel_id="default",  # OBLIGATORIO - Se serializa como "channelId" en JSON
                        data=data or {}  # Datos adicionales (opcional, ej: {"apiaryId": 123})
                    )
                    
                    # Enviar mensaje
                    response = push_client.publish(push_message)
                    device_name = getattr(device, 'deviceName', 'Unknown') or 'Unknown'
                    print(f"Push enviada a dispositivo {device.id or 'legacy'} ({device_name}): {response.status}")
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    device_name = getattr(device, 'deviceName', 'Unknown') or 'Unknown'
                    print(f"Error enviando push a dispositivo {device.id or 'legacy'} ({device_name}): {e}")
            
            print(f"Push notifications enviadas a {user.email}: {success_count} exitosas, {error_count} errores")
            
        except Exception as e:
            print(f"Error enviando push notification: {e}")
            import traceback
            traceback.print_exc()

    def create_notification(self, notification: NotificationCreate, push_data: dict = None):
        """
        Crea una notificación en la base de datos y opcionalmente envía push.
        
        Args:
            notification: Datos de la notificación
            push_data: Datos adicionales para el push (opcional, ej: {"apiaryId": 123})
        """
        db_notification = Notification(**notification.dict())
        self.db.add(db_notification)
        self.db.commit()
        self.db.refresh(db_notification)
        
        # Si es una alerta importante, intentamos enviar push
        if notification.type == "ALERT":
            self.send_push_notification(
                notification.userId, 
                notification.title, 
                notification.message,
                data=push_data
            )
            
        return db_notification

    def mark_as_read(self, notification_id: int, user_id: int):
# ... resto igual
        notification = self.db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.userId == user_id
        ).first()
        if notification:
            notification.isRead = True
            self.db.commit()
            return True
        return False

    def check_apiary_alerts(self):
        """
        Revisa todos los apiarios y genera alertas si:
        1. No se ha visitado en > 30 días.
        2. Reservas bajas (ej. honey < 5kg en invierno - simplificado).
        """
        # Umbral de abandono: 30 días
        threshold_date = datetime.now() - timedelta(days=30)
        
        # Buscar apiarios no actualizados recientemente
        neglected_apiaries = self.db.query(Apiary).filter(
            Apiary.updatedAt < threshold_date
        ).all()

        count = 0
        for apiary in neglected_apiaries:
            # Verificar si ya existe una alerta reciente para no spamear
            # (Simplificado: solo chequeamos si existe una alerta NO LEÍDA de este tipo)
            existing = self.db.query(Notification).filter(
                Notification.userId == apiary.userId,
                Notification.type == "ALERT",
                Notification.isRead == False,
                Notification.message.contains(f"apiario '{apiary.name}'")
            ).first()

            if not existing:
                # Incluir datos del apiario en el push notification
                push_data = {"apiaryId": apiary.id}
                self.create_notification(
                    NotificationCreate(
                        userId=apiary.userId,
                        title="Apiario sin visitar",
                        message=f"Hace más de 30 días que no registras actividad en el apiario '{apiary.name}'.",
                        type="ALERT"
                    ),
                    push_data=push_data
                )
                count += 1
        
        return count

