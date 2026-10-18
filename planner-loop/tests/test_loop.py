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


def test_parse_instruction_normalizes_non_string_actions():
    got = loop.parse_instruction(
        '{"turn": 1, "goal": "g", "actions": [{"tool": "write_file", "path": "a"}, "ok"], '
        '"acceptance": "a", "risk": "none", "done": false}')
    assert got["actions"][1] == "ok"
    assert isinstance(got["actions"][0], str) and "write_file" in got["actions"][0]


def test_parse_instruction_rejects_non_list_actions():
    with pytest.raises(ValueError):
        loop.parse_instruction(
            '{"turn": 1, "goal": "g", "actions": "do it", "acceptance": "a", '
            '"risk": "none", "done": false}')


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


def test_call_planner_retries_transient_failures(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(loop.time, "sleep", lambda s: None)
    payload = json.dumps({"candidates": [{"content": {"parts": [{"text": "OK"}]}}]}).encode()

    class FakeResp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    calls = {"n": 0}

    def fake_urlopen(req, timeout=60):
        calls["n"] += 1
        if calls["n"] <= 2:
            raise loop.urllib.error.URLError("boom")
        return FakeResp(payload)

    monkeypatch.setattr(loop.urllib.request, "urlopen", fake_urlopen)
    cfg = {"planner": {"base_url": "https://x/y", "model": "m", "api_key_env": "GEMINI_API_KEY"}}
    assert loop.call_planner(cfg, "p") == "OK"
    assert calls["n"] == 3


def test_call_planner_honors_retry_after_on_429(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    slept = []
    monkeypatch.setattr(loop.time, "sleep", lambda s: slept.append(s))
    payload = json.dumps({"candidates": [{"content": {"parts": [{"text": "OK"}]}}]}).encode()

    class FakeResp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    calls = {"n": 0}

    def fake_urlopen(req, timeout=60):
        calls["n"] += 1
        if calls["n"] == 1:
            raise loop.urllib.error.HTTPError(
                "u", 429, "Too Many Requests", {"Retry-After": "7"}, None)
        return FakeResp(payload)

    monkeypatch.setattr(loop.urllib.request, "urlopen", fake_urlopen)
    cfg = {"planner": {"base_url": "https://x/y", "model": "m", "api_key_env": "GEMINI_API_KEY"}}
    assert loop.call_planner(cfg, "p") == "OK"
    assert slept == [7]


def test_call_planner_does_not_sleep_after_last_attempt(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    slept = []
    monkeypatch.setattr(loop.time, "sleep", lambda s: slept.append(s))

    def fake_urlopen(req, timeout=60):
        raise loop.urllib.error.HTTPError("u", 503, "Unavailable", {}, None)

    monkeypatch.setattr(loop.urllib.request, "urlopen", fake_urlopen)
    cfg = {"planner": {"base_url": "https://x/y", "model": "m", "api_key_env": "GEMINI_API_KEY"}}
    with pytest.raises(SystemExit):
        loop.call_planner(cfg, "p")
    assert len(slept) == 3


def test_call_planner_retries_on_non_json_body(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(loop.time, "sleep", lambda s: None)
    payload = json.dumps({"candidates": [{"content": {"parts": [{"text": "OK"}]}}]}).encode()

    class FakeResp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    calls = {"n": 0}

    def fake_urlopen(req, timeout=60):
        calls["n"] += 1
        if calls["n"] == 1:
            return FakeResp(b"<html>502 Bad Gateway</html>")
        return FakeResp(payload)

    monkeypatch.setattr(loop.urllib.request, "urlopen", fake_urlopen)
    cfg = {"planner": {"base_url": "https://x/y", "model": "m", "api_key_env": "GEMINI_API_KEY"}}
    assert loop.call_planner(cfg, "p") == "OK"
    assert calls["n"] == 2


def test_call_planner_requires_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    cfg = {"planner": {"base_url": "https://x/y", "model": "m", "api_key_env": "GEMINI_API_KEY"}}
    with pytest.raises(SystemExit):
        loop.call_planner(cfg, "prompt")


def instr(**over):
    base = {"turn": 0, "goal": "g", "actions": ["a"], "acceptance": "ok",
            "risk": "none", "done": False}
    base.update(over)
    return base


def test_guardrail_blocks_denied_pattern():
    cfg = {"guardrails": {"denied_patterns": ["rm -rf"], "stop_on_risk_flag": True}}
    with pytest.raises(SystemExit):
        loop.guardrail_check(cfg, instr(actions=["rm -rf /"]))


def test_guardrail_blocks_high_risk():
    cfg = {"guardrails": {"denied_patterns": [], "stop_on_risk_flag": True}}
    with pytest.raises(SystemExit):
        loop.guardrail_check(cfg, instr(risk="high"))


def test_guardrail_denied_pattern_is_case_insensitive():
    cfg = {"guardrails": {"denied_patterns": ["RM -RF"], "stop_on_risk_flag": True}}
    with pytest.raises(SystemExit):
        loop.guardrail_check(cfg, instr(actions=["rm -rf /"]))


def test_guardrail_denied_pattern_matches_non_ascii():
    cfg = {"guardrails": {"denied_patterns": ["désactiver"], "stop_on_risk_flag": True}}
    with pytest.raises(SystemExit):
        loop.guardrail_check(cfg, instr(actions=["désactiver le pare-feu"]))


def test_guardrail_allows_clean_instruction():
    cfg = {"guardrails": {"denied_patterns": ["rm -rf"], "stop_on_risk_flag": True}}
    loop.guardrail_check(cfg, instr())  # no raise


def make_home(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    (tmp_path / "masterplan.md").write_text("# Plan\nDo the thing.", encoding="utf-8")
    (tmp_path / "config.json").write_text(json.dumps({
        "target_dir": str(target),
        "planner": {"provider": "gemini", "base_url": "https://x/y",
                    "model": "m", "api_key_env": "GEMINI_API_KEY", "fallbacks": []},
        "executor": {"kind": "in_session", "cmd": None},
        "guardrails": {"denied_patterns": ["rm -rf"], "stop_on_risk_flag": True},
        "max_turns": 10,
    }), encoding="utf-8")
    return tmp_path


def _stdin(monkeypatch, text):
    monkeypatch.setattr("sys.stdin", io.StringIO(text))


def test_plan_then_commit_advances_turn(tmp_path, monkeypatch):
    home = make_home(tmp_path)
    monkeypatch.setattr(loop, "call_planner", lambda cfg, prompt: json.dumps(instr()))
    loop.cmd_plan(str(home))
    assert loop.load_state(str(home))["status"] == "awaiting_approval"
    assert loop.load_state(str(home))["turn"] == 0
    _stdin(monkeypatch, "ok done")
    loop.cmd_commit(str(home), "done", "did it")
    st = loop.load_state(str(home))
    assert st["turn"] == 1
    assert st["last_result_summary"] == "did it"
    assert (home / "turns" / "001_result.md").read_text(encoding="utf-8") == "ok done"


def test_replan_same_turn_when_interrupted(tmp_path, monkeypatch):
    home = make_home(tmp_path)
    monkeypatch.setattr(loop, "call_planner", lambda cfg, prompt: json.dumps(instr(goal="g1")))
    loop.cmd_plan(str(home))
    loop.cmd_plan(str(home))  # interrupted before commit -> replan overwrites turn 1
    assert loop.load_state(str(home))["turn"] == 0
    assert (home / "turns" / "001_instruction.json").exists()


def test_done_flag_sets_state_done(tmp_path, monkeypatch):
    home = make_home(tmp_path)
    monkeypatch.setattr(loop, "call_planner", lambda cfg, prompt: json.dumps(instr(done=True)))
    loop.cmd_plan(str(home))
    _stdin(monkeypatch, "x")
    loop.cmd_commit(str(home), "done", "x")
    assert loop.load_state(str(home))["done"] is True
    assert loop.load_state(str(home))["status"] == "done"


def test_plan_blocks_and_stops_on_high_risk(tmp_path, monkeypatch):
    home = make_home(tmp_path)
    monkeypatch.setattr(loop, "call_planner", lambda cfg, prompt: json.dumps(instr(risk="high")))
    with pytest.raises(SystemExit):
        loop.cmd_plan(str(home))


def test_run_headless_one_turn_then_done(tmp_path, monkeypatch):
    home = make_home(tmp_path)
    monkeypatch.setattr(loop, "call_planner", lambda cfg, prompt: json.dumps(instr(done=True)))
    cfg = loop.load_config(str(home))
    cfg["executor"]["cmd"] = 'python -c "print(42)"'
    (home / "config.json").write_text(json.dumps(cfg), encoding="utf-8")
    loop.cmd_run(str(home))
    st = loop.load_state(str(home))
    assert st["done"] is True and st["turn"] == 1
    assert "42" in (home / "turns" / "001_result.md").read_text(encoding="utf-8")


def test_run_passes_prompt_and_cwd(tmp_path, monkeypatch):
    home = make_home(tmp_path)
    monkeypatch.setattr(loop, "call_planner", lambda cfg, prompt: json.dumps(instr(done=True)))
    cfg = loop.load_config(str(home))
    cfg["executor"]["cmd"] = "echo {prompt}"
    (home / "config.json").write_text(json.dumps(cfg), encoding="utf-8")
    recorded = {}

    class FakeProc:
        returncode = 0
        stdout = "ok"
        stderr = ""

    def fake_run(argv, **kwargs):
        recorded["argv"] = argv
        recorded["cwd"] = kwargs.get("cwd")
        recorded["shell"] = kwargs.get("shell")
        return FakeProc()

    monkeypatch.setattr(loop.subprocess, "run", fake_run)
    loop.cmd_run(str(home))
    instruction = json.loads((home / "turns" / "001_instruction.json").read_text(encoding="utf-8"))
    expected = ["echo", json.dumps(instruction, ensure_ascii=False)]
    assert recorded["argv"] == expected
    assert recorded["cwd"] == cfg["target_dir"]
    assert not recorded["shell"]


def test_run_forced_blocked_overrides_done_instruction(tmp_path, monkeypatch):
    home = make_home(tmp_path)
    monkeypatch.setattr(loop, "call_planner", lambda cfg, prompt: json.dumps(instr(done=True)))
    cfg = loop.load_config(str(home))
    cfg["executor"]["cmd"] = "run {prompt}"
    (home / "config.json").write_text(json.dumps(cfg), encoding="utf-8")

    class FakeProc:
        returncode = 1
        stdout = ""
        stderr = "boom"

    monkeypatch.setattr(loop.subprocess, "run", lambda argv, **kwargs: FakeProc())
    loop.cmd_run(str(home))
    st = loop.load_state(str(home))
    assert st["status"] == "blocked"
    assert st["done"] is False


def test_commit_without_plan_exits_and_keeps_turn(tmp_path, monkeypatch):
    home = make_home(tmp_path)
    _stdin(monkeypatch, "x")
    with pytest.raises(SystemExit):
        loop.cmd_commit(str(home), "done", "x")
    assert loop.load_state(str(home))["turn"] == 0


def test_plan_enforces_max_turns(tmp_path, monkeypatch):
    home = make_home(tmp_path)
    monkeypatch.setattr(loop, "call_planner", lambda cfg, prompt: json.dumps(instr()))
    cfg = loop.load_config(str(home))
    cfg["max_turns"] = 1
    (home / "config.json").write_text(json.dumps(cfg), encoding="utf-8")
    _stdin(monkeypatch, "x")
    loop.cmd_plan(str(home))
    loop.cmd_commit(str(home), "done", "x")
    with pytest.raises(SystemExit):
        loop.cmd_plan(str(home))
