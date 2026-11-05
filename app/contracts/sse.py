"""SSE event serialization with request-scoped sequencing."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SseEventFactory:
    request_id: str
    _seq: int = field(default=0, init=False)

    def build(self, event: str, payload: Mapping[str, Any]) -> str:
        self._seq += 1
        data = {"requestId": self.request_id, "seq": self._seq, **payload}
        return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
