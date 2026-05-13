"""
TruthProbe SDK — Balance Query
Supports multiple relay provider balance API formats.
"""

import urllib.request
import json
from dataclasses import dataclass
from typing import Optional

from .config import Config
from .i18n import t


@dataclass
class BalanceInfo:
    provider_name: str
    balance: Optional[float] = None
    currency: str = "CNY"
    error: Optional[str] = None
    supported: bool = True


# Known relay provider balance endpoint patterns
PROVIDER_PATTERNS = {
    "openai_compatible": {
        "path": "/dashboard/billing/credit_grants",
        "method": "GET",
        "extract": lambda data: data.get("total_available", data.get("balance", None)),
    },
    "new_api": {
        "path": "/api/user/self",
        "method": "GET",
        "extract": lambda data: data.get("data", {}).get("quota", 0) / 500000,
    },
    "one_api": {
        "path": "/api/user/self",
        "method": "GET",
        "extract": lambda data: data.get("data", {}).get("quota", 0) / 500000,
    },
    "close_ai": {
        "path": "/dashboard/billing/subscription",
        "method": "GET",
        "extract": lambda data: data.get("hard_limit_usd", None),
    },
}


def _try_fetch_balance(base_url: str, api_key: str, pattern: dict) -> Optional[float]:
    url = base_url.rstrip("/") + pattern["path"]
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    try:
        req = urllib.request.Request(url, headers=headers, method=pattern["method"])
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return pattern["extract"](data)
    except Exception:
        return None


def query_balance(base_url: str, api_key: str, provider_name: str = "") -> BalanceInfo:
    name = provider_name or base_url.split("//")[-1].split("/")[0]

    for pattern_name, pattern in PROVIDER_PATTERNS.items():
        result = _try_fetch_balance(base_url, api_key, pattern)
        if result is not None:
            return BalanceInfo(
                provider_name=name,
                balance=float(result),
                currency="CNY",
            )

    return BalanceInfo(
        provider_name=name,
        balance=None,
        supported=False,
        error=t("unsupported_provider"),
    )


def query_all_balances() -> list[BalanceInfo]:
    cfg = Config.get()
    results = []
    for provider in cfg.providers:
        info = query_balance(
            base_url=provider.get("base_url", ""),
            api_key=provider.get("key", ""),
            provider_name=provider.get("name", ""),
        )
        results.append(info)
    return results
