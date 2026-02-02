from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.services.apiary_service import ApiaryService
from app.services.notification_service import NotificationService
try:
    from app.utils.business_metrics import (
        cron_jobs_executed_total,
        cron_job_duration_seconds
    )
    METRICS_AVAILABLE = True
except (ImportError, AttributeError):
    METRICS_AVAILABLE = False
    # Crear métricas dummy
    class DummyMetric:
        def labels(self, **kwargs):
            return self
        def inc(self, value=1):
            pass
        def observe(self, value):
            pass
    
    cron_jobs_executed_total = DummyMetric()
    cron_job_duration_seconds = DummyMetric()
import logging
import time

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

def handle_cron():
    job_name = "daily_apiary_update"
    start_time = time.time()
    
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
        
        # Registrar métricas de éxito
        duration = time.time() - start_time
        cron_jobs_executed_total.labels(job_name=job_name, status="success").inc()
        cron_job_duration_seconds.labels(job_name=job_name).observe(duration)
        
    except Exception as error:
        # Registrar métricas de error
        duration = time.time() - start_time
        cron_jobs_executed_total.labels(job_name=job_name, status="failed").inc()
        cron_job_duration_seconds.labels(job_name=job_name).observe(duration)
        
        logger.error(f"Error al actualizar los valores de los apiarios: {error}", exc_info=True)
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

