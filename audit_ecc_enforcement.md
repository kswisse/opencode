# ECC Enforcement Audit — Verdict

Read-only audit of Everything Claude Code (ECC) enforcement surfaces against the OpenCode runtime.
Sources: ECC @ `C:\Users\flash\AppData\Local\Temp\ECC-AUDIT` (SHA `c70874fa`, v2.2.2, clean), npm `ecc-agentshield@1.6.0`, `@opencode-ai/plugin` d.ts v1.4.3 + v1.18.27, opencode docs (2026-09-29), GitHub issues #2489/#2626. Nothing was installed; nothing outside the temp dirs was modified.

---

## 1. Executive verdict

**ECC ships real blocking logic only for Claude Code, and even there most "gates" are advisory. Its OpenCode adapter contains zero enforcement by construction — and parts of it do not conform to the plugin contract they were written against. Adopt nothing wholesale; build a small native layer; take three patterns and one offline auditor as reference.**

- Blocking scripts in the whole repo: **6** (`block-no-verify`, `config-protection`, `pre-bash-dev-server-block`, `pre-bash-commit-quality`, `gateguard-fact-force`, `plan-canvas-pending`). All Claude-Code-wired. **0** invoked by the OpenCode adapter.
- `stop-format-typecheck` — the flagship Stop gate — always exits 0 (scripts/hooks/stop-format-typecheck.js:247): **advisory**, despite memory-persistence/README claiming "Blocking: yes on hook failure". Only `plan-canvas-pending` actually emits `{"decision":"block"}` (scripts/hooks/plan-canvas-pending.js:221).
- The OpenCode adapter (`.opencode/plugins/ecc-hooks.ts`, full read) only logs, tracks, and injects compaction context. `scripts/hooks/*` has **zero references** from the adapter.

## 2. Hook event table

### 2a. OpenCode adapter (`.opencode/plugins/ecc-hooks.ts`) — the only surface OpenCode can ever see

| Handler key (line) | In plugin contract? | What it does | Enforcement |
|---|---|---|---|
| `file.edited` (180) | **No** — not a `Hooks` key; docs deliver it via generic `event` | records changed files | none |
| `file.watcher.updated` (452) | **No** (same) | records changes | none |
| `tool.execute.before` (276) | Yes | write tracking + 3 **log-only** reminders (git push, doc-file, tmux) | none — no `throw`, no arg mutation (docs show both are the blocking channels) |
| `tool.execute.after` (220) | Yes | edit records / compaction text | none |
| `permission.ask` (585) | Key yes, **signature violated** | returns `{approved}`; contract (v1.4.3 and v1.18.27 identical) requires mutating `output.status: ask\|deny\|allow`, return type `Promise<void>` → **return value discarded** | none; and its intent is to *auto-approve*, i.e. loosen |
| `session.created` (353) | **No** | CLAUDE.md detection log | none |
| `session.idle` (371) | **No** | console.log audit via shell `grep` + **modal `[MessageBox]::Show` on win32** (ecc-hooks.ts:404) | none + Windows hazard (below) |
| `session.deleted` (437) | **No** | clears store | none |
| `todo.updated` (469) | **No** | todo context | none |
| `shell.env` (484) | Yes | `PROJECT_ROOT`/`PACKAGE_MANAGER`/`DETECTED_LANGUAGES` env | informational |
| `experimental.session.compacting` (537) | Yes | appends ECC context to compaction prompt | **soft context injection — the only behavior that fully works as designed** |

Contract evidence: ECC pins `@opencode-ai/plugin@^1.4.3` (devDep); that d.ts and this environment's 1.18.27 d.ts both define `permission.ask: (input: Permission, output: {status}) => Promise<void>` and contain **no** `file.edited`/`session.*`/`todo.updated` keys. Official docs list those as bus **event types** received through the generic `event` hook (`event.type === "session.idle"`). ECC had to type its plugin return as `Record<string, unknown>` to compile past this. ECC's own tests (`tests/opencode-plugin-hooks.test.js`) call handlers *directly*, so they pass while integration is inert. → These six handlers are **very likely dead code at runtime (UNVERIFIED by instrumented run; immaterial to the verdict — none of them enforce anything either way).**

### 2b. Claude Code graph (`hooks/hooks.json` — 7 events, 24 entries, 55 scripts) — not reachable from OpenCode

