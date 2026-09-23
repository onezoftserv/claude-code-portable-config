#!/usr/bin/env python3
"""Poll a PR for new/updated review and issue comments for a bounded window,
printing each one as a single line the moment it's found — so `Monitor`
(watching this as a background process) surfaces them live instead of only
at the end of the window. CodeRabbit edits its summary comment in place, so
new items are deduped by (endpoint, id, updated_at): an edit changes
updated_at and is reported again on purpose.

Usage: python pr_watch.py <pr-number> [--minutes 8] [--interval 45]
"""
import argparse
import json
import subprocess
import sys
import time

ENDPOINT_TEMPLATES = ["pulls/{n}/comments", "pulls/{n}/reviews", "issues/{n}/comments"]


def gh_json(path: str) -> list:
    result = subprocess.run(
        ["gh", "api", "--paginate", path],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        print(f"[pr_watch] gh api {path} failed: {result.stderr.strip()}", file=sys.stderr)
        return []
    text = result.stdout.strip()
    if not text:
        return []
    # --paginate concatenates JSON arrays back to back with no separator.
    items = []
    decoder = json.JSONDecoder()
    idx = 0
    while idx < len(text):
        obj, idx = decoder.raw_decode(text, idx)
        items.extend(obj if isinstance(obj, list) else [obj])
        while idx < len(text) and text[idx] in " \n\t\r":
            idx += 1
    return items


def repo_slug() -> str:
    result = subprocess.run(
        ["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
        capture_output=True, text=True, timeout=15,
    )
    return result.stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pr_number")
    parser.add_argument("--minutes", type=float, default=8)
    parser.add_argument("--interval", type=float, default=45)
    args = parser.parse_args()

    slug = repo_slug()
    if not slug:
        print("[pr_watch] could not resolve repo (gh repo view failed)", file=sys.stderr)
        sys.exit(1)

    seen = set()
    deadline = time.time() + args.minutes * 60
    print(f"[pr_watch] watching {slug}#{args.pr_number} for {args.minutes:.0f} min, every {args.interval:.0f}s")

    while time.time() < deadline:
        for template in ENDPOINT_TEMPLATES:
            path = f"repos/{slug}/{template.format(n=args.pr_number)}"
            for item in gh_json(path):
                key = (path, item.get("id"), item.get("updated_at"))
                if key in seen:
                    continue
                seen.add(key)
                author = (item.get("user") or {}).get("login", "?")
                body = (item.get("body") or "").strip().replace("\n", " ")
                if len(body) > 240:
                    body = body[:240] + "..."
                print(f"[pr_watch] {author}: {body}")
        time.sleep(args.interval)

    print("[pr_watch] done watching")


if __name__ == "__main__":
    main()
