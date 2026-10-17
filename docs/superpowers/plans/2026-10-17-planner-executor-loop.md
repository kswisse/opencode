# Planner ↔ Executor Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a stdlib-only Python driver that runs an automated planner↔executor loop over a masterplan, with human approval each turn and crash-safe on-disk state.

**Architecture:** One file `loop.py` with three subcommands. `plan` calls a free-API planner (Gemini REST) and writes the next instruction JSON; `commit` records the executor's result and bumps state atomically; `run` chains both headlessly for an optional CLI executor. All loop state lives on disk (`state.json`, `turns/`), so any crash resumes from the last committed turn.

**Tech Stack:** Python 3.12 (stdlib only), pytest for tests, Gemini `generateContent` REST via `urllib`.

## Global Constraints

- Python 3.12, **stdlib only** at runtime — no third-party imports in `loop.py`.
- Tests run with `python -m pytest -q` from `C:\Opencode\planner-loop`.
- Shell is **Windows PowerShell 5.1** (no `&&`; use `;` and `if ($?)`).
- Secrets never in files: the planner key is read from env `GEMINI_API_KEY`.
- Every state write is atomic: write `<path>.tmp` then `os.replace`.
- All paths under `C:\Opencode\planner-loop\`.

---

### Task 1: Scaffold + JSON/state helpers

**Files:**
- Create: `C:\Opencode\planner-loop\loop.py`
- Create: `C:\Opencode\planner-loop\tests\test_loop.py`

**Interfaces:**
- Produces: `loop.atomic_write_json(path, obj)`, `loop.load_json(path, default=None)`, `loop.read_text(path, default="")`, `loop.load_state(home) -> dict`, `loop.save_state(home, state)`, `loop.load_config(home) -> dict`, `loop.append_event(home, line)`, `loop._now() -> str`.

- [ ] **Step 1: Write the failing test**

```python
# C:\Opencode\planner-loop\tests\test_loop.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest -q tests/test_loop.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'loop'`

- [ ] **Step 3: Write minimal implementation**

```python
# C:\Opencode\planner-loop\loop.py
#!/usr/bin/env python3
"""Planner <-> Executor loop driver (stdlib only).

Home layout (--home, default: the dir containing this script):
    masterplan.md   human-owned plan
    config.json     planner endpoint, target_dir, guardrails
    state.json      durable pointer (written atomically)
    turns/NNN_instruction.json, turns/NNN_result.md
    events.log      human-readable audit trail

Commands: plan | commit | run
"""
import argparse
import datetime
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REQUIRED_INSTRUCTION_KEYS = ("turn", "goal", "actions", "acceptance", "risk", "done")
PLANNER_SYSTEM = (
    "You are the PLANNER in a planner/executor loop run by a human. "
    "You receive a MASTERPLAN, the current STATE, and the LAST RESULT. "
    "Reply with exactly ONE JSON object and nothing else. Keys: "
    '{"turn": <int>, "goal": "<one sentence>", "actions": ["<concrete action>", ...], '
    '"acceptance": "<how to verify>", "risk": "none|low|high", "done": <bool>}. '
    "Do not include prose or markdown fences."
)


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def read_text(path, default=""):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return f.read()


def load_json(path, default=None):
    if not os.path.exists(path):
        return default
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def atomic_write_json(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def append_event(home, line):
    with open(os.path.join(home, "events.log"), "a", encoding="utf-8") as f:
        f.write("%s %s\n" % (_now(), line))


def load_config(home):
    cfg = load_json(os.path.join(home, "config.json"))
    if cfg is None:
        raise SystemExit("config.json not found in %s" % home)
    target = cfg.get("target_dir")
    if not target or not os.path.isdir(target):
        raise SystemExit("target_dir missing or not a directory: %r" % target)
    return cfg


def load_state(home):
    state = load_json(os.path.join(home, "state.json"))
    if state is None:
        state = {
            "run_id": _now().replace(":", "-"),
            "turn": 0,
            "status": "new",
            "last_result_summary": "",
            "open_tasks": [],
            "done": False,
            "updated_at": _now(),
        }
    return state


def save_state(home, state):
    state["updated_at"] = _now()
    atomic_write_json(os.path.join(home, "state.json"), state)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest -q tests/test_loop.py`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```powershell
git add planner-loop/loop.py planner-loop/tests/test_loop.py
git commit -m "feat(planner-loop): scaffold driver + json/state helpers"
```

