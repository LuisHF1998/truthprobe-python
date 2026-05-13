"""
TruthProbe SDK — Display & CLI Output
"""

import sys
import time
from datetime import datetime, timezone
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


SPARK_CHARS = "▁▂▃▄▅▆▇█"


def _sparkline(values: list[float]) -> str:
    if not values:
        return ""
    mn, mx = min(values), max(values)
    rng = mx - mn if mx != mn else 1
    return "".join(SPARK_CHARS[min(7, int((v - mn) / rng * 7))] for v in values)


def _get_daily_buckets(records: list[dict], days: int = 7) -> list[dict]:
    now = time.time()
    buckets = []
    for i in range(days - 1, -1, -1):
        day_start = now - (i + 1) * 86400
        day_end = now - i * 86400
        day_records = [r for r in records if day_start <= r.get("timestamp", 0) < day_end]
        total = len(day_records)
        suspicious = sum(1 for r in day_records if r.get("is_suspicious", False))
        cost = sum(r.get("cost", 0) for r in day_records)
        avg_score = sum(r.get("trust_score", 100) for r in day_records) / total if total else 0
        buckets.append({
            "total": total,
            "suspicious": suspicious,
            "cost": cost,
            "avg_score": avg_score,
            "date": datetime.fromtimestamp(day_end, tz=timezone.utc),
        })
    return buckets


def _weekday_labels(buckets: list[dict]) -> str:
    zh_days = ["一", "二", "三", "四", "五", "六", "日"]
    en_days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    lang = Config.get().lang
    labels = []
    for b in buckets:
        wd = b["date"].weekday()
        if lang == "zh":
            labels.append(zh_days[wd])
        else:
            labels.append(en_days[wd])
    if lang == "zh":
        return "  ".join(f"{l}" for l in labels)
    return " ".join(f"{l}" for l in labels)


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

    # Signal breakdown
    report += _signal_breakdown(records)

    _print(report)


def _signal_breakdown(records: list[RequestRecord]) -> str:
    if not records:
        return ""

    suspicious = [r for r in records if r.is_suspicious]
    if not suspicious:
        return ""

    flag_counts: dict[str, int] = {}
    for r in suspicious:
        for flag in r.flags:
            flag_counts[flag] = flag_counts.get(flag, 0) + 1

    if not flag_counts:
        return ""

    lang = Config.get().lang

    flag_labels = {
        "text_quality_low": "文本质量偏低" if lang == "zh" else "Text quality low",
        "timing_anomaly": "时间指纹异常" if lang == "zh" else "Timing anomaly",
        "model_field_mismatch": "模型字段不匹配" if lang == "zh" else "Model field mismatch",
        "model_swapped": "模型替换" if lang == "zh" else "Model swapped",
        "input_token_mismatch": "Token 虚报" if lang == "zh" else "Token mismatch",
    }

    title = "信号分解" if lang == "zh" else "Signal Breakdown"
    header = f"\n┌─ {title} {'─' * (47 - len(title))}┐\n│{' ' * 62}│\n"

    lines = ""
    total_flags = sum(flag_counts.values())
    for flag, cnt in sorted(flag_counts.items(), key=lambda x: -x[1]):
        label = flag_labels.get(flag, flag)
        pct = cnt / total_flags * 100
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        line = f"│  {label:<18} {bar} {pct:>3.0f}%  ({cnt}次)"
        lines += f"{line:<63}│\n"

    footer = f"│{' ' * 62}│\n└{'─' * 62}┘\n"
    return header + lines + footer


