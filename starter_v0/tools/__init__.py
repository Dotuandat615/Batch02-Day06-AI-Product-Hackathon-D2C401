from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

# Folder names match the tool names in artifacts/tools.yaml and data/eval_base.json.
# If a team renames a tool, it MUST stay in sync across ALL of:
#   artifacts/tools.yaml  ->  this dict  ->  data/eval_base.json
from .clarify.tool import ask_user
from .search_nearby.tool import search_nearby_places
from .get_reviews.tool import get_place_reviews
from .format_recommendations.tool import format_recs


TOOL_FUNCTIONS = {
    "clarify": ask_user,
    "search_nearby": search_nearby_places,
    "get_reviews": get_place_reviews,
    "format_recommendations": format_recs,
}


def load_tool_declarations(path: Path) -> list[dict[str, Any]]:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))["tools"]


def to_openai_tools(declarations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{
        "type": "function",
        "function": {
            "name": item["name"],
            "description": item.get("description", ""),
            "parameters": item.get("parameters", {"type": "object", "properties": {}}),
        },
    } for item in declarations]
