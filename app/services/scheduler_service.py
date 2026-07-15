import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.jobs.visa_expiry_job import check_visa_expiries

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(
    timezone="Africa/Lagos",
)


def start_scheduler() -> None:
    if scheduler.running:
        return

    scheduler.add_job(
        check_visa_expiries,
        trigger=CronTrigger(
            hour=8,
            minute=0,
            timezone="Africa/Lagos",
        ),
        id="daily_visa_expiry_check",
        name="Daily visa expiry notification check",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=3600,
    )

    scheduler.start()

    logger.info("Visa expiry scheduler started")


def stop_scheduler() -> None:
    if not scheduler.running:
        return

    scheduler.shutdown(wait=False)

    logger.info("Visa expiry scheduler stopped")