| Event | Entries | Blocking members |
|---|---|---|
| PreToolUse | 9 | `block-no-verify` (exit 2), `pre-bash-dev-server-block` (exit 2), `pre-bash-commit-quality` (`exitCode: 2` :503), `config-protection` (exit 2 :238), `gateguard-fact-force` (`permissionDecision:'deny'` :1822); rest log-only (observe, governance-capture, suggest-compact, doc-file-warning, mcp-health-check) |
| PostToolUse | 2 | none (post-edit format/typecheck all exit 0) |
| PostToolUseFailure | 2 | none |
| PreCompact | 1 | none (state persist) |
| SessionStart | 2 | none (memory recall + plan-canvas) |
| **Stop** | 7 | **only** `plan-canvas-pending` (`decision:'block'`); `stop-format-typecheck`, `check-console-log`, `evaluate-session`, `cost-tracker`, `session-end`, `desktop-notify` all exit 0 → advisory |
| SessionEnd | 1 | none |

All profile-gated through `run-with-flags.js minimal,standard,strict`. Stop bootstrap carries a win32 drive-letter path fix; other bootstraps do not.

## 3. Windows / OpenCode compatibility ratings

| Component | OpenCode | Windows | Basis |
|---|---|---|---|
| Claude hook graph (55 scripts) | **Not wired** (N/A) | Partial — Node-portable, but grep/shell-dependent paths are weak | adapter never calls it |
| `permission.ask` auto-approve | **Broken** (contract violation at 1.4.3 *and* 1.18.27) | n/a | return vs `output.status` |
| Event-named handlers | **Likely inert** (UNVERIFIED runtime) | n/a | d.ts + docs pattern |
| `session.idle` audit | likely inert anyway | **Hazard if it fires**: modal MessageBox blocks the hook thread until clicked; `grep` absent on native Windows → exception → caught → "audit passed" (**false pass**) | ecc-hooks.ts:383-414 |
| Compaction injection | **Works** | OK (pure JS) | documented hook |
| `shell.env` detection | **Works** | OK (fs-based; tests forbid shell probes) | tests prove it |
| Memory vault (`ecc memory` CLI) | standalone, harness-neutral | **#2626 fixed** — `sameFileIdentity` now guards zero `dev` (scripts/lib/memory-vault.js) | verified in code |
| Continuous-learning observer | Claude-only | **#2489 fixed** — explicit win32 probes/branches (observe-runner.js:38-65) | verified in code |
| AgentShield | CLI/CI (any harness) | OK (bundled Node ≥20) | tarball inspected |

ECC's own catalog agrees: OpenCode = `availability: 'advanced'`, `guidedReady: false`, hooks `adapter-opt-in`, `eccConfigured: false` (scripts/lib/harness-capabilities.js).

## 4. Memory / session audit

- Vault: `ecc.memory.v1` markdown in project/team/user scopes; CLI `ecc memory` (`scripts/ecc.js`), opt-in `ecc-memory-mcp`. No `.ecc/` directory ships in the repo.
- Auto-recall exists **only** as Claude `SessionStart` (bounded by `ECC_SESSION_START_MAX_CHARS`, opt-out `ECC_SESSION_START_CONTEXT=off`); persistence at PreCompact/Stop — all declared `Blocking: no`.
- **Under OpenCode: no session-start recall at all; only compaction-time context injection.** Memory recall would be manual CLI only.
- Windows defects #2489 / #2626 are **closed and fixed in current code** (verified in implementation, not just issue text).

## 5. AgentShield audit

- npm `ecc-agentshield@1.6.0` (tarball pulled to temp, 12 files). `bin: agentshield` → bundled `dist/index.js` (~1.15 MB) + GitHub Action (`action.yml`) + GitHub App. Optional paid "Opus pipeline" (`@anthropic-ai/sdk`); MiniClaw export.
- It is an **offline scanner**, not a runtime gate: grades `~/.claude`-style configs for secrets, permissive permission rules, hook injection, MCP risk, agent prompt injection; `--fix` available; report includes "harness adapter evidence" for OpenCode/Codex/etc. (README:111).
- Windows: portable. Usage cost: one `npx ecc-agentshield scan --path <dir>` run; **never `--fix` without review**.

## 6. Cost-benefit (adapt value for THIS OpenCode stack)

