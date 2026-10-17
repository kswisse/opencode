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
