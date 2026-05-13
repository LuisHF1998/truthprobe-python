"""
TruthProbe SDK — Display & CLI Output
"""

import sys
from .config import Config
from .i18n import t
from .tracker import get_tracker, RequestRecord


def _print(msg: str):
    sys.stderr.write(msg + "\n")
    sys.stderr.flush()


def print_request_line(record: RequestRecord):
    cfg = Config.get()
    if cfg.quiet:
        return

    symbol = cfg.currency_symbol
    cost_str = f"{symbol}{record.cost:.3f}"
    time_str = f"{record.response_time_ms / 1000:.1f}s"

    if record.is_suspicious:
        line = f"\033[33m⚠ {cost_str} │ {record.model} → {t('suspected_downgrade')} │ {time_str} │ {t('confidence')} {record.trust_score}%\033[0m"
    else:
        line = f"\033[32m✓\033[0m {cost_str} │ {record.model} │ {time_str}"

    _print(line)


def print_balance_alert(provider: str, balance: float, days_left: float):
    msg = f"\033[31m🚨 [TruthProbe] {provider} {t('balance_low')}: {Config.get().currency_symbol}{balance:.2f}，{t('balance_depleted_in', days=int(days_left))}\033[0m"
    _print(msg)


def print_trust_collapse(rate: float, score: float, window: int):
    pct = int(rate * 100)
    msg = f"\033[31m⚠ [TruthProbe] {t('trust_collapse')}: {t('suspicious_rate', window=window, rate=pct)}，{t('trust_score_dropped', score=int(score))}\033[0m"
    _print(msg)


def prompt_first_report() -> bool:
    tracker = get_tracker()
    cfg = Config.get()
    symbol = cfg.currency_symbol

    suspicious = tracker.session_suspicious
    cost = tracker.session_cost
    score = tracker.get_avg_trust_score()
    count = tracker.total_count

    box = f"""
\033[36m╭──────────────────────────────────────────────╮
│ 📊 {t('first_report_title', count=count):^42} │
│    {t('first_report_trust', score=int(score)):^42} │
│    {t('first_report_cost', symbol=symbol, cost=f'{cost:.2f}'):^42} │
│    {t('first_report_suspicious', count=suspicious):^42} │
│                                              │
│    {t('first_report_prompt'):^42} │
╰──────────────────────────────────────────────╯\033[0m"""
    _print(box)

    import sys
    if not sys.stdin.isatty():
        return False
    try:
        answer = input().strip().lower()
        return answer in ("", "y", "yes", "是")
    except (EOFError, KeyboardInterrupt, OSError):
        return False


def print_full_report():
    tracker = get_tracker()
    cfg = Config.get()
    symbol = cfg.currency_symbol

    records = tracker.get_today_records()
    total = len(records)
    suspicious_count = sum(1 for r in records if r.is_suspicious)
    trusted_count = total - suspicious_count
    total_cost = sum(r.cost for r in records)
    avg_score = sum(r.trust_score for r in records) / total if total else 100

    if total < cfg.min_samples_for_audit:
        _print(f"\n  {t('report_no_data', min=cfg.min_samples_for_audit)}\n")
        return

    model_dist = {}
    model_cost = {}
    for r in records:
        model_dist[r.model] = model_dist.get(r.model, 0) + 1
        model_cost[r.model] = model_cost.get(r.model, 0) + r.cost

    if avg_score >= 85:
        conclusion = t("report_conclusion_good")
    elif avg_score >= 65:
        conclusion = t("report_conclusion_warn")
    else:
        conclusion = t("report_conclusion_bad")

    bar_len = 10
    score_filled = int(avg_score / 100 * bar_len)
    score_bar = "█" * score_filled + "░" * (bar_len - score_filled)

    report = f"""
\033[36m╭─────────────────────────────────────────────────────────────╮
│{'':^61}│
│{t('report_title'):^61}│
│{t('report_summary'):^61}│
│{'':^61}│
╰─────────────────────────────────────────────────────────────╯\033[0m

┌─ {t('report_trust_score')} ─────────────────────────────────────────────┐
│                                                              │
│  {t('report_total_requests')}: {total}    {t('report_trusted')}: {trusted_count}    {t('report_suspicious')}: {suspicious_count:<20}│
│  {t('report_trust_score')}: {score_bar} {int(avg_score)}/100{' ' * 25}│
│  {conclusion:<60}│
│                                                              │
└──────────────────────────────────────────────────────────────┘

┌─ {t('report_cost_today')} ──────────────────────────────────────────────┐
│                                                              │
│  {t('report_cost_today')}: {symbol}{total_cost:.2f}{' ' * 40}│
│                                                              │
│  {t('report_model_distribution')}:{' ' * 44}│"""

    for model, count in sorted(model_dist.items(), key=lambda x: -x[1]):
        pct = count / total * 100
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        cost_val = model_cost.get(model, 0)
        line = f"│  {model:<20} {bar} {pct:>3.0f}%  {symbol}{cost_val:.2f}"
        report += f"\n{line:<63}│"

    report += f"""
│                                                              │
└──────────────────────────────────────────────────────────────┘
"""

    _print(report)
