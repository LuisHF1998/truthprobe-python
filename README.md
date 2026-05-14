> # ⚠️ This project has moved to MCP
>
> **TruthProbe Python SDK is no longer maintained.**
>
> We've rebuilt TruthProbe as an MCP Server that works natively with Claude Code, Cursor, Windsurf, and all MCP-compatible AI tools. No code changes needed.
>
> ## 👉 **[truthprobe-mcp](https://github.com/LuisHF1998/truthprobe-mcp)** (new repo)
>
> ```bash
> npm install -g truthprobe-mcp
> ```
>
> See the [new repo](https://github.com/LuisHF1998/truthprobe-mcp) for setup instructions.

---

<p align="center">
  <strong>TruthProbe</strong> — AI API 信任审计 SDK
</p>

<p align="center">
  <a href="https://pypi.org/project/truthprobe/"><img src="https://img.shields.io/pypi/v/truthprobe?color=blue" alt="PyPI version"></a>
  <img src="https://img.shields.io/pypi/pyversions/truthprobe" alt="Python 3.9+">
  <a href="https://github.com/LuisHF1998/truthprobe-python/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="License MIT"></a>
</p>

<p align="center">
  <a href="#快速开始">中文</a> · <a href="#english-documentation">English</a>
</p>

---

**检测你的 AI 中转站是否偷换模型。3 行代码搞定。**

你付了 GPT-4o 的钱 — 中转站真的在跑 GPT-4o 吗？TruthProbe 通过文本复杂度、时间指纹和模型签名，被动监控每次 API 请求，验证模型真实性。

---

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

---

## 功能列表

| 功能 | 说明 |
|------|------|
| 模型审计 | 自动检测中转站是否偷换模型（如用 GPT-4o-mini 冒充 GPT-4o） |
| 余额查询 | 聚合查看多个中转站账户余额，低余额自动告警 |
| 信任评分 | 每次请求实时打分，累计统计可疑率 |
| CLI 报告 | 命令行生成日报/周报，含趋势折线图 |
| 多中转站 | 支持所有 OpenAI 兼容 API 的中转站 |
| 静默模式 | 不干扰业务输出，后台默默记录 |

---

## CLI 使用

```bash
truthprobe verify --base-url https://your-relay.com/v1 --key sk-xxx --model claude-sonnet-4-6
truthprobe report          # 完整日报
truthprobe report --week   # 周报（含 7 天趋势折线图）
truthprobe balance         # 查询所有 provider 余额
truthprobe score           # 当前信任评分
truthprobe --help
```

### 一行命令验证模型真伪

```bash
$ truthprobe verify --base-url https://api.example.com/v1 --key sk-xxx --model claude-opus-4-7

  TruthProbe Verify — api.example.com
  Model: claude-opus-4-7
  ────────────────────────────────────────

  ✓ PASS
  Trust Score: 88/100
  TTFB: 3200ms | Total: 8500ms
  Returned Model: claude-opus-4-7
```

---

## 输出示例

### 每次请求 — 实时审计行

```
✓ ¥0.032 │ claude-sonnet-4-6 │ 1.2s
✓ ¥0.018 │ gpt-4o │ 0.8s
⚠ ¥0.041 │ claude-opus-4-6 → 疑似降级 │ 2.1s │ 置信度 62%
✓ ¥0.005 │ claude-haiku-4-5 │ 0.4s
```

### `truthprobe report` — 日报

```
╭─────────────────────────────────────────────────────────────╮
│                    TruthProbe 审计报告                       │
│                      今日审计摘要                            │
╰─────────────────────────────────────────────────────────────╯

┌─ 信任评分 ─────────────────────────────────────────────┐
│  总请求: 47    正常: 44    可疑: 3                       │
│  信任评分: ████████░░ 88/100                            │
│  结论: 服务商基本可信，偶有异常，建议持续观察              │
└─────────────────────────────────────────────────────────┘

┌─ 今日花费 ──────────────────────────────────────────────┐
│  今日花费: ¥1.42                                        │
│  模型分布:                                              │
│  claude-sonnet-4-6   ███████████░░░░░░░░░  55%  ¥0.86  │
│  claude-haiku-4-5    █████░░░░░░░░░░░░░░░  26%  ¥0.31  │
│  gpt-4o              ███░░░░░░░░░░░░░░░░░  19%  ¥0.26  │
└─────────────────────────────────────────────────────────┘

┌─ 信号分解 ──────────────────────────────────────────────┐
│  时间指纹异常    ██████████░░░░░░░░░░  50%  (3次)       │
│  文本质量偏低    ██████████░░░░░░░░░░  50%  (3次)       │
└─────────────────────────────────────────────────────────┘
```

### `truthprobe report --week` — 周报

```
╭─────────────────────────────────────────────────────────────╮
│                    TruthProbe 周报                           │
╰─────────────────────────────────────────────────────────────╯

┌─ 近 7 天趋势 ──────────────────────────────────────────┐
│  信任评分:  ▅▆▇▇▆▇█  82 → 90 ↑                        │
│  每日花费:  ▂▃▂▄▃▅▃  avg ¥0.23/天                      │
│  可疑率:    ▃▂▂▁▁▁▁  12% → 2% ↓                       │
│  请求量:    ▁▄█▇▆▅▆  55 total                          │
│                                                         │
│  一  二  三  四  五  六  日                               │
└─────────────────────────────────────────────────────────┘

┌─ 供应商建议 ────────────────────────────────────────────┐
│  ✓ 服务商表现良好，可疑率仅 2%                           │
│  📈 60% 请求使用 claude-sonnet-4-6（花费 ¥0.86）        │
│    → 可在排行榜对比各家该模型定价                         │
│  truthprobe.com/ranking                                 │
└─────────────────────────────────────────────────────────┘
```

### `truthprobe balance` — 余额查询

```
Provider Balances:
  RelayA    ¥142.50    (预估剩余 23 天)
  RelayB    ¥38.20     (预估剩余 6 天)

🚨 RelayB 余额低: ¥38.20，预计 6 天后耗尽
```

---

## 工作原理

TruthProbe 通过 **3 维信号交叉验证** 判断模型真实性：

| 信号 | 权重 | 检测逻辑 |
|------|------|----------|
| 文本复杂度 | 45% | 词汇丰富度、平均句长、推理深度 |
| 响应时间 | 40% | TTFB + tokens/sec 是否符合该模型正常范围 |
| 模型标识 | 15% | 返回的 model 字段是否与请求一致 |

**不夸张说明**：单次检测存在误判可能。TruthProbe 的价值在于多次请求的统计趋势。provider 持续触发告警（可疑率 >30%）= 大概率有问题。

---

## 多 Provider 配置

```python
import truthprobe

truthprobe.init(
    providers=[
        {"name": "RelayA", "base_url": "https://relay-a.com/v1", "key": "sk-aaa"},
        {"name": "RelayB", "base_url": "https://relay-b.com/v1", "key": "sk-bbb"},
    ],
    alert_balance_threshold=50,  # 余额低于 ¥50 时告警
    currency_symbol="¥",
)

truthprobe.patch()
```

---

## 静默模式

```python
truthprobe.patch(quiet=True)     # 完全静默，只记录不输出
truthprobe.patch(verbose=False)  # 不输出每次请求行，但告警仍然触发
```

---

## 社区数据贡献

v0.3.0 起，SDK 默认将**匿名化**的审计指标上报至 TruthProbe 排行榜，帮助改善全社区的信任数据。

**上报内容**: 站点域名、模型名、信任分、响应速度、token 数  
**不上报**: API Key、Prompt 内容、Response 内容、用户身份

```python
truthprobe.patch(report=False)   # 关闭数据上报
```

CLI 中使用 `--no-report` 关闭：
```bash
truthprobe verify --base-url ... --key ... --no-report
```

---

## 排行榜

**[truthprobe.com/ranking](https://truthprobe.com/ranking)** — 看看哪些中转站老实、哪些在偷换模型。

---

## Pro 版本

| 功能 | Free | Pro |
|------|------|-----|
| 本地审计检测 | ✓ | ✓ |
| CLI 报告 | ✓ | ✓ |
| 云端历史记录 | - | ✓ |
| 自动定时报告 | - | ✓ |
| API 调用量分析 | - | ✓ |
| 团队协作 | - | ✓ |

详情: [truthprobe.com/pricing](https://truthprobe.com/pricing)

---

## 贡献

```bash
git clone https://github.com/LuisHF1998/truthprobe-python.git
cd truthprobe-python
pip install -e .
```

欢迎 PR。建议先开 issue 讨论。

---

## 开源协议

MIT

---

<a id="english-documentation"></a>
<details>
<summary><strong>English Documentation</strong></summary>

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

## Features

| Feature | Description |
|---------|-------------|
| Model audit | Detect if relay swaps models (e.g. GPT-4o-mini posing as GPT-4o) |
| Balance monitor | Aggregate balances across relays, auto-alert on low funds |
| Trust scoring | Real-time per-request scoring, cumulative suspicious rate |
| CLI reports | One-command daily & weekly audit reports with trend charts |
| Multi-provider | Works with any OpenAI-compatible API relay |
| Silent mode | Background recording without interfering with your output |

## CLI

```bash
truthprobe report          # Full daily audit report
truthprobe report --week   # Weekly report with 7-day trend charts
truthprobe balance         # Check all provider balances
truthprobe score           # Current trust score
truthprobe --help
```

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

## How It Works

TruthProbe uses **3 independent signals** to verify model authenticity:

| Signal | Weight | Detection |
|--------|--------|-----------|
| Text complexity | 45% | Vocabulary richness, sentence length, reasoning depth |
| Response timing | 40% | TTFB + tokens/sec against known model profiles |
| Model field | 15% | Response model field matches request |

**Honest disclaimer**: Single-request detection has false positive potential. TruthProbe's value is in statistical trends over many requests. If your provider consistently triggers alerts (suspicious rate >30%), there's likely a real problem.

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

## Silent Mode

```python
truthprobe.patch(quiet=True)     # Fully silent — records only, no output
truthprobe.patch(verbose=False)  # No per-request lines, but alerts still fire
```

## Ranking

We continuously track trust scores and pricing across relay providers:

**[truthprobe.com/ranking](https://truthprobe.com/ranking)**

See which relays are honest — and which are swapping models.

## Contributing

```bash
git clone https://github.com/LuisHF1998/truthprobe-python.git
cd truthprobe-python
pip install -e .
```

PRs welcome. Open an issue first to discuss.

## License

MIT

</details>
