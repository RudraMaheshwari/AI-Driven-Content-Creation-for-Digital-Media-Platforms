"""Lightweight trace collector — captures pipeline events alongside each record."""
from __future__ import annotations

import time
from typing import Any


class TraceCollector:
    """Collects a flat list of pipeline events for storage with each content record."""

    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []
        self._stack: list[float] = []

    def start(self, event: str, **payload: Any) -> None:
        self._stack.append(time.perf_counter())
        entry: dict[str, Any] = {"event": f"{event}_start"}
        entry.update(payload)
        self.events.append(entry)

    def end(self, event: str, **payload: Any) -> None:
        started = self._stack.pop() if self._stack else time.perf_counter()
        duration_ms = int((time.perf_counter() - started) * 1000)
        entry: dict[str, Any] = {"event": f"{event}_end", "duration_ms": duration_ms}
        entry.update(payload)
        self.events.append(entry)

    def note(self, event: str, **payload: Any) -> None:
        entry: dict[str, Any] = {"event": event}
        entry.update(payload)
        self.events.append(entry)

    def snapshot(self) -> dict[str, Any]:
        return {"events": list(self.events)}
