import logging, json
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler("app.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("foodai")

def log_request(mcq: dict, lat: float, lng: float):
    logger.info(f"REQUEST | lat={lat} lng={lng} | mcq={json.dumps(mcq, ensure_ascii=False)}")

def log_places_result(count: int, radius: int):
    logger.info(f"PLACES | found={count} quán | radius={radius}m")

def log_ai_response(recommendations: list, warning: str | None):
    logger.info(f"AI_RESP | recs={len(recommendations)} | warning={warning}")

def log_error(stage: str, error: str):
    logger.error(f"ERROR | stage={stage} | {error}")
