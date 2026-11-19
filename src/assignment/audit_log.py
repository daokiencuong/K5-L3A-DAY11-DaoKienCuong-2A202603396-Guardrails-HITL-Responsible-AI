"""
Assignment 11 — interaction audit log.

Records every interaction for forensics. Never blocks by itself —
other layers catch attacks; this layer makes them reviewable.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import time


def default_audit_log_path() -> str:
    """Always resolve to <repo>/outputs/… (safe when cwd is src/)."""
    repo_root = Path(__file__).resolve().parents[2]
    return str(repo_root / "outputs" / "audit_log.json")


class AuditLogPlugin:
    """Framework-agnostic audit logger (wire into ADK callbacks or your pipeline)."""

    def __init__(self):
        self.name = "audit_log"
        self.logs: list[dict] = []
        self._open: dict[str, dict] = {}

    def record_input(self, *, user_id: str, text: str, request_id: str | None = None):
        """Record an input and return the key to pass to ``record_output``."""
        key = request_id or user_id
        started_at = utc_now_iso()
        started_monotonic = time.perf_counter()
        row = {
            "request_id": request_id,
            "user_id": user_id,
            "input": text,
            "started_at": started_at,
            "output": None,
            "blocked": None,
            "layer": None,
            "latency_ms": None,
            "completed_at": None,
        }
        self.logs.append(row)
        self._open[key] = {
            "index": len(self.logs) - 1,
            "started_monotonic": started_monotonic,
        }
        return key

    def record_output(
        self,
        *,
        user_id: str,
        text: str,
        blocked: bool = False,
        layer: str | None = None,
        request_id: str | None = None,
    ):
        """Attach the outcome to its input record, including elapsed time."""
        key = request_id or user_id
        opened = self._open.pop(key, None)
        completed_at = utc_now_iso()

        if opened is None:
            row = {
                "request_id": request_id,
                "user_id": user_id,
                "input": None,
                "started_at": None,
                "output": text,
                "blocked": bool(blocked),
                "layer": layer,
                "latency_ms": None,
                "completed_at": completed_at,
            }
            self.logs.append(row)
            return

        row = self.logs[opened["index"]]
        row.update(
            {
                "output": text,
                "blocked": bool(blocked),
                "layer": layer,
                "latency_ms": round(
                    (time.perf_counter() - opened["started_monotonic"]) * 1000, 3
                ),
                "completed_at": completed_at,
            }
        )

    def export_json(self, filepath: str | None = None):
        """Write logs to disk (JSON array) under repo-root ``outputs/`` by default."""
        path = Path(filepath or default_audit_log_path())
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.logs, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return path


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
