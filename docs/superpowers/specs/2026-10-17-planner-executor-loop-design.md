# Planner ↔ Executor Loop — Design

- **Date:** 2026-10-17
- **Status:** Approved (design) — pending spec review
- **Scope:** Shared, multi-project. Target project selected per run via config.

## 1. Goal

An automated planner↔executor loop driven by a masterplan, with the human
approving each turn:

1. A **planner** LLM (Gemini free tier by default) reads the masterplan and the
   current state, and emits the next instruction as JSON.
2. The **executor** (an opencode session — me — by default) performs that
   instruction inside the target project, respecting guardrails.
3. The result is written to disk, the planner sees it, and the loop continues
   until the planner signals done or the human stops it.

Crash at any point must be recoverable with zero loss: **disk state is the
source of truth, not the chat session.**

## 2. Non-goals (YAGNI)

- No GUI. Terminal + files only.
- No multi-planner coalition / voting. One planner per run.
- No daemon / always-on service. A run is started and stopped by the human.
- No cloud storage of state. Everything under the loop directory on disk.
- No browser automation of the ChatGPT web UI (rejected — brittle vs. free tier).

## 3. Constraints (from environment)

- OpenAI **free tier has no API**, so "ChatGPT as automated planner" is not
  available. Planner is a free-API model instead (`GEMINI_API_KEY` is already
  present in the environment; `gemini` CLI also installed).
- `freellmapi` (in-repo, OpenAI-compatible aggregator with failover) is an
  optional failover planner endpoint. Self-hosting it is NOT required for v1.
- No `opencode` CLI on PATH (opencode runs as a desktop app). Therefore the
  default executor is the in-session opencode agent, not a spawned process.
- `gemini`, `pi`, `openclaude`, `agent-tars` CLIs are installed and available
  as optional headless executors.

## 4. Architecture

```
masterplan/                     # the loop's home (per project or shared)
  masterplan.md                 # human-owned plan, editable mid-run
  config.json                   # planner endpoint, target dir, guardrails
  state.json                    # durable pointer: turn, last_result, open_tasks, done
  turns/
    001_instruction.json        # planner output for turn 1
    001_result.md               # executor output for turn 1
    002_instruction.json
    002_result.md
  loop.py                       # single-file driver
  events.log                    # human-readable audit trail
```

Everything the loop needs to resume lives on disk. `state.json` is written
**atomically** (write temp file → rename) only after a turn fully completes.

## 5. Data formats

### config.json
```json
{
  "target_dir": "C:/Opencode/<project>",
  "planner": {
    "provider": "gemini",
    "base_url": "https://generativelanguage.googleapis.com/v1beta",
    "model": "gemini-2.5-flash",
    "api_key_env": "GEMINI_API_KEY",
    "fallbacks": []
  },
  "executor": { "kind": "in_session", "cmd": null },
  "guardrails": {
    "allowed_roots": ["C:/Opencode/<project>"],
    "denied_patterns": ["rm -rf", "format ", "git push --force", "Remove-Item -Recurse -Force C:"],
    "stop_on_risk_flag": true
  },
  "max_turns": 50
}
```
`executor.kind` is `in_session` (default) or `headless` with `cmd` set
(e.g. `gemini -p "{prompt}"`). `loop.py` never hardcodes an executor.

### state.json
```json
{
  "run_id": "2026-10-17T10-00-00",
  "turn": 0,
  "status": "awaiting_instruction | awaiting_approval | executing | done | stopped | error",
  "last_result_summary": "",
  "open_tasks": [],
  "done": false,
  "updated_at": "2026-10-17T10:00:00Z"
}
```

### instruction JSON (planner → executor)
```json
{
  "turn": 1,
  "goal": "one sentence",
  "actions": ["concrete action", "..."],
  "acceptance": "how we know it worked",
  "risk": "none | low | high",
  "done": false
}
```

### result file (executor → planner)
`turns/NN_result.md`:
```
## Turn NN result
Status: done | partial | blocked
Summary: ...
Evidence: commands run / files changed / test output
Next note: anything the planner must know
```

## 6. Two run modes (one turn = one atomic exchange)

`loop.py` has **two modes**, because the default executor is the in-session
agent and cannot be driven by a separate long-running process:

- **`loop.py plan`** — helper mode (default, in_session executor). Calls the
  planner once, writes `turns/NN_instruction.json`, returns the instruction to
  the caller. No process stays alive.
- **`loop.py commit --status <s> --summary <t>`** — writes `turns/NN_result.md`
  (from stdin), bumps `state.json` atomically, appends `events.log`.
- **`loop.py run`** — driver mode (headless executor only): the full blocking
  loop below, spawning `executor.cmd` each turn.

In **in_session** mode the loop is orchestrated by the agent/user like this:

```
1. loop.py plan            # → instruction NN (planner called here)
2. HUMAN GATE: user reads turns/NN_instruction.json; [a]pprove / [e]dit / [s]kip / [q]uit
3. agent executes the instruction inside target_dir under guardrails
4. loop.py commit          # result + state bump, atomic
5. if instruction.done or user quit or turn >= max_turns → stop, else goto 1
```

In **headless** mode (`loop.py run`), steps 1-5 run unattended inside the
driver: call planner → (no human gate) → spawn executor → commit → repeat,
until `done`, `error`, or `max_turns`.

## 7. Crash-resume semantics

- Planner API failure (timeout / 429 / 5xx): retry with exponential backoff;
  after N retries, try next `fallbacks` entry; after all fail → `status=error`,
  nothing lost (state.json unchanged since last completed turn).
- Session/executor dies mid-turn: `state.json` still points at the last
  completed turn; rerun `loop.py` (or resume in a new opencode session) and it
  restarts from step 2 of the interrupted turn. A partially-written result file
  is detected (no matching `state.json` bump) and overwritten.
- Human edits `masterplan.md` mid-run: picked up at the next planner call.

## 8. Guardrails & oversight

- Human approves every turn (chosen setting).
- Hard stop + ask, regardless of approval, when: a write targets a path outside
  `allowed_roots`; a command matches `denied_patterns`; or `instruction.risk == "high"`.
- The executor never edits `masterplan.md`, `state.json`, or `loop.py` — those
  are the human/driver's files.

## 9. Executor interface (pluggable)

- `in_session` (default): `loop.py plan` / `loop.py commit` are the driver's
  helpers; the in-session opencode agent executes the approved instruction and
  reports back via `commit`. Human gate lives in the chat/session.
- `headless`: `loop.py run` spawns `executor.cmd` with the instruction rendered
  into the prompt, captures stdout into the result file, and loops with no human
  gate (opt-in only).

Swapping executor = changing `config.json`. No code change.

## 10. Error handling

- Planner response not valid JSON → one repair attempt (ask planner to fix), then `error`.
- Missing/invalid config → refuse to start, print what's missing.
- `target_dir` does not exist → refuse to start.
- Atomic write: `tmp` file + `os.replace`; on crash the old state survives.

## 11. Verification

- One runnable check: `loop.py --selftest` exercises the turn state machine with
  a stubbed planner and stubbed executor — asserts turn increments, atomic state
  writes, resume-from-interrupted-turn, and guardrail blocking. No live API calls.
- Manual smoke: a 2-turn run against a throwaway target dir with the real planner.

## 12. Open decisions

- Concrete `denied_patterns` list to be finalized at implementation.
- Whether `gemini` CLI or direct REST is used for the planner call (REST
  preferred — one dependency, no CLI stdout parsing).
- Skill/protocol doc for the in-session executor to be authored in the plan.
