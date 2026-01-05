import logging
from logging.handlers import RotatingFileHandler
import os

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
log_file = os.path.join(LOG_DIR, "actions.log")

logger = logging.getLogger("valutatrade_hub")
logger.setLevel(logging.INFO)

formatter = logging.Formatter(
    "%(asctime)s %(levelname)s %(message)s", "%Y-%m-%dT%H:%M:%S"
)

handler = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=3)
handler.setFormatter(formatter)
logger.addHandler(handler)
