<p align="center">
  <strong>TruthProbe</strong> — AI API 信任审计 SDK
</p>

<p align="center">
  <a href="https://pypi.org/project/truthprobe/"><img src="https://img.shields.io/pypi/v/truthprobe?color=blue" alt="PyPI version"></a>
  <img src="https://img.shields.io/pypi/pyversions/truthprobe" alt="Python 3.9+">
  <a href="https://github.com/LuisHF1998/truthprobe-python/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="License MIT"></a>
</p>

---

**检测你的 AI 中转站有没有偷换模型，3 行代码搞定。**

你付了 GPT-4o 的钱，中转站真的在跑 GPT-4o 吗？TruthProbe 自动监测每一次 API 请求，通过文本复杂度、响应时间、模型标识等多维信号判断模型真实性。

---

## Quick Start

```bash
pip install truthprobe
```

```python
import truthprobe

truthprobe.patch()  # 一行代码，自动审计所有 OpenAI 兼容请求

# 之后正常使用 OpenAI SDK 即可
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
| CLI 报告 | 命令行一键生成审计报告 |
| 多中转站适配 | 支持所有 OpenAI 兼容 API 的中转站 |
| 静默模式 | 不干扰业务输出，后台默默记录 |

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

## CLI 使用

```bash
# 查看完整审计报告
truthprobe report

# 查看本周报告
truthprobe report --week

# 查询所有 provider 余额
truthprobe balance

# 查看当前信任评分
truthprobe score

# 帮助
truthprobe --help
```

示例输出:

```
TruthProbe CLI — AI API Trust & Cost Transparency

Commands:
    truthprobe report          Full audit report (today)
    truthprobe report --week   Weekly report
    truthprobe balance         Check provider balances
    truthprobe score           Current trust score

Options:
    --lang zh|en               Set language
    --quiet                    Suppress output
```

---

## 工作原理

TruthProbe 通过 **3 维信号交叉验证** 判断模型真实性：

| 信号 | 权重 | 检测逻辑 |
|------|------|----------|
| 文本复杂度 | 45% | 词汇丰富度、平均句长、推理深度（对冲语、多角度论述、自我意识表达） |
| 响应时间 | 40% | TTFB + tokens/sec 是否符合该模型的正常范围 |
| 模型标识 | 15% | 返回的 model 字段是否与请求一致 |

每个模型（Claude Opus/Sonnet/Haiku, GPT-4o/4o-mini, DeepSeek 等）都有独立的基线参数。当综合评分低于阈值时，标记为可疑请求。

**不夸张说明**：单次检测存在误判可能，TruthProbe 的价值在于多次请求的统计趋势。如果你的 provider 持续触发告警（可疑率 >30%），那大概率有问题。

---

## 静默模式

```python
truthprobe.patch(quiet=True)     # 完全静默，只记录不输出
truthprobe.patch(verbose=False)  # 不输出每次请求行，但告警仍然触发
```

---

## 排行榜

我们持续跟踪主流中转站的信任评分和性价比数据：

**[truthprobe.com/ranking](https://truthprobe.com/ranking)**

看看哪些中转站老实、哪些在偷换模型。

---

## Pro 版本

| 功能 | Free | Pro |
|------|------|-----|
| 本地审计检测 | Yes | Yes |
| CLI 报告 | Yes | Yes |
| 云端历史记录 | - | Yes |
| 多设备同步 | - | Yes |
| 自动定时报告 | - | Yes |
| API 调用量分析 | - | Yes |
| 团队协作 | - | Yes |

详情: [truthprobe.com/pricing](https://truthprobe.com/pricing)

---

## Contributing

欢迎贡献代码。

```bash
git clone https://github.com/LuisHF1998/truthprobe-python.git
cd truthprobe-python
pip install -e .
```

提 PR 前请确保代码能通过基本测试。有问题先开 issue 讨论。

---

## License

MIT