---

### Task 2: Planner prompt + instruction parsing

**Files:**
- Modify: `C:\Opencode\planner-loop\loop.py` (append functions)
- Modify: `C:\Opencode\planner-loop\tests\test_loop.py` (append tests)

**Interfaces:**
- Consumes: `REQUIRED_INSTRUCTION_KEYS`, `PLANNER_SYSTEM` (Task 1)
- Produces: `loop.build_prompt(masterplan, state, last_result) -> str`, `loop.parse_instruction(text) -> dict`

- [ ] **Step 1: Write the failing tests**

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest -q tests/test_loop.py -k parse_instruction`
Expected: FAIL — `AttributeError: module 'loop' has no attribute 'parse_instruction'`

- [ ] **Step 3: Write minimal implementation (append to loop.py)**

```python
def build_prompt(masterplan, state, last_result):
    return "\n\n".join([
        PLANNER_SYSTEM,
        "=== MASTERPLAN ===\n" + masterplan,
        "=== STATE ===\n" + json.dumps(state, ensure_ascii=False),
        "=== LAST RESULT ===\n" + (last_result or "(none)"),
    ])


def parse_instruction(text):
    s = text.strip()
    if s.startswith("```"):
        s = s.split("```")[1]
        if s[:4].lower() == "json":
            s = s[4:]
        s = s.strip()
    i, j = s.find("{"), s.rfind("}")
    if i < 0 or j < 0:
        raise ValueError("no JSON object found in planner reply")
    obj = json.loads(s[i:j + 1])
    for key in REQUIRED_INSTRUCTION_KEYS:
        if key not in obj:
            raise ValueError("instruction missing key: %s" % key)
    return obj
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest -q tests/test_loop.py`
Expected: PASS (6 passed)

- [ ] **Step 5: Commit**

```powershell
git add planner-loop/loop.py planner-loop/tests/test_loop.py
git commit -m "feat(planner-loop): planner prompt builder + instruction parser"
```

---

### Task 3: Planner API call (Gemini REST + backoff)

**Files:**
- Modify: `C:\Opencode\planner-loop\loop.py` (append function)
- Modify: `C:\Opencode\planner-loop\tests\test_loop.py` (append test)

**Interfaces:**
- Consumes: `cfg["planner"]` with keys `base_url`, `model`, `api_key_env`
- Produces: `loop.call_planner(cfg, prompt) -> str` (the model's raw reply text)

- [ ] **Step 1: Write the failing test**

```python
import io


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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest -q tests/test_loop.py -k call_planner`
Expected: FAIL — `AttributeError: module 'loop' has no attribute 'call_planner'`

- [ ] **Step 3: Write minimal implementation (append to loop.py)**

```python
def call_planner(cfg, prompt):
    planner = cfg["planner"]
    key = os.environ.get(planner.get("api_key_env", ""), "")
    if not key:
        raise SystemExit("planner api key env %r is empty" % planner.get("api_key_env"))
    url = "%s/models/%s:generateContent?key=%s" % (
        planner["base_url"].rstrip("/"), planner["model"], key)
    body = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"})
    last = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.load(resp)
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (urllib.error.URLError, urllib.error.HTTPError, KeyError, IndexError) as exc:
            last = exc
            time.sleep(2 ** attempt)
    raise SystemExit("planner call failed after retries: %r" % last)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest -q tests/test_loop.py`
Expected: PASS (8 passed)

- [ ] **Step 5: Commit**

```powershell
git add planner-loop/loop.py planner-loop/tests/test_loop.py
git commit -m "feat(planner-loop): gemini planner call with retry backoff"
```

---

### Task 4: Guardrails

**Files:**
- Modify: `C:\Opencode\planner-loop\loop.py` (append function)
- Modify: `C:\Opencode\planner-loop\tests\test_loop.py` (append tests + helper)

**Interfaces:**
- Consumes: `cfg["guardrails"]` with keys `denied_patterns` (list[str]), `stop_on_risk_flag` (bool)
- Produces: `loop.guardrail_check(cfg, instruction) -> None` (raises `SystemExit` on violation)

- [ ] **Step 1: Write the failing tests**

```python
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


