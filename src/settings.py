from prettyconf import config
from unipath import Path

PROJECT_DIR = Path(__file__).ancestor(2)

# Logging
LOG_LEVEL = config("LOG_LEVEL", default="INFO")

# Database
default_db_url = 'sqlite:///{}/db.sqlite3'.format(PROJECT_DIR)
DATABASE_URL = config("DATABASE_URL", default=default_db_url)

# Slack
SLACK_WEBHOOK_URL = config("SLACK_WEBHOOK_URL", default="")
SLACK_TIMEOUT = config("SLACK_TIMEOUT", cast=int, default=5)

# SLA configuration
SLA_CONFIG_PATH = config("SLA_CONFIG_PATH", default="sla_config.yaml")
ALERT_THRESHOLD = config("ALERT_THRESHOLD", default=0.85, cast=float)  # when 85% of SLA time has elapsed → ALERT
BREACH_THRESHOLD = config("BREACH_THRESHOLD", default=1.00, cast=float)  # when 100% of SLA time has elapsed → BREACH

# Scheduler
SCHEDULER_INTERVAL_MINUTES = config(
    "SCHEDULER_INTERVAL_MINUTES",
    cast=int,
    default=1
)

# FastAPI settings
API_HOST = config("API_HOST", default="0.0.0.0")
API_PORT = config("API_PORT", cast=int, default=8000)
