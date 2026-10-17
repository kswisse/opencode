import io
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


def test_call_planner_parses_gemini_answer(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    payload = json.dumps({"candidates": [{"content": {"parts": [{"text": "HELLO"}]}}]}).encode()

    class FakeResp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(loop.urllib.request, "urlopen", lambda req, timeout=60: FakeResp(payload))
    cfg = {"planner": {"base_url": "https://x/y", "model": "m", "api_key_env": "GEMINI_API_KEY"}}
    assert loop.call_planner(cfg, "prompt") == "HELLO"


def test_call_planner_requires_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    cfg = {"planner": {"base_url": "https://x/y", "model": "m", "api_key_env": "GEMINI_API_KEY"}}
    with pytest.raises(SystemExit):
        loop.call_planner(cfg, "prompt")
