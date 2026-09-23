#!/usr/bin/env python3
"""statusLine command. Prints one short line to stdout.

Field names below are the commonly documented statusLine payload shape.
If the line looks wrong, dump stdin once to check: this script never
crashes on missing fields, it just prints "?" for them.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _util import read_hook_input


def main() -> None:
    data = read_hook_input()
    model = data.get("model", {}).get("display_name", "?")
    cost = data.get("cost", {}).get("total_cost_usd")
    cost_str = f"${cost:.2f}" if isinstance(cost, (int, float)) else "?"
    cwd = data.get("workspace", {}).get("current_dir", "")
    dirname = Path(cwd).name if cwd else "?"
    print(f"{model} | {cost_str} | {dirname}")


if __name__ == "__main__":
    main()
