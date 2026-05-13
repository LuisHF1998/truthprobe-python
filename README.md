<p align="center">
  <strong>TruthProbe</strong> — AI API Trust Audit SDK
</p>

<p align="center">
  <a href="https://pypi.org/project/truthprobe/"><img src="https://img.shields.io/pypi/v/truthprobe?color=blue" alt="PyPI version"></a>
  <img src="https://img.shields.io/pypi/pyversions/truthprobe" alt="Python 3.9+">
  <a href="https://github.com/LuisHF1998/truthprobe-python/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="License MIT"></a>
</p>

<p align="center">
  <a href="#quick-start">English</a> · <a href="#快速开始">中文</a>
</p>

---

**Detect if your AI relay is secretly swapping models. 3 lines of code.**

You're paying for GPT-4o — is your relay actually running GPT-4o? TruthProbe passively monitors every API request using text complexity, timing patterns, and model signatures to verify model authenticity.

---

## Quick Start

```bash
pip install truthprobe
```

```python
import truthprobe

truthprobe.patch()  # One line — all OpenAI-compatible calls are now audited

from openai import OpenAI
client = OpenAI(api_key="sk-xxx", base_url="https://your-relay.com/v1")
response = client.chat.completions.create(
    model="claude-sonnet-4-6",
    messages=[{"role": "user", "content": "Hello"}]
)
# Terminal output:
# ✓ ¥0.032 │ claude-sonnet-4-6 │ 1.2s │ trust: 92
```

---

## Features

| Feature | Description |
|---------|-------------|
| Model audit | Detect if relay swaps models (e.g. GPT-4o-mini posing as GPT-4o) |
| Balance monitor | Aggregate balances across relays, auto-alert on low funds |
| Trust scoring | Real-time per-request scoring, cumulative suspicious rate |
| CLI reports | One-command daily & weekly audit reports with trend charts |
| Multi-provider | Works with any OpenAI-compatible API relay |
| Silent mode | Background recording without interfering with your output |

---

## CLI

```bash
truthprobe report          # Full daily audit report
truthprobe report --week   # Weekly report with 7-day trend charts
truthprobe balance         # Check all provider balances
truthprobe score           # Current trust score
truthprobe --help
```

---

## Output Examples

### Per-request — real-time audit line

```
✓ ¥0.032 │ claude-sonnet-4-6 │ 1.2s
✓ ¥0.018 │ gpt-4o │ 0.8s
⚠ ¥0.041 │ claude-opus-4-6 → suspected swap │ 2.1s │ confidence 62%
✓ ¥0.005 │ claude-haiku-4-5 │ 0.4s
```

### `truthprobe report` — daily audit report

```
╭─────────────────────────────────────────────────────────────╮
│                                                             │
│                   TruthProbe Audit Report                   │
│                       Today's Summary                       │
│                                                             │
╰─────────────────────────────────────────────────────────────╯

┌─ Trust Score ──────────────────────────────────────────┐
│                                                         │
│  Total: 47    Trusted: 44    Suspicious: 3              │
│  Trust score: ████████░░ 88/100                         │
│  Provider is performing normally                        │
│                                                         │
└─────────────────────────────────────────────────────────┘

┌─ Cost ─────────────────────────────────────────────────┐
│                                                         │
│  Today's cost: ¥1.42                                    │
│                                                         │
│  Model distribution:                                    │
│  claude-sonnet-4-6   ███████████░░░░░░░░░  55%  ¥0.86  │
│  claude-haiku-4-5    █████░░░░░░░░░░░░░░░  26%  ¥0.31  │
│  gpt-4o              ███░░░░░░░░░░░░░░░░░  19%  ¥0.26  │
│                                                         │
└─────────────────────────────────────────────────────────┘

┌─ Signal Breakdown ─────────────────────────────────────┐
│                                                         │
│  Timing anomaly      ██████████░░░░░░░░░░  50%  (3x)   │
│  Text quality low    ██████████░░░░░░░░░░  50%  (3x)   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### `truthprobe report --week` — weekly report with trend charts

```
╭─────────────────────────────────────────────────────────────╮
│                                                             │
│                  TruthProbe Weekly Report                   │
│                                                             │
╰─────────────────────────────────────────────────────────────╯

