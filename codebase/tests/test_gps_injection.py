"""
test_gps_injection.py — Unit + endpoint tests cho bug fix GPS injection.

BUG:  /chat endpoint nhận lat/lng từ frontend nhưng không inject vào messages.
      LLM gọi tool mà không có lat/lng → tool fallback sang IP (sai vị trí).
FIX:  inject_gps() append [GPS] note vào system message trước khi gọi LLM.

Chạy: python -m pytest tests/test_gps_injection.py -v
"""

import sys
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.stdout.reconfigure(encoding="utf-8")

from main import inject_gps  # pure function — không cần mock


# ══════════════════════════════════════════════════════════════════
# PHẦN 1 — Unit tests cho inject_gps (không cần mock, không cần FastAPI)
# ══════════════════════════════════════════════════════════════════

NHA_TRANG = (12.2451, 109.1943)
SYSTEM_MSG = {"role": "system", "content": "Bạn là AI Local Guide."}
USER_MSG   = {"role": "user",   "content": "Tìm quán ăn gần đây"}


class TestInjectGpsNoCoords:

    def test_both_none_returns_same_list(self):
        """
        Đầu vào : lat=None, lng=None
        Mong đợi: trả về đúng list gốc, không thay đổi gì
        """
        msgs = [SYSTEM_MSG, USER_MSG]
        result = inject_gps(msgs, None, None)
        assert result == msgs

    def test_only_lat_no_inject(self):
        """
        Đầu vào : lat có giá trị nhưng lng=None
        Mong đợi: không inject (cần cả hai)
        """
        result = inject_gps([SYSTEM_MSG], 12.2451, None)
        assert "[GPS]" not in result[0]["content"]

    def test_only_lng_no_inject(self):
        """
        Đầu vào : lng có giá trị nhưng lat=None
        Mong đợi: không inject
        """
        result = inject_gps([SYSTEM_MSG], None, 109.1943)
        assert "[GPS]" not in result[0]["content"]


class TestInjectGpsWithExistingSystemMessage:

    def test_gps_appended_to_system_message(self):
        """
        Đầu vào : messages có system message, lat=12.2451, lng=109.1943
        Mong đợi: '[GPS]' được append vào cuối content của system message
        """
        lat, lng = NHA_TRANG
        result = inject_gps([SYSTEM_MSG, USER_MSG], lat, lng)

        sys_content = result[0]["content"]
        print(f"\n  system content:\n{sys_content}")

        assert "[GPS]" in sys_content
        assert str(lat) in sys_content
        assert str(lng) in sys_content
        assert sys_content.startswith("Bạn là AI Local Guide.")  # nội dung gốc còn nguyên

    def test_gps_note_contains_instruction(self):
        """
        Mong đợi: note chỉ rõ 'LUÔN truyền lat/lng' để LLM biết phải dùng
        """
        lat, lng = NHA_TRANG
        result = inject_gps([SYSTEM_MSG], lat, lng)
        assert "LUÔN truyền" in result[0]["content"]
        assert "search_nearby_restaurants" in result[0]["content"]

    def test_message_count_unchanged(self):
        """
        Mong đợi: inject không thêm/xóa message nào
        """
        msgs = [SYSTEM_MSG, USER_MSG]
        result = inject_gps(msgs, *NHA_TRANG)
        assert len(result) == 2

    def test_user_message_untouched(self):
        """
        Mong đợi: các message không phải system không bị ảnh hưởng
        """
        result = inject_gps([SYSTEM_MSG, USER_MSG], *NHA_TRANG)
        assert result[1] == USER_MSG

    def test_finds_system_message_by_role(self):
        """
        Đầu vào : system message không ở vị trí đầu tiên
        Mong đợi: vẫn tìm đúng và inject vào system message đó
        """
        msgs = [
            {"role": "user",      "content": "Hi"},
            {"role": "system",    "content": "System here"},
            {"role": "assistant", "content": "Hello"},
        ]
        result = inject_gps(msgs, *NHA_TRANG)
        assert "[GPS]" in result[1]["content"]  # index 1 vẫn là system
        assert "[GPS]" not in result[0]["content"]
        assert "[GPS]" not in result[2]["content"]


class TestInjectGpsNoSystemMessage:

    def test_creates_system_message_at_index_0(self):
        """
        Đầu vào : messages không có system message
        Mong đợi: system message mới được tạo và chèn vào index 0
        """
        msgs = [USER_MSG]
        result = inject_gps(msgs, *NHA_TRANG, fallback_system="Fallback prompt.")

        print(f"\n  result[0]: {result[0]}")
        assert result[0]["role"] == "system"
        assert "[GPS]" in result[0]["content"]
        assert "Fallback prompt." in result[0]["content"]

    def test_original_messages_shifted_to_back(self):
        """
        Mong đợi: user message gốc vẫn còn, bị dịch sang index 1
        """
        msgs = [USER_MSG]
        result = inject_gps(msgs, *NHA_TRANG, fallback_system="")
        assert len(result) == 2
        assert result[1] == USER_MSG

    def test_empty_messages_creates_system(self):
        """
        Đầu vào : list rỗng
        Mong đợi: chỉ có 1 system message sau inject
        """
        result = inject_gps([], *NHA_TRANG, fallback_system="Base.")
        assert len(result) == 1
        assert result[0]["role"] == "system"


