import logging
import os

import requests

logger = logging.getLogger("snaprecommend.notifications")

MATTERMOST_WEBHOOK_ENV = "FLASK_MATTERMOST_WEBHOOK_URL"


def notify_mattermost(message: str) -> bool:
    """
    Post a message to the configured Mattermost webhook.
    Returns True on success, False if the webhook is not configured or the
    request fails. Never raises — callers should not be blocked by a
    notification failure.
    """
    webhook_url = os.environ.get(MATTERMOST_WEBHOOK_ENV)
    if not webhook_url:
        logger.warning(
            "Mattermost webhook not configured (%s). "
            "Notification not sent: %s",
            MATTERMOST_WEBHOOK_ENV,
            message,
        )
        return False

    try:
        response = requests.post(
            webhook_url,
            json={"text": message},
            timeout=10,
        )
        response.raise_for_status()
        return True
    except Exception as exc:
        logger.error("Failed to send Mattermost notification: %s", exc)
        return False