def print_weekly_report():
    tracker = get_tracker()
    cfg = Config.get()
    symbol = cfg.currency_symbol

    all_records = tracker.get_all_history(limit=1000)
    if len(all_records) < 5:
        _print(f"\n  {t('report_no_data', min=5)}\n")
        return

    buckets = _get_daily_buckets(all_records, days=7)

    scores = [b["avg_score"] for b in buckets if b["total"] > 0]
    costs = [b["cost"] for b in buckets if b["total"] > 0]
    suspicious_rates = [
        (b["suspicious"] / b["total"] * 100) if b["total"] > 0 else 0
        for b in buckets
    ]
    totals = [b["total"] for b in buckets]

    score_spark = _sparkline(scores) if scores else "─" * 7
    cost_spark = _sparkline(costs) if costs else "─" * 7
    sus_spark = _sparkline(suspicious_rates)
    vol_spark = _sparkline([float(x) for x in totals])

    total_requests = sum(b["total"] for b in buckets)
    total_cost = sum(b["cost"] for b in buckets)
    total_suspicious = sum(b["suspicious"] for b in buckets)
    avg_score_all = sum(scores) / len(scores) if scores else 0
    sus_rate = (total_suspicious / total_requests * 100) if total_requests > 0 else 0

    score_first = scores[0] if scores else 0
    score_last = scores[-1] if scores else 0
    score_trend = "↑" if score_last > score_first else ("↓" if score_last < score_first else "→")

    sus_first = suspicious_rates[0] if suspicious_rates else 0
    sus_last = suspicious_rates[-1] if suspicious_rates else 0
    sus_trend = "↓" if sus_last < sus_first else ("↑" if sus_last > sus_first else "→")

    cost_avg = total_cost / 7

    day_labels = _weekday_labels(buckets)

    lang = Config.get().lang

    title = "TruthProbe 周报" if lang == "zh" else "TruthProbe Weekly Report"
    subtitle = "近 7 天趋势" if lang == "zh" else "7-Day Trends"
    score_label = "信任评分" if lang == "zh" else "Trust Score"
    cost_label = "每日花费" if lang == "zh" else "Daily Cost"
    sus_label = "可疑率" if lang == "zh" else "Suspicious %"
    vol_label = "请求量" if lang == "zh" else "Requests"
    summary_title = "汇总" if lang == "zh" else "Summary"
    avg_label = "平均" if lang == "zh" else "avg"
    day_label = "/天" if lang == "zh" else "/day"
    rec_title = "供应商建议" if lang == "zh" else "Provider Recommendations"

    report = f"""
\033[36m╭─────────────────────────────────────────────────────────────╮
│{'':^61}│
│{title:^61}│
│{'':^61}│
╰─────────────────────────────────────────────────────────────╯\033[0m

┌─ {subtitle} ────────────────────────────────────────────────┐
│                                                              │
│  {score_label}:  {score_spark}  {int(score_first)} → {int(score_last)} {score_trend}{' ' * 25}│
│  {cost_label}:  {cost_spark}  {avg_label} {symbol}{cost_avg:.2f}{day_label}{' ' * 22}│
│  {sus_label}:    {sus_spark}  {sus_first:.0f}% → {sus_last:.0f}% {sus_trend}{' ' * 24}│
│  {vol_label}:    {vol_spark}  {total_requests} total{' ' * 26}│
│                                                              │
│  {day_labels}{' ' * (60 - len(day_labels))}│
│                                                              │
└──────────────────────────────────────────────────────────────┘

┌─ {summary_title} ──────────────────────────────────────────────────┐
│                                                              │
│  📊 {t('report_total_requests')}: {total_requests:<8} {t('report_trust_score')}: {int(avg_score_all)}/100{' ' * 15}│
│  💰 {t('report_cost_today')}: {symbol}{total_cost:.2f}{' ' * 8} {t('report_suspicious')}: {total_suspicious} ({sus_rate:.0f}%){' ' * 10}│
│                                                              │
└──────────────────────────────────────────────────────────────┘
"""

    # Provider recommendations
    rec = _provider_recommendations(all_records, lang, symbol)
    if rec:
        report += rec

    _print(report)


def _provider_recommendations(records: list[dict], lang: str, symbol: str) -> str:
    if not records:
        return ""

    total = len(records)
    suspicious = sum(1 for r in records if r.get("is_suspicious", False))
    sus_rate = suspicious / total if total > 0 else 0

    lines = []

    if sus_rate >= 0.15:
        if lang == "zh":
            lines.append(f"  ⚠ 本周可疑率 {int(sus_rate*100)}%，建议考虑更换或分流")
            lines.append(f"    → 查看可信服务商: truthprobe.com/ranking")
        else:
            lines.append(f"  ⚠ Weekly suspicious rate {int(sus_rate*100)}%, consider switching")
            lines.append(f"    → Find trusted providers: truthprobe.com/ranking")
    elif sus_rate >= 0.05:
        if lang == "zh":
            lines.append(f"  💡 可疑率 {int(sus_rate*100)}%，偶有异常，持续观察")
            lines.append(f"    → 排行榜对比: truthprobe.com/ranking")
        else:
            lines.append(f"  💡 Suspicious rate {int(sus_rate*100)}%, occasional anomalies")
            lines.append(f"    → Compare providers: truthprobe.com/ranking")
    else:
        if lang == "zh":
            lines.append(f"  ✓ 服务商表现良好，可疑率仅 {int(sus_rate*100)}%")
        else:
            lines.append(f"  ✓ Provider performing well, only {int(sus_rate*100)}% suspicious")

    # Model cost optimization hint
    model_costs: dict[str, float] = {}
    model_counts: dict[str, int] = {}
    for r in records:
        m = r.get("model", "")
        model_costs[m] = model_costs.get(m, 0) + r.get("cost", 0)
        model_counts[m] = model_counts.get(m, 0) + 1

    if model_costs:
        top_model = max(model_costs, key=model_costs.get)
        top_pct = model_counts.get(top_model, 0) / total * 100
        top_cost = model_costs[top_model]
        if top_pct >= 50:
            if lang == "zh":
                lines.append(f"")
                lines.append(f"  📈 {int(top_pct)}% 请求使用 {top_model}（花费 {symbol}{top_cost:.2f}）")
                lines.append(f"    → 可在排行榜对比各家该模型定价")
            else:
                lines.append(f"")
                lines.append(f"  📈 {int(top_pct)}% of requests use {top_model} ({symbol}{top_cost:.2f})")
                lines.append(f"    → Compare pricing on the ranking page")

    if not lines:
        return ""

    title = "供应商建议" if lang == "zh" else "Recommendations"
    header = f"\n┌─ {title} {'─' * (47 - len(title))}┐\n│{' ' * 62}│\n"
    body = ""
    for line in lines:
        body += f"│{line:<62}│\n"
    footer = f"│{' ' * 62}│\n│  {'truthprobe.com/ranking':<60}│\n│{' ' * 62}│\n└{'─' * 62}┘\n"

    return header + body + footer
