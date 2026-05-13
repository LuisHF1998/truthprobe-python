"""
TruthProbe SDK Configuration
"""

import locale
import os
from dataclasses import dataclass, field
from typing import Optional


def _detect_lang() -> str:
    env_lang = os.environ.get("TRUTHPROBE_LANG")
    if env_lang:
        return env_lang[:2].lower()
    try:
        sys_locale = locale.getdefaultlocale()[0] or ""
        if sys_locale.startswith("zh"):
            return "zh"
    except Exception:
        pass
    return "en"


REPORT_ENDPOINT = os.environ.get(
    "TRUTHPROBE_REPORT_URL", "https://truthprobe.com/api/v1/submit-probe"
)


@dataclass
class Config:
    lang: str = field(default_factory=_detect_lang)
    verbose: bool = True
    quiet: bool = False
    report: bool = True
    report_url: str = field(default_factory=lambda: REPORT_ENDPOINT)
    alert_balance_threshold: float = 50.0
    alert_trust_collapse_rate: float = 0.30
    alert_trust_window: int = 20
    first_report_threshold: int = 10
    min_samples_for_audit: int = 10
    currency_symbol: str = "¥"
    providers: list = field(default_factory=list)

    _instance: Optional["Config"] = field(default=None, init=False, repr=False)

    @classmethod
    def get(cls) -> "Config":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def set(cls, **kwargs) -> "Config":
        cfg = cls.get()
        for k, v in kwargs.items():
            if hasattr(cfg, k):
                setattr(cfg, k, v)
        return cfg
