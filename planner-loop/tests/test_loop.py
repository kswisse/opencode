import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import loop


def test_atomic_write_leaves_no_tmp(tmp_path):
    p = tmp_path / "s.json"
    loop.atomic_write_json(str(p), {"turn": 0})
    assert json.loads(p.read_text(encoding="utf-8")) == {"turn": 0}
    assert not os.path.exists(str(p) + ".tmp")


def test_load_state_defaults_when_missing(tmp_path):
    st = loop.load_state(str(tmp_path))
    assert st["turn"] == 0 and st["done"] is False and st["status"] == "new"


def test_parse_instruction_plain_json():
    got = loop.parse_instruction(
        '{"turn": 1, "goal": "g", "actions": [], "acceptance": "a", "risk": "none", "done": false}')
    assert got["turn"] == 1 and got["goal"] == "g"


def test_parse_instruction_strips_fences():
    got = loop.parse_instruction(
        '```json\n{"turn": 2, "goal": "g", "actions": ["x"], "acceptance": "a", '
        '"risk": "low", "done": false}\n```')
    assert got["turn"] == 2 and got["actions"] == ["x"]


def test_parse_instruction_rejects_missing_key():
    with pytest.raises(ValueError):
        loop.parse_instruction('{"turn": 1}')


def test_build_prompt_contains_sections():
    p = loop.build_prompt("# Plan", {"turn": 0}, "prev")
    assert "MASTERPLAN" in p and "STATE" in p and "LAST RESULT" in p and "prev" in p
