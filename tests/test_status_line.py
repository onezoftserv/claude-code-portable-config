import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "hooks" / "common"))
from status_line import format_status_line  # noqa: E402

CASES = [
    (
        {"model": {"display_name": "Sonnet 5"}, "cost": {"total_cost_usd": 0.42}, "workspace": {"current_dir": "/home/x/draft"}},
        "Sonnet 5 | $0.42 | draft",
    ),
    ({}, "? | ? | ?"),
    ({"model": None, "cost": None, "workspace": None}, "? | ? | ?"),
    ({"model": {}, "cost": {}, "workspace": {}}, "? | ? | ?"),
    ({"model": {"display_name": None}}, "? | ? | ?"),
    ({"cost": {"total_cost_usd": "not-a-number"}}, "? | ? | ?"),
    ({"workspace": {"current_dir": ""}}, "? | ? | ?"),
    ({"workspace": {"current_dir": "/a/b/c"}}, "? | ? | c"),
]


@pytest.mark.parametrize("data,expected", CASES)
def test_format_status_line(data, expected):
    assert format_status_line(data) == expected


def test_zero_cost_is_not_treated_as_falsy():
    # 0 is a valid cost (a fresh session) and must not print as "?" just
    # because `0` is falsy in a naive `or "?"` check.
    assert format_status_line({"cost": {"total_cost_usd": 0}}) == "? | $0.00 | ?"
