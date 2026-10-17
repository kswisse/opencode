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
import shlex
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
        except (urllib.error.URLError, urllib.error.HTTPError, KeyError, IndexError,
                ValueError) as exc:
            last = exc
            time.sleep(2 ** attempt)
    raise SystemExit("planner call failed after retries: %r" % last)


def guardrail_check(cfg, instruction):
    g = cfg.get("guardrails", {})
    blob = json.dumps(instruction, ensure_ascii=False).lower()
    for pattern in g.get("denied_patterns", []):
        if pattern.lower() in blob:
            raise SystemExit("GUARDRAIL: instruction matches denied pattern %r" % pattern)
    if g.get("stop_on_risk_flag", True) and instruction.get("risk") == "high":
        raise SystemExit("GUARDRAIL: instruction flagged risk=high; human must handle")


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
    if cfg.get("max_turns") and turn > cfg["max_turns"]:
        raise SystemExit("max_turns=%d reached; stopping" % cfg["max_turns"])
    instruction["turn"] = turn
    os.makedirs(os.path.join(home, "turns"), exist_ok=True)
    atomic_write_json(_instruction_path(home, turn), instruction)
    state["status"] = "awaiting_approval"
    save_state(home, state)
    append_event(home, "plan turn=%d goal=%s" % (turn, instruction.get("goal", "")))
    print(json.dumps(instruction, ensure_ascii=False, indent=2))


def commit_result(home, turn, body, status_name, summary, forced_status=None):
    os.makedirs(os.path.join(home, "turns"), exist_ok=True)
    with open(_result_path(home, turn), "w", encoding="utf-8") as f:
        f.write(body)
    instruction = load_json(_instruction_path(home, turn), default={})
    state = load_state(home)
    state["turn"] = turn
    state["last_result_summary"] = summary
    if forced_status == "blocked":
        state["done"] = False
        state["status"] = "blocked"
    elif instruction.get("done"):
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
    if not os.path.exists(_instruction_path(home, turn)):
        raise SystemExit("no instruction for turn %d; run `plan` first" % turn)
    commit_result(home, turn, sys.stdin.read(), status_name, summary)
    print("committed turn %d" % turn)


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
        # ponytail: posix=True always; template paths with backslashes are unsupported
        parts = shlex.split(executor_cmd, posix=True)
        if "{prompt}" in parts:
            parts[parts.index("{prompt}")] = prompt
        proc = subprocess.run(
            parts, cwd=cfg["target_dir"], capture_output=True, text=True,
            encoding="utf-8")
        body = proc.stdout + ("\n[stderr]\n" + proc.stderr if proc.stderr else "")
        status_name = "done" if proc.returncode == 0 else "blocked"
        commit_result(home, turn, body, status_name, body.strip()[:200],
                      forced_status=status_name)


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
