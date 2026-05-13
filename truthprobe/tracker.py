"""
TruthProbe SDK — Request Tracker
Stores local request history for reporting and alerts.
"""

import json
import os
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

from .audit import AuditResult


def _data_dir() -> Path:
    d = Path.home() / ".truthprobe"
    d.mkdir(exist_ok=True)
    return d


@dataclass
class RequestRecord:
    timestamp: float
    model: str
    cost: float
    trust_score: int
    is_suspicious: bool
    response_time_ms: float
    flags: list = field(default_factory=list)


class Tracker:
    def __init__(self):
        self._records: list[RequestRecord] = []
        self._session_start = time.time()
        self._total_cost_session = 0.0
        self._suspicious_count_session = 0
        self._first_report_shown = False
        self._load_state()

    def _state_file(self) -> Path:
        return _data_dir() / "state.json"

    def _history_file(self) -> Path:
        return _data_dir() / "history.jsonl"

    def _load_state(self):
        sf = self._state_file()
        if sf.exists():
            try:
                state = json.loads(sf.read_text())
                self._first_report_shown = state.get("first_report_shown", False)
            except Exception:
                pass

    def _save_state(self):
        sf = self._state_file()
        state = {"first_report_shown": self._first_report_shown}
        sf.write_text(json.dumps(state))

    def add(self, record: RequestRecord):
        self._records.append(record)
        self._total_cost_session += record.cost
        if record.is_suspicious:
            self._suspicious_count_session += 1

        with open(self._history_file(), "a") as f:
            f.write(json.dumps(asdict(record)) + "\n")

    @property
    def session_count(self) -> int:
        return len(self._records)

    @property
    def total_count(self) -> int:
        hf = self._history_file()
        if not hf.exists():
            return 0
        try:
            with open(hf) as f:
                return sum(1 for _ in f)
        except Exception:
            return 0

    @property
    def session_cost(self) -> float:
        return self._total_cost_session

    @property
    def session_suspicious(self) -> int:
        return self._suspicious_count_session

    def recent_suspicious_rate(self, window: int = 20) -> float:
        recent = self._records[-window:]
        if not recent:
            return 0.0
        return sum(1 for r in recent if r.is_suspicious) / len(recent)

    def should_show_first_report(self, threshold: int = 10) -> bool:
        if self._first_report_shown:
            return False
        return self.total_count >= threshold

    def mark_first_report_shown(self):
        self._first_report_shown = True
        self._save_state()

    def get_today_records(self) -> list[RequestRecord]:
        today_start = time.time() - (time.time() % 86400)
        return [r for r in self._records if r.timestamp >= today_start]

    def get_all_history(self, limit: int = 500) -> list[dict]:
        hf = self._history_file()
        if not hf.exists():
            return []
        records = []
        try:
            with open(hf) as f:
                for line in f:
                    if line.strip():
                        records.append(json.loads(line))
        except Exception:
            pass
        return records[-limit:]

    def get_model_distribution(self) -> dict[str, int]:
        dist: dict[str, int] = {}
        for r in self._records:
            dist[r.model] = dist.get(r.model, 0) + 1
        return dist

    def get_avg_trust_score(self) -> float:
        if not self._records:
            return 100.0
        return sum(r.trust_score for r in self._records) / len(self._records)


_tracker: Optional[Tracker] = None


def get_tracker() -> Tracker:
    global _tracker
    if _tracker is None:
        _tracker = Tracker()
    return _tracker
