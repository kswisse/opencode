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
python loop.py commit --home <dir> --status done --summary "one line" < result.md   # result piped on stdin
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
What the code enforces today: instructions whose text matches a
`denied_patterns` entry, or that carry `"risk": "high"`, abort before execution
and require a human.

The executor is *expected* to stay inside `guardrails.allowed_roots` and never
edit `masterplan.md`, `state.json`, or `loop.py` — but `allowed_roots` is
reserved and **not yet enforced** by `guardrail_check`; treat it as a
convention, not a boundary.

## Tests
```
python -m pytest -q
```
