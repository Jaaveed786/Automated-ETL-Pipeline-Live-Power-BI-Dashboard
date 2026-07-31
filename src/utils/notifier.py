import os
import json
import requests
from src.utils.logger import setup_logger

logger = setup_logger("slack_notifier")

def send_failure_alert(pipeline_name: str, error_message: str) -> bool:
    """
    Sends a HTTP Webhook notification to Slack / Discord on pipeline exception.
    """
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url or webhook_url.startswith("https://hooks.slack.com/services/YOUR"):
        logger.info("SLACK_WEBHOOK_URL not configured. Skipping webhook alert.")
        return False

    payload = {
        "text": f"🚨 *ETL Pipeline Failure Alert*\n*Pipeline:* `{pipeline_name}`\n*Error Details:* ```{error_message}```"
    }

    try:
        response = requests.post(
            webhook_url,
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        if response.status_code == 200:
            logger.info("Failure alert successfully posted to Slack/Discord webhook.")
            return True
        else:
            logger.warning(f"Failed to post webhook alert. HTTP {response.status_code}: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Exception while sending failure alert: {e}")
        return False