| ECC mechanism | Benefit | Adaptation cost | Rating |
|---|---|---|---|
| Hard-block patterns (no-verify, config-protection, dev-server, commit-quality, gateguard deny) | HIGH | MEDIUM — must be rewritten against OpenCode channels anyway (ECC ships no OpenCode-ready form) | **HIGH → take as native rewrite patterns** |
| Stop quality gate (format/typecheck before done) | HIGH | IMPOSSIBLE — OpenCode has no Stop hook; ECC's version is advisory even in Claude | **LOW as-is; substitute natively (verify skill)** |
| Plan gate (plan-canvas Stop block) | MEDIUM | IMPOSSIBLE channel | **LOW as-is; procedural substitute** |
| Compaction context injection | MEDIUM | LOW — native documented hook already works | **HIGH → adopt idea** |
| `permission.ask` auto-approve | negative (loosens) | — | **reject** |
| Memory vault + CLI | MEDIUM | LOW-MEDIUM; overlaps existing hyperresearch vault | **MEDIUM → defer** |
| Continuous-learning observer | LOW-MEDIUM | daemon history, Windows baggage | **reject** |
| AgentShield offline scan | MEDIUM | LOW (run occasionally, read-only) | **HIGH → adopt as auditor** |
| Config weight: 11 always-loaded skills, ~25 agents, `"mcp_*": "ask"` only | LOW for enforcement | HIGH (token/session cost; stacks onto existing 239-agent/216-skill bloat) | **reject** |
| Notify/statusline/dashboard | LOW | — | **reject** |

## 7. Option A / B / C

- **A — Adopt ECC's OpenCode adapter wholesale: REJECT.** Zero enforcement by construction, `permission.ask` contract violation, likely-dead event handlers, modal-MessageBox/grep Windows hazards, large always-loaded config weight, and ECC itself marks the target `not installed by default`.
- **B — Port ECC's Claude-side blocking scripts into an OpenCode adapter: REJECT as stated.** The scripts speak Claude's stdin/exit-2/JSON-decision conventions; every valuable behavior must be re-expressed on OpenCode channels (`permission.ask → output.status`, `tool.execute.before → throw`, static `permission` rules) — that is a rewrite, and porting cost ≈ native cost while importing Claude-specific baggage (root resolver, bash probes, profile runner).
- **C — Build a native minimal enforcement layer, ECC as reference: SELECT.** Take 3 hard-guard patterns (block-no-verify, config-protection, protected-path write block), the compaction-injection idea, and AgentShield as an offline auditor. Everything else stays out.

## 8. Minimal target architecture

`MASTERPLAN → PLAN → IMPLEMENT → TEST → REVIEW → VERIFY → DRIFT CHECK → DONE`

| Stage | Mechanism | Strength |
|---|---|---|
| MASTERPLAN | `masterplan/` docs + workflow stamp via existing superpowers first-message injection (note: MASTERPLAN currently has zero references in root docs — wire it as part of this work) | soft |
| PLAN | mandatory plan/todo before code (`ce-plan`/`brainstorming` skills); REVIEW checks a plan artifact exists | medium |
| IMPLEMENT | **static `permission` rules in opencode.json** (currently zero rules in this env): DENY writes to config/lock/CI paths, ASK on `git push --force` etc. + optional ~150-line local plugin: `tool.execute.before` **throws** on `--no-verify`/protected paths/`rm -rf`, `permission.ask` sets `output.status = "deny"` for `curl\|sh`-style patterns | **hard** |
| TEST | TDD skill (`ado-test-driven-development` / `tdd`) with results recorded in todos | soft-medium |
| REVIEW | `ce-code-review` subagent before merge | medium |
| VERIFY | `verification-before-completion` skill: run lint/typecheck/tests, attach real command output as receipt | soft-medium |
| DRIFT CHECK | `git diff` vs plan + occasional `npx ecc-agentshield scan --path .` (read-only, no `--fix`) for config drift/security | medium |
| DONE | no native Stop hook exists — DONE declared only after a VERIFY receipt; the plugin hard-guards above are the backstop | medium + hard edge |

## 9. UNVERIFIED

1. Runtime dispatch of ECC's event-named handler keys (inferred inert from d.ts v1.4.3/v1.18.27 + official docs; would need an instrumented OpenCode run).
2. Whether OpenCode ever honors stray hook return values (contract says no).
3. Whether Claude Code treats Stop exit-1 as blocking (README's "yes on hook failure" claim; no exit-2/decision in `stop-format-typecheck`).
4. Depth of AgentShield's OpenCode-pattern coverage (README claims only; scan not executed).
5. Installed desktop-app OpenCode core version vs docs snapshot (2026-09-29).

## 10. One exact next step

**Draft (do not apply) the native enforcement change set as a reviewable diff plan: (1) `.opencode/plugins/gates.ts` — one dependency-free plugin with three hard guards: `tool.execute.before` throws on git `--no-verify`/`core.hooksPath=` and on writes to `opencode.json`/lockfiles/`.github/`, and `permission.ask` sets `output.status = "deny"` for `curl … | sh` / `rm -rf /` patterns; (2) matching static `permission` rules in `opencode.json`; (3) MASTERPLAN workflow stamp in CLAUDE.md — presented to the user for approval before any file outside the temp audit dir is touched.**
