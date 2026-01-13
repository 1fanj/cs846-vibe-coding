import logging
from pythonjsonlogger import jsonlogger
import os

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

logger = logging.getLogger("vibe")
logger.setLevel(logging.INFO)

# JSON handler
json_handler = logging.FileHandler(os.path.join(LOG_DIR, "app.log.json"))
json_formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s')
json_handler.setFormatter(json_formatter)

# Markdown handler: simple text to a .md file
md_handler = logging.FileHandler(os.path.join(LOG_DIR, "app.log.md"))
md_handler.setFormatter(logging.Formatter('### %(levelname)s - %(asctime)s\n- logger: %(name)s\n- msg: %(message)s\n'))

# Console handler for convenience
console = logging.StreamHandler()
console.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))

logger.addHandler(json_handler)
logger.addHandler(md_handler)
logger.addHandler(console)

def get_logger():
    return logger
