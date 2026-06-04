"""
conftest.py — Mock các module nặng TRƯỚC khi test import main.py.
Nếu không làm điều này, make_provider("openai") sẽ chạy ngay lúc import
và yêu cầu API key thật.
"""

import sys
from unittest.mock import MagicMock

# ── Mock providers ──────────────────────────────────────────────────────────
_provider_inst = MagicMock()
_provider_inst.default_model = "gpt-4o-mini"

_providers_mod = MagicMock()
_providers_mod.make_provider.return_value = _provider_inst

for _name in ["providers", "providers.base", "providers.anthropic_provider",
              "providers.openai_provider", "providers.gemini_provider",
              "providers.openrouter_provider"]:
    sys.modules.setdefault(_name, MagicMock())
sys.modules["providers"] = _providers_mod

# ── Mock logger (không cần ghi file trong test) ─────────────────────────────
sys.modules.setdefault("logger", MagicMock())

# ── Mock versioning ─────────────────────────────────────────────────────────
sys.modules.setdefault("versioning", MagicMock())
