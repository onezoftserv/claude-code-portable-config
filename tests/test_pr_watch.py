import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import pr_watch  # noqa: E402


def test_parses_single_json_array():
    assert pr_watch.parse_concatenated_json('[{"id": 1}, {"id": 2}]') == [{"id": 1}, {"id": 2}]


def test_parses_paginated_arrays_with_no_separator():
    # gh api --paginate emits one array per page, concatenated with no
    # separator between them -- this is the shape a real multi-page
    # response actually has.
    text = '[{"id": 1}]' + '[{"id": 2}, {"id": 3}]'
    assert pr_watch.parse_concatenated_json(text) == [{"id": 1}, {"id": 2}, {"id": 3}]


def test_parses_arrays_separated_by_whitespace():
    text = '[{"id": 1}]\n[{"id": 2}]'
    assert pr_watch.parse_concatenated_json(text) == [{"id": 1}, {"id": 2}]


def test_empty_input_returns_empty_list():
    assert pr_watch.parse_concatenated_json("") == []
    assert pr_watch.parse_concatenated_json("   \n  ") == []


def test_a_bare_object_is_wrapped_in_a_list():
    assert pr_watch.parse_concatenated_json('{"id": 1}') == [{"id": 1}]


def test_malformed_json_raises():
    with pytest.raises(json.JSONDecodeError):
        pr_watch.parse_concatenated_json("not json")
