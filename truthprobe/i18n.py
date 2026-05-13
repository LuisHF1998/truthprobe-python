"""
TruthProbe SDK i18n — Minimal translation strings
"""

STRINGS = {
    "zh": {
        "trusted": "可信",
        "suspected_downgrade": "疑似降级",
        "confidence": "可信度",
        "cost": "花费",
        "balance": "余额",
        "balance_low": "余额不足",
        "balance_depleted_in": "预计 {days} 天内耗尽",
        "trust_collapse": "信任崩塌",
        "suspicious_rate": "近 {window} 次请求可疑率 {rate}%",
        "trust_score_dropped": "信任评分降至 {score}",
        "first_report_title": "TruthProbe 首份分析完成（{count} 次请求）",
        "first_report_trust": "信任评分: {score}/100",
        "first_report_cost": "花费: {symbol}{cost}",
        "first_report_suspicious": "检测到 {count} 条可疑记录",
        "first_report_prompt": "查看完整报告？[Y/n]",
        "report_title": "TruthProbe 审计报告",
        "report_summary": "今日摘要",
        "report_total_requests": "总请求",
        "report_trusted": "可信",
        "report_suspicious": "可疑",
        "report_cost_today": "今日花费",
        "report_cost_month": "本月累计",
        "report_budget_remaining": "预算剩余",
        "report_model_distribution": "模型分布",
        "report_trust_score": "信任评分",
        "report_conclusion_good": "该中转站表现正常",
        "report_conclusion_warn": "该中转站存在间歇性降级行为，建议关注",
        "report_conclusion_bad": "该中转站存在系统性降级，建议更换",
        "report_balance_title": "余额监控",
        "report_no_data": "数据不足，请至少完成 {min} 次请求后查看",
        "unsupported_provider": "暂不支持该中转站余额查询",
        "weekly_title": "TruthProbe 周报",
        "weekly_subtitle": "近 7 天趋势",
        "signal_breakdown": "信号分解",
        "recommendations": "供应商建议",
    },
    "en": {
        "trusted": "trusted",
        "suspected_downgrade": "suspected downgrade",
        "confidence": "confidence",
        "cost": "cost",
        "balance": "balance",
        "balance_low": "low balance",
        "balance_depleted_in": "estimated {days} days until depleted",
        "trust_collapse": "trust collapse",
        "suspicious_rate": "suspicious rate {rate}% in last {window} requests",
        "trust_score_dropped": "trust score dropped to {score}",
        "first_report_title": "TruthProbe first analysis complete ({count} requests)",
        "first_report_trust": "Trust score: {score}/100",
        "first_report_cost": "Cost: {symbol}{cost}",
        "first_report_suspicious": "{count} suspicious record(s) detected",
        "first_report_prompt": "View full report? [Y/n]",
        "report_title": "TruthProbe Audit Report",
        "report_summary": "Today's Summary",
        "report_total_requests": "Total requests",
        "report_trusted": "Trusted",
        "report_suspicious": "Suspicious",
        "report_cost_today": "Today's cost",
        "report_cost_month": "Month total",
        "report_budget_remaining": "Budget remaining",
        "report_model_distribution": "Model distribution",
        "report_trust_score": "Trust score",
        "report_conclusion_good": "Provider is performing normally",
        "report_conclusion_warn": "Provider shows intermittent downgrade behavior, monitor closely",
        "report_conclusion_bad": "Provider shows systematic downgrade, consider switching",
        "report_balance_title": "Balance Monitor",
        "report_no_data": "Insufficient data, complete at least {min} requests first",
        "unsupported_provider": "Balance query not supported for this provider",
        "weekly_title": "TruthProbe Weekly Report",
        "weekly_subtitle": "7-Day Trends",
        "signal_breakdown": "Signal Breakdown",
        "recommendations": "Provider Recommendations",
    },
}


def t(key: str, **kwargs) -> str:
    from .config import Config
    lang = Config.get().lang
    strings = STRINGS.get(lang, STRINGS["en"])
    template = strings.get(key, STRINGS["en"].get(key, key))
    if kwargs:
        return template.format(**kwargs)
    return template
