import logging
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from src import models, settings
from src.alerts import process_alert
from src.config import get_sla_config
from src.database import SessionLocal

logger = logging.getLogger(__name__)


def evaluate_slas() -> None:
    """
    Scan all tickets and generate alerts or breaches
    by calling process_alert().
    """
    db: Session = SessionLocal()
    try:
        sla_config = get_sla_config()
        now = datetime.now(timezone.utc)

        tickets = db.query(models.Ticket).all()

        for ticket in tickets:
            created = ticket.created_at
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            elapsed_minutes = (now - created).total_seconds() / 60

            for sla_type in ("response", "resolution"):
                tier = ticket.customer_tier
                priority = ticket.priority
                try:
                    target_minutes = sla_config[tier][priority][sla_type]
                except KeyError:
                    logger.warning(
                        "No SLA config for %s/%s/%s", tier, priority, sla_type
                    )
                    continue

                percent_used = elapsed_minutes / target_minutes

                if percent_used >= settings.BREACH_THRESHOLD:
                    state = models.SLAState.BREACH
                elif percent_used >= settings.ALERT_THRESHOLD:
                    state = models.SLAState.ALERT
                else:
                    continue

                details = {
                    "elapsed_minutes": elapsed_minutes,
                    "target_minutes": target_minutes,
                    "percent_used": percent_used,
                }

                process_alert(ticket.id, sla_type, state, details)

    except Exception:
        logger.exception("Error during SLA evaluation")
    finally:
        db.close()


def start_scheduler() -> None:
    """
    Start a background scheduler that runs evaluate_slas() every N minutes.
    """
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        evaluate_slas,
        trigger="interval",
        minutes=settings.SCHEDULER_INTERVAL_MINUTES,
        next_run_time=datetime.now(timezone.utc)
    )
    scheduler.start()
    logger.info(
        "Scheduler started: evaluate_slas every %d minute(s)",
        settings.SCHEDULER_INTERVAL_MINUTES
    )