┌─ 7-Day Trends ─────────────────────────────────────────┐
│                                                         │
│  Trust Score:  ▅▆▇▇▆▇█  82 → 90 ↑                     │
│  Daily Cost:   ▂▃▂▄▃▅▃  avg ¥0.23/day                 │
│  Suspicious %: ▃▂▂▁▁▁▁  12% → 2% ↓                   │
│  Requests:     ▁▄█▇▆▅▆  55 total                      │
│                                                         │
│  Mon Tue Wed Thu Fri Sat Sun                            │
│                                                         │
└─────────────────────────────────────────────────────────┘

┌─ Recommendations ─────────────────────────────────────┐
│                                                         │
│  ✓ Provider performing well, only 2% suspicious         │
│                                                         │
│  📈 60% of requests use claude-sonnet-4-6 (¥0.86)      │
│    → Compare pricing on the ranking page                │
│                                                         │
│  truthprobe.com/ranking                                 │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## How It Works

TruthProbe uses **3 independent signals** to verify model authenticity:

| Signal | Weight | Detection |
|--------|--------|-----------|
| Text complexity | 45% | Vocabulary richness, sentence length, reasoning depth |
| Response timing | 40% | TTFB + tokens/sec against known model profiles |
| Model field | 15% | Response model field matches request |

Each model (Claude Opus/Sonnet/Haiku, GPT-4o/4o-mini, DeepSeek, etc.) has independent baseline parameters. When the combined score drops below threshold, the request is flagged.

**Honest disclaimer**: Single-request detection has false positive potential. TruthProbe's value is in statistical trends over many requests. If your provider consistently triggers alerts (suspicious rate >30%), there's likely a real problem.

---

## Multi-Provider Setup

```python
import truthprobe

truthprobe.init(
    providers=[
        {"name": "RelayA", "base_url": "https://relay-a.com/v1", "key": "sk-aaa"},
        {"name": "RelayB", "base_url": "https://relay-b.com/v1", "key": "sk-bbb"},
    ],
    alert_balance_threshold=50,
    currency_symbol="¥",
)

truthprobe.patch()
```

---

## Silent Mode

```python
truthprobe.patch(quiet=True)     # Fully silent — records only, no output
truthprobe.patch(verbose=False)  # No per-request lines, but alerts still fire
```

---

## Ranking

We continuously track trust scores and pricing across relay providers:

**[truthprobe.com/ranking](https://truthprobe.com/ranking)**

See which relays are honest — and which are swapping models.

---

## Contributing

```bash
git clone https://github.com/LuisHF1998/truthprobe-python.git
cd truthprobe-python
pip install -e .
```

PRs welcome. Open an issue first to discuss.

---

## License

MIT

---

<details>
<summary><strong>中文文档 (Chinese)</strong></summary>

## 快速开始

```bash
pip install truthprobe
```

```python
import truthprobe

truthprobe.patch()  # 一行代码，自动审计所有 OpenAI 兼容请求

from openai import OpenAI
client = OpenAI(api_key="sk-xxx", base_url="https://your-relay.com/v1")
response = client.chat.completions.create(
    model="claude-sonnet-4-6",
    messages=[{"role": "user", "content": "Hello"}]
)
# 控制台自动输出:
# ✓ ¥0.032 │ claude-sonnet-4-6 │ 1.2s │ trust: 92
```

## 功能列表

| 功能 | 说明 |
|------|------|
| 模型审计 | 自动检测中转站是否偷换模型（如用 GPT-4o-mini 冒充 GPT-4o） |
| 余额查询 | 聚合查看多个中转站账户余额，低余额自动告警 |
| 信任评分 | 每次请求实时打分，累计统计可疑率 |
| CLI 报告 | 命令行生成日报/周报，含趋势图 |
| 多中转站 | 支持所有 OpenAI 兼容 API 的中转站 |
| 静默模式 | 不干扰业务输出，后台默默记录 |

## 工作原理

TruthProbe 通过 **3 维信号交叉验证** 判断模型真实性：

| 信号 | 权重 | 检测逻辑 |
|------|------|----------|
| 文本复杂度 | 45% | 词汇丰富度、平均句长、推理深度 |
| 响应时间 | 40% | TTFB + tokens/sec 是否符合该模型正常范围 |
| 模型标识 | 15% | 返回的 model 字段是否与请求一致 |

**不夸张说明**：单次检测存在误判可能。TruthProbe 的价值在于多次请求的统计趋势。provider 持续触发告警（可疑率 >30%）= 大概率有问题。

## 排行榜

**[truthprobe.com/ranking](https://truthprobe.com/ranking)** — 看看哪些中转站老实、哪些在偷换模型。

</details>
