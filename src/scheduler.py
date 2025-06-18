import logging
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler

from src import models, settings
from src.alerts import process_alert
from src.config import get_sla_config
from src.database import SessionLocal

logger = logging.getLogger(__name__)

db = SessionLocal()


def evaluate_slas() -> None:
    """
    Scan all tickets and generate an ALERT per ticket/SLA type
    by calling process_alert(), using whatever config.get_sla_config() returns.
    """
    try:
        sla_config = get_sla_config()  # dynamic lookup
        now = datetime.now(timezone.utc)

        tickets = db.query(models.Ticket).all()

        for ticket in tickets:
            created = ticket.created_at
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            elapsed_minutes = (now - created).total_seconds() / 60

            for sla_type in ("response", "resolution"):
                try:
                    target = sla_config[ticket.customer_tier][ticket.priority][sla_type]
                except KeyError:
                    logger.warning(
                        "No SLA config for %s/%s/%s",
                        ticket.customer_tier,
                        ticket.priority,
                        sla_type
                    )
                    continue

                percent_used = elapsed_minutes / target
                if percent_used < settings.ALERT_THRESHOLD:
                    continue

                # Always emit an ALERT
                state = models.SLAState.ALERT
                details = {
                    "elapsed_minutes": elapsed_minutes,
                    "target_minutes": target,
                    "percent_used": percent_used,
                }

                # Single call: persist + notify + broadcast
                process_alert(ticket.id, sla_type, state, details)

    except Exception:
        logger.exception("Error during SLA evaluation")
    finally:
        db.close()


def evaluate_slas_for_ticket(ticket_id: str) -> None:
    """
    Compute SLA usage for one ticket and call process_alert()
    if the ALERT threshold is breached.
    """
    try:
        sla_conf = get_sla_config()
        ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).one()
        now = datetime.now(timezone.utc)
        elapsed = (now - ticket.created_at).total_seconds() / 60
        target = sla_conf[ticket.customer_tier][ticket.priority]["response"]
        if elapsed / target >= settings.ALERT_THRESHOLD:
            process_alert(ticket.id, "response", models.SLAState.ALERT,
                          {"elapsed_minutes": elapsed, "target_minutes": target})
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