def test_guardrail_allows_clean_instruction():
    cfg = {"guardrails": {"denied_patterns": ["rm -rf"], "stop_on_risk_flag": True}}
    loop.guardrail_check(cfg, instr())  # no raise
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest -q tests/test_loop.py -k guardrail`
Expected: FAIL — `AttributeError: module 'loop' has no attribute 'guardrail_check'`

- [ ] **Step 3: Write minimal implementation (append to loop.py)**

```python
def guardrail_check(cfg, instruction):
    g = cfg.get("guardrails", {})
    blob = json.dumps(instruction).lower()
    for pattern in g.get("denied_patterns", []):
        if pattern.lower() in blob:
            raise SystemExit("GUARDRAIL: instruction matches denied pattern %r" % pattern)
    if g.get("stop_on_risk_flag", True) and instruction.get("risk") == "high":
        raise SystemExit("GUARDRAIL: instruction flagged risk=high; human must handle")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest -q tests/test_loop.py`
Expected: PASS (11 passed)

- [ ] **Step 5: Commit**

```powershell
git add planner-loop/loop.py planner-loop/tests/test_loop.py
git commit -m "feat(planner-loop): guardrail checks for denied patterns and risk"
```

---

### Task 5: plan / commit state machine

**Files:**
- Modify: `C:\Opencode\planner-loop\loop.py` (append functions)
- Modify: `C:\Opencode\planner-loop\tests\test_loop.py` (append tests + `make_home` helper)

**Interfaces:**
- Consumes: `load_config`, `load_state`, `save_state`, `build_prompt`, `parse_instruction`, `call_planner`, `guardrail_check`, `load_json`, `atomic_write_json`, `append_event`
- Produces: `loop.cmd_plan(home)`, `loop.commit_result(home, turn, body, status_name, summary)`, `loop.cmd_commit(home, status_name, summary)`, `loop._instruction_path(home, turn)`, `loop._result_path(home, turn)`

- [ ] **Step 1: Write the failing tests**

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest -q tests/test_loop.py -k "plan or commit"`
Expected: FAIL — `AttributeError: module 'loop' has no attribute 'cmd_plan'`

- [ ] **Step 3: Write minimal implementation (append to loop.py)**

```python
def _instruction_path(home, turn):
    return os.path.join(home, "turns", "%03d_instruction.json" % turn)


def _result_path(home, turn):
    return os.path.join(home, "turns", "%03d_result.md" % turn)


def cmd_plan(home):
    cfg = load_config(home)
    state = load_state(home)
    masterplan = read_text(os.path.join(home, "masterplan.md"), default="(empty)")
    instruction = None
    for _ in range(2):
        raw = call_planner(
            cfg, build_prompt(masterplan, state, state.get("last_result_summary")))
        try:
            instruction = parse_instruction(raw)
            break
        except ValueError:
            instruction = None
    if instruction is None:
        raise SystemExit("planner returned an invalid instruction twice; stopping")
    guardrail_check(cfg, instruction)
    turn = state["turn"] + 1
    instruction["turn"] = turn
    os.makedirs(os.path.join(home, "turns"), exist_ok=True)
    atomic_write_json(_instruction_path(home, turn), instruction)
    state["status"] = "awaiting_approval"
    save_state(home, state)
    append_event(home, "plan turn=%d goal=%s" % (turn, instruction.get("goal", "")))
    print(json.dumps(instruction, ensure_ascii=False, indent=2))


def commit_result(home, turn, body, status_name, summary):
    os.makedirs(os.path.join(home, "turns"), exist_ok=True)
    with open(_result_path(home, turn), "w", encoding="utf-8") as f:
        f.write(body)
    instruction = load_json(_instruction_path(home, turn), default={})
    state = load_state(home)
    state["turn"] = turn
    state["last_result_summary"] = summary
    if instruction.get("done"):
        state["done"] = True
        state["status"] = "done"
    elif status_name == "blocked":
        state["status"] = "blocked"
    else:
        state["status"] = "awaiting_instruction"
    save_state(home, state)
    append_event(home, "commit turn=%d status=%s" % (turn, status_name))


def cmd_commit(home, status_name, summary):
    state = load_state(home)
    turn = state["turn"] + 1
    commit_result(home, turn, sys.stdin.read(), status_name, summary)
    print("committed turn %d" % turn)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest -q tests/test_loop.py`
