from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.services.apiary_service import ApiaryService
from app.services.notification_service import NotificationService
import logging

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

def handle_cron():
    db: Session = SessionLocal()
    try:
        apiary_service = ApiaryService(db)
        notification_service = NotificationService(db)
        
        # Subtract food
        apiary_service.subtract_food()
        
        # Subtract one day from treatments
        apiary_service.subtract_one_day_treatment('tFence')
        apiary_service.subtract_one_day_treatment('tAmitraz')
        apiary_service.subtract_one_day_treatment('tFlumetrine')
        apiary_service.subtract_one_day_treatment('tOxalic')
        
        # Check alerts (New)
        alerts_count = notification_service.check_apiary_alerts()
        if alerts_count > 0:
            logger.info(f"Se generaron {alerts_count} alertas de apiarios.")
        
        logger.info("Se han actualizado los valores de los apiarios y verificado alertas.")
    except Exception as error:
        logger.error(f"Error al actualizar los valores de los apiarios: {error}")
    finally:
        db.close()

# Schedule the cron job to run every day at midnight
scheduler.add_job(
    handle_cron,
    trigger=CronTrigger(hour=0, minute=0),
    id="daily_apiary_update",
    name="Update apiary values daily",
    replace_existing=True,
    max_instances=1
)

