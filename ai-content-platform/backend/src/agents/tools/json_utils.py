"""Gemini sometimes wraps JSON in ```json fences or prose — this pulls out the
first JSON object reliably."""
from __future__ import annotations

import json
import re
from typing import Any


def extract_json(text: str) -> dict[str, Any]:
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
    if fenced:
        return json.loads(fenced.group(1))
    brace = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if brace:
        return json.loads(brace.group(0))
    raise ValueError(f"no JSON object found in model output: {text!r}")
