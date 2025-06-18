import logging
from typing import Any, Dict, List, Optional

import httpx

from src.settings import SLACK_WEBHOOK_URL, SLACK_TIMEOUT

logger = logging.getLogger(__name__)


def send_slack_notification(
        text: str,
        attachments: Optional[List[Dict[str, Any]]] = None,
        blocks: Optional[List[Dict[str, Any]]] = None,
) -> None:
    """
    Send a message to Slack via incoming webhook.

    :param text: The main text of the Slack message.
    :param attachments: Optional list of Slack-style attachment dicts.
    :param blocks: Optional list of Slack-style block dicts.
    """
    if not SLACK_WEBHOOK_URL:
        logger.warning("SLACK_WEBHOOK_URL is not set; skipping Slack notification.")
        return

    payload: Dict[str, Any] = {"text": text}
    if attachments:
        payload["attachments"] = attachments
    if blocks:
        payload["blocks"] = blocks

    try:
        response = httpx.post(
            SLACK_WEBHOOK_URL,
            json=payload,
            timeout=SLACK_TIMEOUT,
        )
        response.raise_for_status()
        logger.info("Slack notification sent successfully")
    except Exception as exc:
        logger.error(f"Failed to send Slack notification: {exc}")