Expected: PASS (15 passed)

- [ ] **Step 5: Commit**

```powershell
git add planner-loop/loop.py planner-loop/tests/test_loop.py
git commit -m "feat(planner-loop): plan/commit state machine with atomic checkpoint"
```

---

### Task 6: Headless `run` + CLI dispatch

**Files:**
- Modify: `C:\Opencode\planner-loop\loop.py` (append `cmd_run` + `main`)
- Modify: `C:\Opencode\planner-loop\tests\test_loop.py` (append test)

**Interfaces:**
- Consumes: `cfg["executor"]["cmd"]` (str with `{prompt}` placeholder), `cfg["max_turns"]`, `cmd_plan`, `commit_result`
- Produces: `loop.cmd_run(home)`, `loop.main(argv=None)`

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest -q tests/test_loop.py -k run_headless`
Expected: FAIL — `AttributeError: module 'loop' has no attribute 'cmd_run'`

- [ ] **Step 3: Write minimal implementation (append to loop.py)**

```python
def cmd_run(home):
    cfg = load_config(home)
    executor_cmd = (cfg.get("executor") or {}).get("cmd")
    if not executor_cmd:
        raise SystemExit("executor.cmd is required for headless run")
    max_turns = cfg.get("max_turns", 50)
    while True:
        state = load_state(home)
        if state.get("done"):
            print("done after %d turns" % state["turn"])
            return
        if state["turn"] >= max_turns:
            print("stopped at max_turns=%d" % max_turns)
            return
        cmd_plan(home)
        turn = load_state(home)["turn"] + 1
        instruction = load_json(_instruction_path(home, turn))
        prompt = json.dumps(instruction, ensure_ascii=False)
        proc = subprocess.run(
            executor_cmd.replace("{prompt}", prompt),
            shell=True, cwd=cfg["target_dir"], capture_output=True, text=True)
        body = proc.stdout + ("\n[stderr]\n" + proc.stderr if proc.stderr else "")
        status_name = "done" if proc.returncode == 0 else "blocked"
        commit_result(home, turn, body, status_name, body.strip()[:200])


def main(argv=None):
    parser = argparse.ArgumentParser(description="Planner <-> Executor loop driver")
    parser.add_argument("command", choices=["plan", "commit", "run"])
    parser.add_argument("--home", default=HERE)
    parser.add_argument("--status", default="done")
    parser.add_argument("--summary", default="")
    args = parser.parse_args(argv)
    if args.command == "plan":
        cmd_plan(args.home)
    elif args.command == "commit":
        cmd_commit(args.home, args.status, args.summary)
    elif args.command == "run":
        cmd_run(args.home)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest -q tests/test_loop.py`
Expected: PASS (16 passed)

- [ ] **Step 5: Commit**

```powershell
git add planner-loop/loop.py planner-loop/tests/test_loop.py
git commit -m "feat(planner-loop): headless run mode + CLI dispatch"
```

---

### Task 7: Example config, masterplan template, and README

**Files:**
- Create: `C:\Opencode\planner-loop\config.example.json`
- Create: `C:\Opencode\planner-loop\masterplan.example.md`
- Create: `C:\Opencode\planner-loop\README.md`

**Interfaces:**
- Consumes: everything from Tasks 1–6
- Produces: an at-a-glance usage doc; no code

- [ ] **Step 1: Write the example config**

```json
// C:\Opencode\planner-loop\config.example.json  (copy to config.json and edit)
{
  "target_dir": "C:/Opencode/<your-project>",
  "planner": {
    "provider": "gemini",
    "base_url": "https://generativelanguage.googleapis.com/v1beta",
    "model": "gemini-2.5-flash",
    "api_key_env": "GEMINI_API_KEY",
    "fallbacks": []
  },
  "executor": { "kind": "in_session", "cmd": null },
  "guardrails": {
    "allowed_roots": ["C:/Opencode/<your-project>"],
    "denied_patterns": [
      "rm -rf", "rmdir /s", "format ", "mkfs", "shutdown",
      "git push --force", "git reset --hard", "Remove-Item -Recurse -Force C:"
    ],
    "stop_on_risk_flag": true
  },
  "max_turns": 50
}
```

- [ ] **Step 2: Write the masterplan template**

```markdown
<!-- C:\Opencode\planner-loop\masterplan.example.md -->
# Masterplan: <goal in one line>

