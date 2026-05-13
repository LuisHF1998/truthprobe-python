"""
TruthProbe SDK — CLI Entry Point
Usage:
    truthprobe verify          Verify a provider's model authenticity
    truthprobe report          Full audit report
    truthprobe balance         Check all provider balances
    truthprobe score           Current trust score
"""

import sys
import time
import json

from .config import Config
from .core import report, balance, score


def main():
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help", "help"):
        print("""TruthProbe CLI — AI API Trust & Cost Transparency

Commands:
    truthprobe verify          Verify provider model authenticity
    truthprobe report          Full audit report (today)
    truthprobe report --week   Weekly report with 7-day trends
    truthprobe balance         Check provider balances
    truthprobe score           Current trust score

Options:
    --base-url URL             Provider API base URL
    --key KEY                  API key for the provider
    --model MODEL              Model to verify (default: claude-sonnet-4-6)
    --no-report                Disable anonymous metric sharing
    --lang zh|en               Set language
    --quiet                    Suppress output
""")
        return

    # Parse global flags
    if "--lang" in args:
        idx = args.index("--lang")
        if idx + 1 < len(args):
            Config.set(lang=args[idx + 1])
            args = args[:idx] + args[idx + 2:]

    if "--quiet" in args:
        Config.set(quiet=True)
        args.remove("--quiet")

    if "--no-report" in args:
        Config.set(report=False)
        args.remove("--no-report")

    cmd = args[0] if args else "report"

    if cmd == "verify":
        _cmd_verify(args[1:])
    elif cmd == "report":
        if "--week" in args or "-w" in args:
            from .display import print_weekly_report
            print_weekly_report()
        else:
            report()
    elif cmd == "balance":
        balance()
    elif cmd == "score":
        score()
    else:
        print(f"Unknown command: {cmd}")
        print("Run 'truthprobe --help' for usage.")
        sys.exit(1)


def _cmd_verify(args):
    """Run a quick model verification probe against a provider."""
    base_url = ""
    api_key = ""
    model = "claude-sonnet-4-6"

    if "--base-url" in args:
        idx = args.index("--base-url")
        if idx + 1 < len(args):
            base_url = args[idx + 1]

    if "--key" in args:
        idx = args.index("--key")
        if idx + 1 < len(args):
            api_key = args[idx + 1]

    if "--model" in args:
        idx = args.index("--model")
        if idx + 1 < len(args):
            model = args[idx + 1]

    if not base_url or not api_key:
        print("Error: --base-url and --key are required")
        print("Usage: truthprobe verify --base-url https://api.example.com/v1 --key sk-xxx")
        sys.exit(1)

    from .audit import run_audit
    from urllib.request import Request as URLRequest, urlopen
    from urllib.parse import urlparse

    url = base_url.rstrip("/") + "/chat/completions"
    domain = urlparse(base_url).hostname

    print(f"\n  TruthProbe Verify — {domain}")
    print(f"  Model: {model}")
    print(f"  {'─' * 40}")

    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": "Explain the philosophical implications of Gödel's incompleteness theorems on artificial intelligence. Consider multiple perspectives and identify the strongest counterargument to your main thesis."}],
        "max_tokens": 500,
        "temperature": 0.7,
    }).encode()

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    start = time.time()
    try:
        req = URLRequest(url, data=payload, headers=headers, method="POST")
        with urlopen(req, timeout=30) as resp:
            ttfb_ms = (time.time() - start) * 1000
            raw = resp.read().decode()
            total_ms = (time.time() - start) * 1000
    except Exception as e:
        print(f"\n  ✗ Connection failed: {e}")
        sys.exit(1)

    data = json.loads(raw)
    response_text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    returned_model = data.get("model", "")
    usage = data.get("usage", {})
    total_tokens = usage.get("total_tokens", len(response_text) // 4)

    audit_result = run_audit(
        claimed_model=model,
        response_text=response_text,
        returned_model=returned_model,
        ttfb_ms=ttfb_ms,
        total_ms=total_ms,
        total_tokens=total_tokens,
    )

    # Display results
    status = "✓ PASS" if not audit_result.is_suspicious else "⚠ SUSPICIOUS"
    color = "\033[32m" if not audit_result.is_suspicious else "\033[33m"
    reset = "\033[0m"

    print(f"\n  {color}{status}{reset}")
    print(f"  Trust Score: {audit_result.trust_score}/100")
    print(f"  TTFB: {ttfb_ms:.0f}ms | Total: {total_ms:.0f}ms")
    print(f"  Returned Model: {returned_model or 'not disclosed'}")
    if audit_result.flags:
        print(f"  Flags: {', '.join(audit_result.flags)}")
    print()

    # Report to ranking if enabled
    cfg = Config.get()
    if cfg.report:
        from .core import _submit_to_ranking
        cfg.providers = [{"base_url": base_url}]
        _submit_to_ranking(cfg, model, returned_model, audit_result, ttfb_ms, total_ms, total_tokens)


if __name__ == "__main__":
    main()
