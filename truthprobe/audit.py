"""
TruthProbe SDK — Audit Engine (adapted from server audit_engine.py)
Lightweight version for local SDK use.
"""

import re
import statistics
from dataclasses import dataclass, field
from typing import Optional


MODEL_PROFILES = {
    "claude-opus-4-7": {"tier": "top", "family": "claude", "vocabulary_richness": (0.65, 0.85), "avg_sentence_length": (15, 25), "reasoning_depth_score": (7, 10), "ttfb_ms": (800, 4000), "tokens_per_sec": (15, 50)},
    "claude-opus-4-6": {"tier": "top", "family": "claude", "vocabulary_richness": (0.65, 0.85), "avg_sentence_length": (15, 25), "reasoning_depth_score": (7, 10), "ttfb_ms": (800, 4000), "tokens_per_sec": (15, 50)},
    "claude-sonnet-4-6": {"tier": "mid", "family": "claude", "vocabulary_richness": (0.55, 0.75), "avg_sentence_length": (12, 22), "reasoning_depth_score": (5, 8), "ttfb_ms": (300, 1500), "tokens_per_sec": (40, 120)},
    "claude-haiku-4-5": {"tier": "low", "family": "claude", "vocabulary_richness": (0.45, 0.65), "avg_sentence_length": (10, 18), "reasoning_depth_score": (3, 6), "ttfb_ms": (100, 600), "tokens_per_sec": (80, 200)},
    "gpt-4o": {"tier": "top", "family": "openai", "vocabulary_richness": (0.60, 0.80), "avg_sentence_length": (14, 24), "reasoning_depth_score": (6, 9), "ttfb_ms": (200, 1200), "tokens_per_sec": (30, 100)},
    "gpt-4o-mini": {"tier": "low", "family": "openai", "vocabulary_richness": (0.45, 0.65), "avg_sentence_length": (10, 20), "reasoning_depth_score": (3, 7), "ttfb_ms": (100, 500), "tokens_per_sec": (60, 180)},
    "deepseek-v4-pro": {"tier": "mid", "family": "deepseek", "vocabulary_richness": (0.55, 0.75), "avg_sentence_length": (12, 22), "reasoning_depth_score": (5, 8), "ttfb_ms": (300, 2000), "tokens_per_sec": (20, 80)},
    "deepseek-v4-flash": {"tier": "low", "family": "deepseek", "vocabulary_richness": (0.45, 0.65), "avg_sentence_length": (10, 18), "reasoning_depth_score": (3, 6), "ttfb_ms": (100, 800), "tokens_per_sec": (50, 150)},
}

HEDGE_PATTERNS = [
    r"it'?s worth noting", r"however", r"that said", r"on the other hand",
    r"arguably", r"it depends", r"nuance", r"caveat",
    r"值得注意", r"不过", r"话虽如此", r"需要指出",
]

PERSPECTIVE_PATTERNS = [
    r"from .+ perspective", r"one view", r"alternatively",
    r"从.*角度", r"另一种观点", r"支持者认为",
]

SELF_AWARE_PATTERNS = [
    r"I should (note|mention)", r"my (assumption|limitation)",
    r"I('m| am) not (certain|sure)", r"我需要说明", r"我不确定",
]


@dataclass
class AuditResult:
    trust_score: int = 100
    confidence: float = 0.0
    claimed_model: str = ""
    likely_tier: str = "matches_claimed"
    flags: list = field(default_factory=list)
    is_suspicious: bool = False


def _analyze_text(text: str) -> dict:
    if not text:
        return {"vocabulary_richness": 0, "avg_sentence_length": 0, "reasoning_depth": 0}

    words = re.findall(r'\b\w+\b', text.lower())
    sentences = [s for s in re.split(r'[.!?。！？]\s*', text) if len(s.strip()) > 5]

    word_count = max(len(words), 1)
    sentence_count = max(len(sentences), 1)
    unique_words = len(set(words))

    vr = unique_words / word_count
    asl = word_count / sentence_count

    hedge_count = sum(1 for p in HEDGE_PATTERNS if re.search(p, text, re.I))
    perspective_count = sum(1 for p in PERSPECTIVE_PATTERNS if re.search(p, text, re.I))
    self_aware_count = sum(1 for p in SELF_AWARE_PATTERNS if re.search(p, text, re.I))

    depth = 0.0
    if vr > 0.7: depth += 2.5
    elif vr > 0.55: depth += 1.5
    elif vr > 0.45: depth += 0.5
    if asl > 18: depth += 2.0
    elif asl > 12: depth += 1.0
    depth += min(2.0, hedge_count * 0.7)
    depth += min(2.0, perspective_count * 1.0)
    depth += min(1.5, self_aware_count * 0.75)
    depth = min(10.0, depth)

    return {"vocabulary_richness": vr, "avg_sentence_length": asl, "reasoning_depth": depth}