class TestInjectGpsImmutability:

    def test_does_not_mutate_input_list(self):
        """
        Mong đợi: list gốc không bị thay đổi (phòng side-effect)
        """
        original = [SYSTEM_MSG.copy(), USER_MSG.copy()]
        original_copy = [m.copy() for m in original]
        inject_gps(original, *NHA_TRANG)
        assert original == original_copy

    def test_does_not_mutate_system_message_dict(self):
        """
        Mong đợi: dict của system message gốc không bị mutate
        """
        sys_msg = {"role": "system", "content": "Original content"}
        original_content = sys_msg["content"]
        inject_gps([sys_msg], *NHA_TRANG)
        assert sys_msg["content"] == original_content  # gốc không đổi


class TestInjectGpsValues:

    def test_different_coordinates_reflected_correctly(self):
        """
        Đầu vào : Hà Nội (21.0285, 105.8542)
        Mong đợi: note chứa đúng tọa độ Hà Nội, không phải Nha Trang
        """
        lat, lng = 21.0285, 105.8542
        result = inject_gps([SYSTEM_MSG], lat, lng)
        content = result[0]["content"]
        assert "21.0285" in content
        assert "105.8542" in content
        assert "12.2451" not in content  # không lẫn tọa độ khác

    def test_float_precision_preserved(self):
        """
        Đầu vào : tọa độ có nhiều chữ số thập phân
        Mong đợi: giá trị được giữ nguyên chính xác
        """
        lat, lng = 10.82199, 106.62571
        result = inject_gps([SYSTEM_MSG], lat, lng)
        content = result[0]["content"]
        assert str(lat) in content
        assert str(lng) in content


# ══════════════════════════════════════════════════════════════════
# PHẦN 2 — Endpoint tests qua FastAPI TestClient
# ══════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def client():
    """
    TestClient với run_model_tool_loop bị mock.
    Dùng để kiểm tra /chat endpoint inject GPS đúng vào messages.
    """
    from fastapi.testclient import TestClient
    from main import app

    fake_result = {
        "status": "answered",
        "assistant_text": "Đây là gợi ý quán ăn.",
        "rounds": [],
        "tool_events": [],
    }

    with patch("main.run_model_tool_loop", return_value=fake_result) as mock_loop:
        with TestClient(app) as c:
            c._mock_loop = mock_loop
            yield c


class TestChatEndpointGpsInjection:

    def _post(self, client, lat=None, lng=None, messages=None):
        if messages is None:
            messages = [{"role": "system", "content": "You are a guide."},
                        {"role": "user", "content": "Tìm quán ăn"}]
        return client.post("/chat", json={"messages": messages, "lat": lat, "lng": lng})

    def test_with_gps_injects_into_system_message(self, client):
        """
        Đầu vào : POST /chat { lat=12.2451, lng=109.1943, messages=[system, user] }
        Mong đợi: run_model_tool_loop nhận messages trong đó system message có '[GPS]'
        """
        self._post(client, lat=12.2451, lng=109.1943)

        called_messages = client._mock_loop.call_args.kwargs["messages"]
        sys_content = next(m["content"] for m in called_messages if m["role"] == "system")

        print(f"\n  system content passed to LLM:\n{sys_content[-200:]}")
        assert "[GPS]" in sys_content
        assert "12.2451" in sys_content
        assert "109.1943" in sys_content

    def test_without_gps_no_injection(self, client):
        """
        Đầu vào : POST /chat không có lat/lng
        Mong đợi: system message KHÔNG chứa '[GPS]'
        """
        self._post(client, lat=None, lng=None)

        called_messages = client._mock_loop.call_args.kwargs["messages"]
        sys_content = next(
            (m["content"] for m in called_messages if m["role"] == "system"), ""
        )
        assert "[GPS]" not in sys_content

    def test_endpoint_returns_llm_response(self, client):
        """
        Mong đợi: /chat trả về đúng kết quả từ run_model_tool_loop
        """
        resp = self._post(client, lat=12.2451, lng=109.1943)
        assert resp.status_code == 200
        assert resp.json()["assistant_text"] == "Đây là gợi ý quán ăn."

    def test_gps_injected_once_not_duplicated(self, client):
        """
        Mong đợi: gọi endpoint 2 lần không tạo ra '[GPS]' trùng nhau trong 1 request
        """
        self._post(client, lat=10.0, lng=106.0)
        called_messages = client._mock_loop.call_args.kwargs["messages"]
        sys_content = next(m["content"] for m in called_messages if m["role"] == "system")
        assert sys_content.count("[GPS]") == 1
