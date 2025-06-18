import asyncio
import logging
from datetime import timezone
from typing import Dict, Any

import requests

from src import crud, models, settings
from src.database import SessionLocal
from src.ws import manager

logger = logging.getLogger(__name__)


def send_slack_notification(ticket: models.Ticket, alert: models.Alert) -> None:
    """
    Send a structured Slack message for the given alert.
    """
    if not settings.SLACK_WEBHOOK_URL:
        logger.warning("SLACK_WEBHOOK_URL not set; skipping Slack notification.")
        return

    payload = {
        "text": f"SLA {alert.state.value.upper()} for Ticket {ticket.id}",
        "attachments": [
            {
                "color": "#ff0000" if alert.state == models.SLAState.BREACH else "#ffa500",
                "fields": [
                    {
                        "title": "Ticket ID",
                        "value": ticket.id,
                        "short": True
                    }, {
                        "title": "Priority",
                        "value": ticket.priority,
                        "short": True
                    }, {
                        "title": "Customer Tier",
                        "value": ticket.customer_tier,
                        "short": True
                    }, {
                        "title": "SLA Type",
                        "value": alert.sla_type,
                        "short": True
                    }, {
                        "title": "State",
                        "value": alert.state.value,
                        "short": True
                    }, {
                        "title": "Escalation Lv.",
                        "value": ticket.escalation_level,
                        "short": True
                    }, {
                        "title": "Elapsed (min)",
                        "value": f"{alert.details.get('elapsed_minutes'):.1f}",
                        "short": True
                    }, {
                        "title": "Target (min)",
                        "value": alert.details.get("target_minutes"),
                        "short": True
                    }, {
                        "title": "Details",
                        "value": str(alert.details),
                        "short": False
                    }, {
                        "title": "Timestamp",
                        "value": alert.created_at.astimezone(timezone.utc).isoformat(),
                        "short": False
                    },
                ],
            }
        ],
    }

    try:
        response = requests.post(
            settings.SLACK_WEBHOOK_URL,
            json=payload,
            timeout=settings.SLACK_TIMEOUT,
        )
        response.raise_for_status()
        logger.info(f"Slack notification sent for alert id={alert.id}")
    except Exception as exc:
        logger.error(f"Failed to send Slack notification: {exc}")


def process_alert(
        ticket_id: str,
        sla_type: str,
        state: models.SLAState,
        details: Dict[str, Any]
) -> None:
    """
    Persist a new alert, increment escalation level, notify Slack,
    and broadcast over WebSocket.
    """
    db = SessionLocal()
    try:
        alert = crud.create_alert(db, ticket_id, sla_type, state, details)
        ticket = crud.get_ticket(db, ticket_id)

        send_slack_notification(ticket, alert)

        message = {
            "ticket_id": ticket.id,
            "sla_type": alert.sla_type,
            "state": alert.state.value,
            "details": alert.details,
            "timestamp": alert.created_at.astimezone(timezone.utc).isoformat(),
        }
        # schedule broadcast without blocking
        asyncio.create_task(manager.broadcast(message))

    except Exception:
        db.rollback()
        logger.exception(f"Error processing alert for ticket {ticket_id}")
    finally:
        db.close()
