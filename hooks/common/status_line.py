#!/usr/bin/env python3
"""statusLine command. Prints one short line to stdout.

Field names below are the commonly documented statusLine payload shape.
If the line looks wrong, dump stdin once to check. Every field lookup is
None-guarded: a null field prints "?" instead of crashing.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _util import read_hook_input


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    data = read_hook_input()
    model = (data.get("model") or {}).get("display_name") or "?"
    cost = (data.get("cost") or {}).get("total_cost_usd")
    cost_str = f"${cost:.2f}" if isinstance(cost, (int, float)) else "?"
    cwd = (data.get("workspace") or {}).get("current_dir") or ""
    dirname = Path(cwd).name if cwd else "?"
    print(f"{model} | {cost_str} | {dirname}")


if __name__ == "__main__":
    main()
