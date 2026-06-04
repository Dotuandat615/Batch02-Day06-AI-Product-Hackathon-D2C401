import logging
import json
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler("app.log", encoding="utf-8"),
        logging.StreamHandler()  # cũng in ra console
    ]
)
logger = logging.getLogger("foodai")

def log_request(mcq: dict, lat: float, lng: float):
    logger.info(f"[1] REQUEST | lat={lat} lng={lng} | mcq={json.dumps(mcq, ensure_ascii=False)}")

def log_places_result(count: int, radius: int):
    logger.info(f"[2] PLACES | found={count} quán | radius={radius}m")

def log_ai_response(recommendations: list, warning: str | None):
    logger.info(f"[3] AI_RESP | recs={len(recommendations)} | warning={warning}")

def log_error(stage: str, error: str):
    logger.error(f"ERROR | stage={stage} | {error}")

def log_agent_metrics(latency_ms: int, prompt_tokens: int, completion_tokens: int, model: str, parsing_success: bool):
    """
    Theo dõi hiệu suất của AI (Agent Observability):
    - latency_ms: Đánh giá tốc độ phản hồi (có đủ nhanh cho UX không)
    - tokens: Đánh giá chi phí (Cost/Request)
    - model: Version model đang dùng
    - parsing_success: Đánh giá LLM có tuân thủ format JSON không, hay bị rác
    """
    logger.info(
        f"[4] AGENT_METRICS | model={model} | latency={latency_ms}ms | "
        f"tokens={prompt_tokens}+{completion_tokens}={prompt_tokens+completion_tokens} | "
        f"json_parse={'SUCCESS' if parsing_success else 'FAILED'}"
    )