def _score_text(features: dict, profile: dict) -> float:
    scores = []

    vr = features["vocabulary_richness"]
    vr_range = profile["vocabulary_richness"]
    if vr_range[0] <= vr <= vr_range[1]:
        scores.append(1.0)
    elif vr < vr_range[0]:
        scores.append(max(0, 1.0 - (vr_range[0] - vr) * 5))
    else:
        scores.append(0.8)

    asl = features["avg_sentence_length"]
    sl_range = profile["avg_sentence_length"]
    if sl_range[0] <= asl <= sl_range[1]:
        scores.append(1.0)
    elif asl < sl_range[0]:
        scores.append(max(0, 1.0 - (sl_range[0] - asl) * 0.1))
    else:
        scores.append(0.9)

    depth = features["reasoning_depth"]
    d_range = profile["reasoning_depth_score"]
    if d_range[0] <= depth <= d_range[1]:
        scores.append(1.0)
    elif depth < d_range[0]:
        scores.append(max(0, 1.0 - (d_range[0] - depth) * 0.2))
    else:
        scores.append(0.9)

    return sum(scores) / len(scores) if scores else 0.5


def _score_timing(ttfb_ms: float, tokens_per_sec: float, profile: dict) -> float:
    scores = []

    if ttfb_ms > 0:
        ttfb_range = profile["ttfb_ms"]
        if ttfb_ms < ttfb_range[0] * 0.4:
            scores.append(0.2)
        elif ttfb_range[0] <= ttfb_ms <= ttfb_range[1] * 1.5:
            scores.append(1.0)
        else:
            scores.append(0.7)

    if tokens_per_sec > 0:
        tps_range = profile["tokens_per_sec"]
        if tokens_per_sec > tps_range[1] * 1.8:
            scores.append(0.1)
        elif tps_range[0] <= tokens_per_sec <= tps_range[1]:
            scores.append(1.0)
        elif tokens_per_sec < tps_range[0] * 0.5:
            scores.append(0.7)
        else:
            scores.append(0.85)

    return sum(scores) / len(scores) if scores else 0.5


def run_audit(
    claimed_model: str,
    response_text: str,
    returned_model: str = "",
    ttfb_ms: float = 0.0,
    total_ms: float = 0.0,
    total_tokens: int = 0,
) -> AuditResult:
    profile = MODEL_PROFILES.get(claimed_model)
    if not profile:
        return AuditResult(trust_score=50, confidence=0.0, claimed_model=claimed_model, likely_tier="unknown")

    text_features = _analyze_text(response_text)
    text_score = _score_text(text_features, profile)

    tps = (total_tokens / (total_ms / 1000)) if total_ms > 0 else 0
    timing_score = _score_timing(ttfb_ms, tps, profile)

    model_score = 1.0
    if returned_model and returned_model.lower() != claimed_model.lower():
        if claimed_model.split("-")[0] not in returned_model.lower():
            model_score = 0.2

    weighted = text_score * 0.45 + timing_score * 0.40 + model_score * 0.15
    trust_score = int(weighted * 100)

    flags = []
    if text_score < 0.5:
        flags.append("text_quality_low")
    if timing_score < 0.5:
        flags.append("timing_anomaly")
    if model_score < 0.5:
        flags.append("model_mismatch")

    if weighted >= 0.8:
        likely_tier = "matches_claimed"
    elif weighted >= 0.6:
        likely_tier = "uncertain"
    else:
        likely_tier = "likely_downgraded"

    return AuditResult(
        trust_score=trust_score,
        confidence=min(0.8, 0.3 + (0.1 if ttfb_ms > 0 else 0) + (0.2 if len(response_text) > 50 else 0)),
        claimed_model=claimed_model,
        likely_tier=likely_tier,
        flags=flags,
        is_suspicious=len(flags) > 0,
    )