## Done looks like
- <observable end state>

## Constraints
- <what must not change / must hold>

## Steps (guidance, not gospel)
1. <first thing>
2. <next thing>
```

- [ ] **Step 3: Write the README**

```markdown
<!-- C:\Opencode\planner-loop\README.md -->
# Planner ↔ Executor Loop

A planner LLM (Gemini free tier) and an executor take turns over a masterplan,
one human-approved turn at a time. All state is on disk, so a crash at any
point resumes from the last committed turn.

## Setup
1. `copy config.example.json config.json`, then edit `target_dir` and `guardrails`.
2. Write your plan into `masterplan.md` (see `masterplan.example.md`).
3. Ensure the env var named in `planner.api_key_env` (default `GEMINI_API_KEY`) is set.

## In-session loop (default executor = your opencode agent)
```
python loop.py plan          # planner writes turns/NNN_instruction.json and prints it
# -> read the instruction, approve / edit / skip with the agent
python loop.py commit --status done --summary "one line"   # pipe the result on stdin
```
Repeat. Stop when the instruction has `"done": true`.

## Headless loop (optional; needs an executor CLI)
Set `executor.cmd` to a command containing `{prompt}` (e.g. `gemini -p "{prompt}"`),
then:
```
python loop.py run
```

## Files
- `state.json` — durable pointer (atomic writes). Resume point after a crash.
- `turns/NNN_instruction.json` / `turns/NNN_result.md` — per-turn audit trail.
- `events.log` — human-readable history.

## Guardrails
Instructions whose text matches a `denied_patterns` entry, or that carry
`"risk": "high"`, abort before execution and require a human. The executor must
never write outside `guardrails.allowed_roots`, and must never edit
`masterplan.md`, `state.json`, or `loop.py`.

## Tests
```
python -m pytest -q
```
```

- [ ] **Step 4: Verify the full suite and the CLI smoke**

Run: `python -m pytest -q`
Expected: PASS (16 passed)

Run: `python loop.py --help`
Expected: usage listing `plan`, `commit`, `run`

- [ ] **Step 5: Commit**

```powershell
git add planner-loop/config.example.json planner-loop/masterplan.example.md planner-loop/README.md
git commit -m "docs(planner-loop): example config, masterplan template, README"
```

---

## Self-Review

**1. Spec coverage**
- §4 Architecture / file layout → Tasks 1, 5, 7 (`masterplan.md`, `config.json`, `state.json`, `turns/`, `events.log`).
- §5 Data formats (config / state / instruction / result) → Tasks 1, 2, 7.
- §6 Two run modes (`plan`/`commit` in-session, `run` headless) → Tasks 5, 6.
- §7 Crash-resume (atomic writes, replan-in-place, backoff) → Tasks 1, 3, 5.
- §8 Guardrails & oversight → Task 4 (deny patterns + risk flag); human gate is the manual `plan`→approve→`commit` cycle.
- §9 Pluggable executor → Task 6 (`executor.cmd` with `{prompt}`).
- §10 Error handling (invalid JSON repair-once, missing config/target refused) → Tasks 1, 3, 5.
- §11 Verification → pytest suite (16 tests); spec's `--selftest` flag is superseded by pytest (same coverage, project's own runner).
- §12 Open decisions → resolved here: direct REST (not the gemini CLI); concrete `denied_patterns` in Task 7; in-session executor protocol = README.

**2. Placeholder scan** — no TBD/TODO; every code step shows full code. `<your-project>` is an intentional fill-in template in the example config, not a plan gap.

**3. Type consistency** — `commit_result(home, turn, body, status_name, summary)` has the same signature in Tasks 5 and 6; `_instruction_path`/`_result_path` defined once (Task 5) and reused (Task 6); planner config keys (`base_url`, `model`, `api_key_env`) identical across Tasks 3 and 7.
