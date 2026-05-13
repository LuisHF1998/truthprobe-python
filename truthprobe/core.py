"""
TruthProbe SDK — Core (patch, init, report, balance, score)
"""

import time
import functools
from typing import Optional

from .config import Config
from .audit import run_audit
from .tracker import get_tracker, RequestRecord
from .balance import query_all_balances, query_balance
from .display import (
    print_request_line,
    print_balance_alert,
    print_trust_collapse,
    prompt_first_report,
    print_full_report,
)
from .i18n import t


_patched = False


def init(
    providers: Optional[list] = None,
    lang: Optional[str] = None,
    verbose: bool = True,
    quiet: bool = False,
    alert_balance_threshold: float = 50.0,
    currency_symbol: str = "¥",
    **kwargs,
):
    cfg = Config.get()
    if providers:
        cfg.providers = providers
    if lang:
        cfg.lang = lang
    cfg.verbose = verbose
    cfg.quiet = quiet
    cfg.alert_balance_threshold = alert_balance_threshold
    cfg.currency_symbol = currency_symbol
    for k, v in kwargs.items():
        if hasattr(cfg, k):
            setattr(cfg, k, v)


def patch(verbose: Optional[bool] = None, quiet: Optional[bool] = None, lang: Optional[str] = None):
    global _patched
    if _patched:
        return

    cfg = Config.get()
    if verbose is not None:
        cfg.verbose = verbose
    if quiet is not None:
        cfg.quiet = quiet
    if lang is not None:
        cfg.lang = lang

    _patch_openai()
    _patched = True


def _patch_openai():
    try:
        from openai import OpenAI
        from openai.resources.chat import completions as chat_mod
    except ImportError:
        return

    original_create = chat_mod.Completions.create

    @functools.wraps(original_create)
    def patched_create(self, *args, **kwargs):
        model = kwargs.get("model", "unknown")
        stream = kwargs.get("stream", False)

        start_time = time.time()
        ttfb = 0.0

        if stream:
            return _handle_stream(original_create, self, args, kwargs, model, start_time)
        else:
            response = original_create(self, *args, **kwargs)
            total_ms = (time.time() - start_time) * 1000
            _process_response(model, response, ttfb_ms=0, total_ms=total_ms)
            return response

    chat_mod.Completions.create = patched_create

    # Also patch async if available
    try:
        from openai.resources.chat import completions as async_chat_mod
        if hasattr(async_chat_mod, "AsyncCompletions"):
            original_async_create = async_chat_mod.AsyncCompletions.create

            @functools.wraps(original_async_create)
            async def patched_async_create(self, *args, **kwargs):
                model = kwargs.get("model", "unknown")
                stream = kwargs.get("stream", False)
                start_time = time.time()

                if stream:
                    return await _handle_async_stream(original_async_create, self, args, kwargs, model, start_time)
                else:
                    response = await original_async_create(self, *args, **kwargs)
                    total_ms = (time.time() - start_time) * 1000
                    _process_response(model, response, ttfb_ms=0, total_ms=total_ms)
                    return response

            async_chat_mod.AsyncCompletions.create = patched_async_create
    except (ImportError, AttributeError):
        pass


def _handle_stream(original_create, self, args, kwargs, model, start_time):
    response_chunks = []
    ttfb = 0.0
    first_chunk = True

    original_stream = original_create(self, *args, **kwargs)

    class AuditedStream:
        def __init__(self, stream):
            self._stream = stream
            self._chunks = []
            self._first = True
            self._finalized = False

        def __iter__(self):
            return self

        def __next__(self):
            nonlocal ttfb, first_chunk
            try:
                chunk = next(self._stream)
            except StopIteration:
                self._finalize()
                raise
            if first_chunk:
                ttfb = (time.time() - start_time) * 1000
                first_chunk = False
            self._chunks.append(chunk)
            return chunk

        def _finalize(self):
            if not self._finalized:
                self._finalized = True
                total_ms = (time.time() - start_time) * 1000
                text = _extract_stream_text(self._chunks)
                total_tokens = _estimate_tokens(text)
                returned_model = _extract_stream_model(self._chunks)
                _process_audit(model, text, returned_model, ttfb, total_ms, total_tokens)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self._finalize()
            if hasattr(self._stream, '__exit__'):
                self._stream.__exit__(*args)

    return AuditedStream(original_stream)


async def _handle_async_stream(original_create, self, args, kwargs, model, start_time):
    ttfb = 0.0
    first_chunk = True
    chunks = []

    original_stream = await original_create(self, *args, **kwargs)

    class AsyncAuditedStream:
        def __init__(self, stream):
            self._stream = stream

        def __aiter__(self):
            return self

        async def __anext__(self):
            nonlocal ttfb, first_chunk
            chunk = await self._stream.__anext__()
            if first_chunk:
                ttfb = (time.time() - start_time) * 1000
                first_chunk = False
            chunks.append(chunk)
            return chunk

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            total_ms = (time.time() - start_time) * 1000
            text = _extract_stream_text(chunks)
            total_tokens = _estimate_tokens(text)
            returned_model = _extract_stream_model(chunks)
            _process_audit(model, text, returned_model, ttfb, total_ms, total_tokens)

    return AsyncAuditedStream(original_stream)


