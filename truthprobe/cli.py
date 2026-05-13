"""
TruthProbe SDK — CLI Entry Point
Usage:
    truthprobe report          Full audit report
    truthprobe report --week   Weekly report with trends
    truthprobe balance         Check all provider balances
    truthprobe score           Current trust score
"""

import sys

from .config import Config
from .core import report, balance, score


def main():
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help", "help"):
        print("""TruthProbe CLI — AI API Trust & Cost Transparency

Commands:
    truthprobe report          Full audit report (today)
    truthprobe report --week   Weekly report with 7-day trends
    truthprobe balance         Check provider balances
    truthprobe score           Current trust score

Options:
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

    cmd = args[0] if args else "report"

    if cmd == "report":
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


if __name__ == "__main__":
    main()