def _extract_stream_text(chunks) -> str:
    text_parts = []
    for chunk in chunks:
        if hasattr(chunk, "choices") and chunk.choices:
            delta = chunk.choices[0].delta
            if hasattr(delta, "content") and delta.content:
                text_parts.append(delta.content)
    return "".join(text_parts)


def _extract_stream_model(chunks) -> str:
    for chunk in chunks:
        if hasattr(chunk, "model") and chunk.model:
            return chunk.model
    return ""


def _process_response(model: str, response, ttfb_ms: float, total_ms: float):
    text = ""
    returned_model = ""
    total_tokens = 0

    if hasattr(response, "choices") and response.choices:
        msg = response.choices[0].message
        if hasattr(msg, "content") and msg.content:
            text = msg.content
    if hasattr(response, "model"):
        returned_model = response.model
    if hasattr(response, "usage") and response.usage:
        total_tokens = response.usage.total_tokens

    _process_audit(model, text, returned_model, ttfb_ms, total_ms, total_tokens)


def _process_audit(
    model: str,
    text: str,
    returned_model: str,
    ttfb_ms: float,
    total_ms: float,
    total_tokens: int,
):
    cfg = Config.get()
    tracker = get_tracker()

    audit_result = run_audit(
        claimed_model=model,
        response_text=text,
        returned_model=returned_model,
        ttfb_ms=ttfb_ms,
        total_ms=total_ms,
        total_tokens=total_tokens,
    )

    cost = _estimate_cost(model, total_tokens or _estimate_tokens(text))

    record = RequestRecord(
        timestamp=time.time(),
        model=model,
        cost=cost,
        trust_score=audit_result.trust_score,
        is_suspicious=audit_result.is_suspicious,
        response_time_ms=total_ms,
        flags=audit_result.flags,
    )
    tracker.add(record)

    if cfg.verbose and not cfg.quiet:
        print_request_line(record)

    _check_alerts(tracker, cfg)


def _check_alerts(tracker, cfg: Config):
    if tracker.should_show_first_report(cfg.first_report_threshold):
        show = prompt_first_report()
        tracker.mark_first_report_shown()
        if show:
            print_full_report()

    window = cfg.alert_trust_window
    rate = tracker.recent_suspicious_rate(window)
    if rate >= cfg.alert_trust_collapse_rate and tracker.session_count >= window:
        avg_score = tracker.get_avg_trust_score()
        print_trust_collapse(rate, avg_score, window)


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


# Rough cost estimation per model (per 1K tokens, in CNY)
_COST_TABLE = {
    "claude-opus-4-7": 0.12,
    "claude-opus-4-6": 0.12,
    "claude-sonnet-4-6": 0.024,
    "claude-haiku-4-5": 0.002,
    "gpt-4o": 0.04,
    "gpt-4o-mini": 0.001,
    "deepseek-v4-pro": 0.014,
    "deepseek-v4-flash": 0.004,
}


def _estimate_cost(model: str, total_tokens: int) -> float:
    rate = _COST_TABLE.get(model, 0.02)
    return rate * total_tokens / 1000


# --- Public CLI functions ---


def report():
    print_full_report()


def balance():
    cfg = Config.get()
    results = query_all_balances()

    if not results:
        from .display import _print
        _print(f"  {t('unsupported_provider')}")
        return results

    from .display import _print
    for info in results:
        if info.balance is not None:
            symbol = cfg.currency_symbol
            bar_len = 10
            # Assume max 500 for bar display
            filled = min(bar_len, int(info.balance / 500 * bar_len))
            bar = "█" * filled + "░" * (bar_len - filled)

            warn = ""
            if info.balance < cfg.alert_balance_threshold:
                warn = f" \033[31m⚠ {t('balance_low')}\033[0m"

            _print(f"  {info.provider_name}: {symbol}{info.balance:.2f}  {bar}{warn}")
        else:
            _print(f"  {info.provider_name}: {info.error or t('unsupported_provider')}")

    return results


def score() -> float:
    tracker = get_tracker()
    avg = tracker.get_avg_trust_score()
    from .display import _print
    cfg = Config.get()

    count = tracker.session_count
    suspicious = tracker.session_suspicious

    bar_len = 10
    filled = int(avg / 100 * bar_len)
    bar = "█" * filled + "░" * (bar_len - filled)

    _print(f"  {t('report_trust_score')}: {bar} {int(avg)}/100 ({count} requests, {suspicious} suspicious)")
    return avg
