# ECC Skill Coverage Audit — ECC Skill → OpenCode Capability Mapping

READ-ONLY audit. Nothing outside this file was modified. Companion document: `C:\Opencode\audit_ecc_enforcement.md` (ECC enforcement architecture audit).

**Sources of truth**

- ECC catalog: `C:\Users\flash\AppData\Local\Temp\ECC-AUDIT\skills\` (293 skills, every one has a `SKILL.md`; clone SHA `c70874fa`, v2.2.2, clean tree). Path prefix below: `ECC/<skill>/SKILL.md`.
- Current OpenCode environment: `C:\Opencode\.opencode\skills\` (182), `C:\Opencode\.claude\skills\` (19, loaded via `skills.paths`), superpowers plugin `C:\Users\flash\.config\opencode\superpowers\skills\` (14), 1 builtin (`customize-opencode`) = **216 discoverable skills**; **239 agents** in `C:\Users\flash\.config\opencode\agents\`; **4 MCP servers** (project: autoclip, hyperresearch, context7 in `C:\Opencode\opencode.json`; global: playwright in `C:\Users\flash\.config\opencode\opencode.jsonc`); 1 plugin (superpowers, `experimental.chat.messages.transform`); `C:\Opencode\CLAUDE.md`; workflow docs under `C:\Opencode\masterplan\`.
- **Excluded as duplicates** (per task rules): `C:\Opencode\opencode-skill-pack\skills\`; inactive agent libraries (`C:\Opencode\agent\`, `agent.zip`, Octop libs); `.claude\agents\` (16 hyperresearch-* agents are NOT discovered by OpenCode).

**Evidence-path legend used in §5**

`OP/` = `.opencode\skills\`, `CL/` = `.claude\skills\`, `SP/` = superpowers plugin skills, `AG/` = active agents dir, `CFG` = `C:\Opencode\opencode.json`, `BUILTIN` = OpenCode built-in tool/skill. Rows marked `UNVERIFIED` have insufficient evidence.

**Type vocabulary (§5):** direct / functional / partial / missing / incompatible / redundant. **Coverage:** full / substantial / partial / none. No numeric scores are used.

**Classification rule applied:** "Claude-specific" = body or frontmatter depends on Claude Code runtime surfaces (`~/.claude`, hooks, slash commands, Claude products) — automated scan found 77 such skills. "OpenCode-compatible" = the skill is plain instructions that OpenCode can execute as written (`yes`), can execute with a substitute tool (`partial`), or cannot execute (`no`).

---

## 1. ECC Skill Enumeration (293)

### 1.1 Summary statistics (mechanically derived from all 293 SKILL.md files)

| Signal | Count | Meaning for OpenCode |
| --- | --- | --- |
| Total skills | 293 | Full catalog |
| Claude-specific (runtime/product dependency) | 77 | Needs adaptation or is ECC-internal |
| Depend on Claude Code hooks | 36 | No OpenCode hook engine → enforcement lost |
| Depend on an MCP server | 37 | Workable only where an equivalent MCP/tool exists |
| Contain a workflow (multi-phase procedure) | 50 | Directly portable as instructions |
| Contain explicit verification steps | 93 | Portable; enforcement is not |
| Ship scripts (deterministic automation) | 14 | Portable if the runtime exists |
| Reference external skill/command files | 12 | Often ECC-internal → not portable |
| Explicitly deprecated | 4 | `continuous-learning`, `mysql-patterns`, `agent-payment-x402`, `architecture-decision-records`* (*flagged deprecated in scan; ADR itself is still functional — see §5.10) |
| Mention OpenCode | 5 | `dmux-workflows`, `ecc-guide`, `plan-canvas`, `product-capability`, `unified-notifications-ops` |
| Frontmatter keys present | `name`, `description` (293), `metadata` (266), `tools` (11), `allowed-tools` (2) | No `dependencies:` / `requires:` / `mcp_servers:` frontmatter anywhere — all dependencies live in the body text |

### 1.2 Full enumeration (name · short purpose · dependencies · Claude-specific · OpenCode-compatible · primary type)

| # | ECC Skill | Short purpose | Dependencies | Claude-specific | OC-compatible | Primary type |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | accessibility | WCAG 2.2 AA UI design/audit | none | no | yes | reference material |
| 2 | agent-architecture-audit | 12-layer agent stack diagnostic | none | no | yes | verification |
| 3 | agent-eval | Head-to-head coding-agent comparison | scripts | yes | partial | workflow |
| 4 | agent-harness-construction | Design agent action spaces/tools | none | no | yes | instruction/prompt |
| 5 | agentic-engineering | Eval-first agentic execution model | none | no | yes | workflow |
| 6 | agentic-os | Persistent multi-agent OS on Claude Code | hooks | yes | no | orchestration |
| 7 | agent-introspection-debugging | Structured agent-failure diagnosis | none | no | yes | workflow |
| 8 | agent-payment-x402 | x402 payment execution for agents (deprecated) | MCP, SDK | yes | no | tool wrapper |
| 9 | agent-self-evaluation | 5-axis post-task self-rating | hooks | yes | partial | verification |
| 10 | agent-sort | Sort ECC parts into daily/library install plan | MCP | yes | no | workflow |
| 11 | ai-first-engineering | Process/review gates for agent-written code | none | no | yes | instruction/prompt |
| 12 | ai-regression-testing | Regression strategy for AI-assisted dev | none | yes | yes | workflow |
| 13 | android-clean-architecture | Android/KMP Clean Architecture | none | no | no | reference material |
| 14 | angular-developer | Angular codegen + architecture guidance | MCP | no | no | reference material |
| 15 | api-connector-builder | Clone existing integration pattern | MCP, hooks | yes | partial | workflow |
| 16 | api-design | REST API design patterns | none | no | yes | reference material |
| 17 | architecture-decision-records | Numbered ADRs in docs/adr | none | no | yes | workflow |
| 18 | article-writing | Long-form content in derived voice | none | no | yes | instruction/prompt |
| 19 | automation-audit-ops | Inventory live/broken/redundant automations | MCP, hooks | yes | partial | workflow |
| 20 | autonomous-agent-harness | Autonomous agent system on Claude Code | MCP, hooks | yes | no | orchestration |
| 21 | autonomous-loops | Autonomous loop patterns (compat shim) | none | yes | no | orchestration |
| 22 | backend-patterns | Node/Express/Next API patterns | none | no | yes | reference material |
| 23 | benchmark | Perf baselines + regression detection | MCP | no | partial | verification |
| 24 | benchmark-methodology | Weighted competitor profile scoring | none | no | yes | workflow |
| 25 | benchmark-optimization-loop | Bounded measured optimization loop | scripts | no | yes | workflow |
| 26 | blender-motion-state-inspection | Blender rig/motion inspection | scripts | no | no | tool wrapper |
| 27 | blueprint | One-line objective → multi-session build plan | none | yes | yes | workflow |
| 28 | brand-discovery | 8-module brand identity interview | none | no | yes | workflow |
| 29 | brand-voice | Source-derived writing style profile | hooks | yes | partial | workflow |
| 30 | browser-qa | Post-deploy automated UI verification | MCP | yes | partial | verification |
| 31 | bun-runtime | Bun runtime/package/test guidance | none | no | no | reference material |
| 32 | canary-watch | Post-deploy URL smoke monitoring | hooks | yes | partial | verification |
| 33 | carrier-relationship-management | Freight carrier portfolio management | none | no | no | reference material |
| 34 | cisco-ios-patterns | Cisco IOS config review patterns | none | no | no | reference material |
| 35 | ck | Deterministic per-project memory CLI + hook | Node CLI, hooks | yes | partial | memory |
| 36 | claude-devfleet | Multi-agent worktree orchestration | MCP | yes | partial | orchestration |
| 37 | clickhouse-io | ClickHouse schema/query patterns | MCP | no | no | reference material |
| 38 | click-path-audit | Trace UI state-sequence bugs | none | no | yes | workflow |
| 39 | codebase-onboarding | Codebase → onboarding guide + CLAUDE.md | none | yes | yes | workflow |
| 40 | codehealth-mcp | CodeScene quality gates on edits/PRs | MCP | yes | partial | tool wrapper |
| 41 | code-tour | CodeTour .tour walkthrough files | none | no | yes | workflow |
| 42 | coding-standards | Baseline cross-project conventions | hooks | yes | yes | instruction/prompt |
| 43 | competitive-platform-analysis | Scope/filter a competitor set | none | no | yes | workflow |
| 44 | competitive-report-structure | Assemble scored competitive report | none | no | yes | workflow |
| 45 | compose-multiplatform-patterns | KMP/Compose UI patterns | none | no | no | reference material |
| 46 | config-gc | Garbage-collect stale ~/.claude config | MCP, hooks | yes | partial | workflow |
| 47 | configure-ecc | Conversational ECC setup wizard | hooks | yes | no | deterministic automation |
| 48 | connections-optimizer | X/LinkedIn network pruning + outreach | none | no | no | workflow |
| 49 | content-engine | Platform-native content systems | none | no | yes | workflow |
| 50 | content-hash-cache-pattern | SHA-256 result caching pattern | none | no | yes | reference material |
| 51 | context-budget | Audit context-window consumption/bloat | MCP | yes | partial | verification |
| 52 | continuous-agent-loop | Autonomous loops with quality gates | none | no | yes | orchestration |
| 53 | continuous-learning | Deprecated v1 learning extractor | hooks | yes | no | memory |
| 54 | continuous-learning-v2 | Instinct-based session learning | hooks | yes | partial | memory |
| 55 | contract-first | One machine-checkable interface contract | none | no | yes | workflow |
| 56 | cost-aware-llm-pipeline | LLM cost routing/budget patterns | none | no | yes | reference material |
| 57 | cost-tracking | Token spend from ECC metrics log | hooks | yes | no | tool wrapper |
| 58 | council | Four-voice decision council | none | yes | yes | workflow |
| 59 | council-multi-model | External model critique of a decision | MCP | no | partial | workflow |
| 60 | counterparty-channel-discipline | Agent comms rules in shared channels | none | no | no | instruction/prompt |
| 61 | cpp-coding-standards | C++ Core Guidelines standards | none | no | no | reference material |
| 62 | cpp-testing | GoogleTest/CTest patterns | none | no | no | reference material |
| 63 | crosspost | Multi-platform content distribution | none | no | yes | workflow |
| 64 | csharp-testing | xUnit/.NET testing patterns | none | no | no | reference material |
| 65 | customer-billing-ops | Stripe billing/subscriber workflows | none | no | no | workflow |
| 66 | customs-trade-compliance | Tariff/Incoterms compliance expertise | none | no | no | reference material |
| 67 | dart-flutter-patterns | Flutter/Dart production patterns | none | no | no | reference material |
| 68 | dashboard-builder | Grafana/SigNoz operator dashboards | MCP | no | partial | workflow |
| 69 | database-migrations | Safe reversible migration patterns | none | no | yes | reference material |
| 70 | data-scraper-agent | Scheduled automated data collection | none | no | yes | workflow |
| 71 | data-throughput-accelerator | Diagnose/accelerate bulk data movement | tools | no | partial | workflow |
| 72 | deep-research | Cited multi-source research report | MCP (firecrawl, exa) | yes | partial | workflow |
| 73 | defi-amm-security | Solidity AMM security checklist | none | no | UNVERIFIED | security |
| 74 | delivery-gate | Stop hook blocks unfinished work | hooks | yes | partial | verification |
| 75 | deployment-patterns | CI/CD, Docker, rollback patterns | none | no | yes | reference material |
| 76 | design-system | Codebase → design tokens + DESIGN.md | MCP | no | yes | workflow |
| 77 | dev-team | Multi-persona team session | none | no | yes | orchestration |
| 78 | django-celery | Django+Celery async patterns | none | no | no | reference material |
| 79 | django-patterns | Django/DRF architecture patterns | none | no | no | reference material |
| 80 | django-security | Django auth/input security | none | no | no | security |
| 81 | django-tdd | pytest-django TDD | none | no | no | workflow |
| 82 | django-verification | Django lint/test/security verification loop | none | no | no | verification |
| 83 | dmux-workflows | tmux multi-agent parallel sessions | tmux/dmux | yes | yes | orchestration |
| 84 | docker-patterns | Docker/Compose build + hardening | none | no | yes | reference material |
| 85 | documentation-lookup | Current library docs via Context7 MCP | MCP (context7) | yes | yes | tool wrapper |
| 86 | dotnet-patterns | C#/.NET idioms + DI | none | no | no | reference material |
| 87 | dynamic-workflow-mode | Task-local harnesses + eval gates | none | yes | partial | workflow |
| 88 | e2e-testing | Playwright E2E patterns + POM | none | no | yes | reference material |
| 89 | ecc-guide | Answers about ECC itself | none | yes | no | tool wrapper |
| 90 | ecc-recipes | ECC command-group recipes | none | yes | no | reference material |
| 91 | ecc-tools-cost-audit | ECC Tools billing/quota audit | none | yes | no | workflow |
| 92 | email-ops | Mailbox triage/send evidence workflow | none | yes | no | workflow |
| 93 | energy-procurement | Energy tariff/hedging expertise | none | no | no | reference material |
| 94 | enterprise-agent-ops | Long-lived agent lifecycle/observability | none | no | yes | orchestration |
| 95 | error-handling | TS/Py/Go error-handling patterns | none | no | yes | reference material |
| 96 | esign-field-placement | Deterministic e-sign field placement | browser automation | no | no | deterministic automation |
| 97 | eval-harness | Eval-driven development framework | scripts, hooks | yes | partial | verification |
| 98 | evm-token-decimals | EVM decimal-mismatch prevention | none | no | UNVERIFIED | reference material |
| 99 | exa-search | Exa neural search via MCP | MCP (exa) | no | partial | tool wrapper |
| 100 | fal-ai-media | Image/video/audio generation via fal.ai | MCP (fal) | no | partial | tool wrapper |

| 101 | fastapi-patterns | FastAPI project/service patterns | none | no | no | reference material |
| 102 | finance-billing-ops | ECC internal revenue/billing truth | none | yes | no | workflow |
| 103 | flox-environments | Nix-based reproducible environments | Flox/Nix, hooks | yes | no | deterministic automation |
| 104 | flutter-dart-code-review | Flutter/Dart review checklist | none | no | no | reference material |
| 105 | foundation-models-on-device | Apple on-device LLM framework | none | no | no | reference material |
| 106 | frontend-a11y | React/Next accessibility patterns | none | no | yes | reference material |
| 107 | frontend-design-direction | ECC frontend design direction | none | no | yes | instruction/prompt |
| 108 | frontend-patterns | React/Next component patterns | none | yes | yes | reference material |
| 109 | frontend-slides | Animation-rich HTML presentations | none | no | yes | workflow |
| 110 | fsharp-testing | F# property/xUnit testing | none | no | no | reference material |
| 111 | gan-style-harness | Generator-Evaluator autonomous harness | MCP | yes | partial | orchestration |
| 112 | gateguard | Deny first write until facts presented | hooks | yes | no | verification |
| 113 | generating-python-installer | Nuitka/Inno Setup Windows installer | build tools | no | no | reference material |
| 114 | github-ops | gh CLI issues/PRs/CI/releases | gh CLI | no | yes | workflow |
| 115 | git-workflow | Branching/commits/rebase/conflicts | git | no | yes | workflow |
| 116 | golang-patterns | Idiomatic Go patterns | none | no | no | reference material |
| 117 | golang-testing | Go table-driven/fuzz testing | none | no | no | reference material |
| 118 | google-workspace-ops | Drive/Docs/Sheets one workflow | Google MCP/APIs | no | no | workflow |
| 119 | growth-log | Extract reusable pattern per completed task | none | yes | yes | memory |
| 120 | healthcare-cdss-patterns | Clinical decision support patterns | none | no | no | reference material |
| 121 | healthcare-emr-patterns | EMR/EHR development patterns | none | no | no | reference material |
| 122 | healthcare-eval-harness | Patient-safety eval gate | none | no | no | verification |
| 123 | healthcare-phi-compliance | PHI/PII compliance patterns | none | no | no | security |
| 124 | hermes-imports | Hermes workflow → ECC skill conversion | none | yes | no | workflow |
| 125 | hexagonal-architecture | Ports & Adapters architecture | none | no | yes | reference material |
| 126 | hipaa-compliance | HIPAA privacy/security entrypoint | none | no | no | security |
| 127 | homelab-network-readiness | Homelab VLAN/DNS/VPN readiness | none | no | no | reference material |
| 128 | homelab-network-setup | Home network planning | none | no | no | reference material |
| 129 | homelab-pihole-dns | Pi-hole DNS setup/troubleshooting | none | no | no | reference material |
| 130 | homelab-vlan-segmentation | VLAN segmentation how-to | none | no | no | reference material |
| 131 | homelab-wireguard-vpn | WireGuard server/peers setup | none | no | no | reference material |
| 132 | hookify-rules | Declarative warn/block hook rules | hooks | yes | no | deterministic automation |
| 133 | i18n-sync | Locale file translate/sync | none | yes | no | workflow |
| 134 | inherit-legacy-style | Scan codebase → enforceable style rules | none | yes | yes | workflow |
| 135 | intent-driven-development | Ambiguity → verifiable acceptance criteria | none | no | yes | workflow |
| 136 | inventory-demand-planning | Retail demand forecasting expertise | none | no | no | reference material |
| 137 | investor-materials | Decks/memos/financial models | none | no | no | workflow |
| 138 | investor-outreach | Fundraising outreach drafts | none | no | no | workflow |
| 139 | ios-icon-gen | iOS icon PNG imagesets | icon APIs | no | no | tool wrapper |
| 140 | iterative-retrieval | Progressive context retrieval for subagents | none | no | yes | workflow |
| 141 | ito-baskets | Itô prediction-market basket data | MCP | no | no | tool wrapper |
| 142 | ito-compute | Itô GPU booking/RFQ | MCP | no | no | tool wrapper |
| 143 | ito-inference | Itô model-serving inspection | MCP | no | no | tool wrapper |
| 144 | ito-training | Itô ML-training inspection | MCP | no | no | tool wrapper |
| 145 | java-coding-standards | Java/Spring/Quarkus standards | none | no | no | reference material |
| 146 | jira-integration | Jira tickets via MCP/REST | MCP | no | no | tool wrapper |
| 147 | jpa-patterns | JPA/Hibernate entity patterns | none | no | no | reference material |
| 148 | knowledge-ops | Knowledge base ingest/sync/search | MCP | yes | partial | memory |
| 149 | kotlin-coroutines-flows | Kotlin coroutines/Flow patterns | none | no | no | reference material |
| 150 | kotlin-exposed-patterns | Exposed ORM patterns | none | no | no | reference material |
| 151 | kotlin-ktor-patterns | Ktor server patterns | none | no | no | reference material |
| 152 | kotlin-patterns | Idiomatic Kotlin patterns | none | no | no | reference material |
| 153 | kotlin-testing | Kotest/MockK testing | none | no | no | reference material |
| 154 | kubernetes-patterns | K8s workload/RBAC patterns | kubectl | no | no | reference material |
| 155 | laravel-patterns | Laravel architecture patterns | none | no | no | reference material |
| 156 | laravel-plugin-discovery | Laravel package discovery | MCP | no | no | tool wrapper |
| 157 | laravel-security | Laravel auth/input security | none | no | no | security |
| 158 | laravel-tdd | Laravel PHPUnit/Pest TDD | none | no | no | workflow |
| 159 | laravel-verification | Laravel verification loop | none | no | no | verification |
| 160 | latency-critical-systems | p50/p95/p99 latency optimization | tools | no | partial | workflow |
| 161 | lead-intelligence | AI lead scoring/outreach pipeline | MCP | no | no | workflow |
| 162 | liquid-glass-design | iOS 26 Liquid Glass UI | none | no | no | reference material |
| 163 | living-docs-governance | Keep long-lived docs from rotting | none | yes | yes | workflow |
| 164 | llm-trading-agent-security | Trading-agent security patterns | none | no | no | security |
| 165 | logistics-exception-management | Freight exception handling | none | no | no | reference material |
| 166 | loop-design-check | Design/review agent loops for failure modes | none | yes | yes | verification |
| 167 | mailtrap-email-integration | Transactional email integration | external API | no | no | tool wrapper |
| 168 | make-interfaces-feel-better | UI polish details (spacing/motion/states) | none | no | yes | instruction/prompt |
| 169 | manim-video | Manim animated explainers | Manim | no | no | tool wrapper |
| 170 | marketing-campaign | End-to-end campaign plan + assets | none | no | yes | workflow |
| 171 | market-research | Market/competitor research w/ sources | none | no | yes | workflow |
| 172 | master-agreement-generator | Counterparty agreement drafts | none | no | no | workflow |
| 173 | mcp-server-patterns | Build MCP servers (Node SDK) | MCP SDK | no | yes | reference material |
| 174 | messages-ops | Messaging/OTP evidence workflow | none | yes | no | workflow |
| 175 | ml-adoption-playbook | Add ML to non-ML codebases | none | no | yes | workflow |
| 176 | mle-workflow | Production ML engineering workflow | none | no | yes | workflow |
| 177 | motion-advanced | React drag/gesture/SVG motion | motion lib | yes | partial | reference material |
| 178 | motion-foundations | Motion tokens/springs foundation | motion lib | no | partial | reference material |
| 179 | motion-patterns | React button/modal/transition animations | motion lib | no | partial | reference material |
| 180 | mysql-patterns | MySQL schema/index patterns (deprecated) | none | no | no | reference material |
| 181 | nanoclaw-repl | NanoClaw session REPL | Node, hooks | yes | no | tool wrapper |
| 182 | nasiko-control-plane | Nasiko CLI lifecycle | external CLI | yes | no | tool wrapper |
| 183 | nestjs-patterns | NestJS module/provider patterns | none | no | no | reference material |
| 184 | netmiko-ssh-automation | Safe Python SSH device automation | Netmiko | no | no | deterministic automation |
| 185 | network-bgp-diagnostics | BGP troubleshooting patterns | network gear | no | no | verification |
| 186 | network-config-validation | Pre-deploy network config checks | none | no | no | verification |
| 187 | network-interface-health | Interface error diagnosis | none | no | no | verification |
| 188 | nextjs-turbopack | Next 16/Turbopack guidance | none | no | yes | reference material |
| 189 | nodejs-keccak256 | Ethereum Keccak-256 correctness | none | no | no | reference material |
| 190 | nutrient-document-processing | Cloud document OCR/convert/redact | MCP (Nutrient) | no | partial | tool wrapper |
| 191 | nuxt4-patterns | Nuxt 4 SSR/hydration patterns | none | no | no | reference material |
| 192 | openclaw-persona-forge | OpenClaw agent persona generation | image gen | yes | no | workflow |
| 193 | opensource-pipeline | Fork/sanitize/package for public release | none | no | yes | workflow |
| 194 | operator-approval-loop | Human approval contract for outbound msgs | none | no | yes | verification |
| 195 | orch-add-feature | Orchestrate new feature end to end | none | no | yes | orchestration |
| 196 | orch-build-mvp | Orchestrate MVP from spec | none | no | yes | orchestration |
| 197 | orch-change-feature | Orchestrate behavior change | none | no | yes | orchestration |
| 198 | orch-fix-defect | Orchestrate bug fix as regression test | none | no | yes | orchestration |
| 199 | orch-pipeline | Gated Research-Plan-TDD-Review-Commit engine | none | no | yes | orchestration |
| 200 | orch-refine-code | Orchestrate behavior-preserving refactor | none | no | yes | orchestration |

| 201 | parallel-execution-optimizer | Task → dependency-graph parallel lanes | none | no | yes | orchestration |
| 202 | perl-patterns | Modern Perl idioms | none | no | no | reference material |
| 203 | perl-security | Perl taint/input security | none | no | no | security |
| 204 | perl-testing | Test2::V0 / TDD for Perl | none | no | no | reference material |
| 205 | plan-canvas | Browser canvas for human plan approval | hooks | yes | partial | workflow |
| 206 | plankton-code-quality | Write-time format/lint/auto-fix hooks | hooks | yes | no | deterministic automation |
| 207 | plan-orchestrate | Plan → per-step agent chain prompts | none | yes | yes | workflow |
| 208 | postgres-patterns | PostgreSQL schema/index/RLS patterns | none | no | yes | reference material |
| 209 | prediction-market-oracle-research | Prediction markets as data signals | none | no | yes | workflow |
| 210 | prediction-market-risk-review | Risk review of market/trading workflows | none | no | yes | verification |
| 211 | prisma-patterns | Prisma ORM schema/query patterns | none | no | no | reference material |
| 212 | product-capability | PRD → implementation-ready capability plan | none | yes | yes | workflow |
| 213 | production-audit | Local-evidence production readiness audit | none | yes | yes | verification |
| 214 | production-scheduling | Manufacturing scheduling expertise | none | no | no | reference material |
| 215 | product-lens | YC-style product go/no-go diagnostics | none | no | yes | workflow |
| 216 | project-flow-ops | GitHub + Linear execution flow | MCP | no | partial | workflow |
| 217 | prompt-optimizer | Diagnose + rewrite draft prompts | none | yes | partial | instruction/prompt |
| 218 | python-patterns | PEP 8 / idiomatic Python | none | no | yes | reference material |
| 219 | python-testing | pytest fixtures/mocks/coverage + TDD | none | no | yes | reference material |
| 220 | pytorch-patterns | PyTorch training pipeline patterns | none | no | no | reference material |
| 221 | quality-nonconformance | Regulated-manufacturing QMS expertise | none | no | no | reference material |
| 222 | quarkus-patterns | Quarkus 3 architecture patterns | none | no | no | reference material |
| 223 | quarkus-security | Quarkus JWT/RBAC security | none | no | no | security |
| 224 | quarkus-tdd | Quarkus JUnit/Mockito TDD | none | no | no | workflow |
| 225 | quarkus-verification | Quarkus build/scan/coverage loop | none | no | no | verification |
| 226 | rails-patterns | Rails 7.1+/8 patterns | none | no | no | reference material |
| 227 | ralphinho-rfc-pipeline | RFC → multi-agent execution DAG | none | no | yes | orchestration |
| 228 | react-native-patterns | React Native/Expo patterns | none | yes | no | reference material |
| 229 | react-patterns | React 18/19 hooks/boundaries/forms | none | yes | yes | reference material |
| 230 | react-performance | Vercel 40+ React/Next perf rules | none | yes | yes | reference material |
| 231 | react-testing | RTL/Vitest/MSW component testing | none | yes | yes | reference material |
| 232 | recsys-pipeline-architect | Recommendation pipeline framework | none | no | no | reference material |
| 233 | recursive-decision-ledger | Append-only ledger for recursive rollouts | none | no | UNVERIFIED | verification |
| 234 | redis-patterns | Redis caching/lock/rate-limit patterns | none | no | no | reference material |
| 235 | regex-vs-llm-structured-text | Regex-first vs LLM parsing decision | none | no | yes | workflow |
| 236 | remotion-video-creation | Programmatic video in React (Remotion) | Remotion | no | yes | reference material |
| 237 | repo-scan | Bootstrap pointer installing external skill | install step | no | no | tool wrapper |
| 238 | research-ops | Evidence-first current-state research | none | no | yes | workflow |
| 239 | returns-reverse-logistics | Returns/refunds/fraud operations | none | no | no | reference material |
| 240 | rules-distill | Extract cross-cutting rules from skills | none | yes | yes | memory |
| 241 | rust-patterns | Idiomatic Rust patterns | none | no | no | reference material |
| 242 | rust-testing | Rust test/property/coverage patterns | none | no | no | reference material |
| 243 | safety-guard | Intercept destructive commands (3 modes) | hooks | yes | no | security |
| 244 | santa-method | Two independent reviewers must both pass | none | yes | yes | verification |
| 245 | scientific-db-pubmed-database | PubMed/NCBI E-utilities workflows | NCBI APIs | no | partial | tool wrapper |
| 246 | scientific-db-uspto-database | USPTO patent lookup workflows | USPTO APIs | no | no | tool wrapper |
| 247 | scientific-pkg-gget | gget genomic queries | gget CLI | no | no | tool wrapper |
| 248 | scientific-thinking-literature-review | Systematic literature-review workflow | none | no | yes | workflow |
| 249 | scientific-thinking-scholar-evaluation | Scholarly work evaluation | none | no | yes | verification |
| 250 | search-first | Search npm/PyPI/GitHub before building | MCP, scripts | yes | yes | workflow |
| 251 | security-bounty-hunter | Bounty-qualifying vulnerability hunting | none | no | yes | security |
| 252 | security-review | Auth/input/secrets security checklist | none | no | yes | security |
| 253 | security-scan | Scan agent config with AgentShield | AgentShield, MCP | yes | partial | security |
| 254 | seo | Technical/on-page SEO audit + fixes | none | no | yes | workflow |
| 255 | skill-comply | Measure whether skills are actually followed | scripts, hooks | yes | partial | verification |
| 256 | skill-scout | Search existing skills before creating | MCP | yes | yes | workflow |
| 257 | skill-stocktake | Batch-audit skill quality | none | yes | yes | verification |
| 258 | social-graph-ranker | Warm-intro graph ranking engine | none | no | no | reference material |
| 259 | social-publisher | Publish to 13 platforms (SocialClaw) | MCP, hooks | yes | partial | tool wrapper |
| 260 | springboot-patterns | Spring Boot architecture patterns | none | no | no | reference material |
| 261 | springboot-security | Spring Security authn/authz patterns | none | no | no | security |
| 262 | springboot-tdd | Spring Boot JUnit/Testcontainers TDD | none | no | no | workflow |
| 263 | springboot-verification | Spring build/scan/coverage loop | none | no | no | verification |
| 264 | strategic-compact | Phase-gated manual context compaction | none | yes | yes | instruction/prompt |
| 265 | swift-actor-persistence | Swift actor persistence patterns | none | no | no | reference material |
| 266 | swift-concurrency-6-2 | Swift 6.2 concurrency patterns | none | no | no | reference material |
| 267 | swift-protocol-di-testing | Swift protocol DI + Swift Testing | none | no | no | reference material |
| 268 | swiftui-patterns | SwiftUI architecture patterns | none | no | no | reference material |
| 269 | taste | Music-video aesthetic/grammar | none | no | no | instruction/prompt |
| 270 | taste-application | Generate + cut video against style pack | fal.ai, media tools | no | no | workflow |
| 271 | taste-distillation | Measure reference videos into style pack | media tools | no | no | workflow |
| 272 | tasteforge-video | File-driven video discovery/distill/apply | media tools | no | no | workflow |
| 273 | tdd-workflow | Red/green/refactor + 80% coverage | none | yes | yes | workflow |
| 274 | team-agent-orchestration | Agent squads kanban + merge gates | none | yes | partial | orchestration |
| 275 | team-builder | Pick personas, dispatch in parallel | none | yes | yes | orchestration |
| 276 | terminal-opener | Open exe in visible terminal (Codex) | Codex runtime | yes | no | deterministic automation |
| 277 | terminal-ops | Evidence-first repo command execution | none | no | yes | workflow |
| 278 | tinystruct-patterns | tinystruct Java framework guidance | MCP | no | no | reference material |
| 279 | token-budget-advisor | Offer response depth choice | none | yes | yes | instruction/prompt |
| 280 | ui-demo | Record polished UI demo videos | Playwright, hooks | no | partial | tool wrapper |
| 281 | ui-to-vue | Screenshots → Vue 3 components | none | no | partial | workflow |
| 282 | uncloud | Uncloud cluster operations | external CLI | no | no | tool wrapper |
| 283 | unified-memory | Cross-harness Memory Vault handoffs | MCP | yes | partial | memory |
| 284 | unified-notifications-ops | Notification routing/dedup | hooks, MCP | yes | no | tool wrapper |
| 285 | verification-loop | Six-phase PASS/FAIL verification report | none | yes | yes | verification |
| 286 | videodb | Cloud video ingest/index/search | VideoDB SDK | no | no | tool wrapper |
| 287 | video-editing | AI-assisted video editing pipeline | FFmpeg, fal, Descript | yes | yes | workflow |
| 288 | visa-doc-translate | OCR visa docs → bilingual PDF | OCR, PDF tools | no | no | tool wrapper |
| 289 | vite-patterns | Vite config/build patterns | none | no | no | reference material |
| 290 | vue-patterns | Vue 3/Nuxt/Pinia patterns | none | yes | no | reference material |
| 291 | windows-desktop-e2e | pywinauto desktop E2E | pywinauto | no | no | reference material |
| 292 | workspace-surface-audit | Audit repo/MCP/plugins, recommend ECC setup | MCP, hooks | yes | partial | workflow |
| 293 | x-api | X/Twitter API posting/search | X API, MCP | yes | partial | tool wrapper |

**Type distribution (primary type, all 293):** reference material ≈ 130 · workflow ≈ 84 · verification ≈ 30 · orchestration ≈ 21 · tool wrapper ≈ 20 · security ≈ 14 · memory ≈ 7 · instruction/prompt ≈ 16 · deterministic automation ≈ 5.

---

## 2. Current OpenCode Capabilities (enumerated)

| Capability class | Inventory | Evidence |
| --- | --- | --- |
| Project skills | 182 | `C:\Opencode\.opencode\skills\` (dirs verified; includes Compound Engineering `ce-*` ×40, `kw-data-*` ×9, `kw-des-*` ×7, `kw-eng-*` ×11, `kw-mkt-*` ×9, `kw-pm-*` ×9, `kw-prod-*` ×2, plus `tdd`, `ado-test-driven-development`, `code-review`, `code-review-and-quality`, `security-and-hardening`, `deep-research`, `documentation-and-adrs`, `git-workflow-and-versioning`, `context-engineering`, `spec-driven-development`, `skill-creator`, `mcp-builder`, `kw-mkt-seo-audit`, `kw-des-accessibility-review`, …) |
| `.claude` skills (loaded) | 19 | `C:\Opencode\.claude\skills\` = `hyperresearch` + 18 pipeline step skills; discovered via `skills.paths` in `C:\Opencode\opencode.json` |
| Superpowers plugin skills | 14 | `C:\Users\flash\.config\opencode\superpowers\skills\` (brainstorming, writing-plans, executing-plans, test-driven-development, systematic-debugging, verification-before-completion, dispatching-parallel-agents, subagent-driven-development, using-git-worktrees, finishing-a-development-branch, requesting/receiving-code-review, writing-skills, using-superpowers) |
| Builtin | 1 | `customize-opencode` |
| Active agents | 239 | `C:\Users\flash\.config\opencode\agents\` (role specialists: Code Reviewer, Penetration Tester, Security Architect, Senior SecOps Engineer, Frontend/Backend Developer, QA, Recruiter, GIS, quant/finance, marketing, etc.) |
| MCP servers | 4 | autoclip (video clip/export/publish), hyperresearch (research vault), context7 (library docs) in `C:\Opencode\opencode.json`; playwright in `C:\Users\flash\.config\opencode\opencode.jsonc` |
| Plugins | 1 | superpowers — only automatic mechanism is `experimental.chat.messages.transform` (first-message injection) |
| Built-in tools | — | bash, read/write/edit, grep/glob, websearch, webfetch, task (subagents), todowrite, context7/autoclip/hyperresearch tool sets, playwright browser tools |
| Memory / context docs | — | `C:\Opencode\CLAUDE.md` (hyperresearch CLI conventions), `C:\Opencode\masterplan\` (workflow/baseline docs), research vault `C:\Opencode\research\` |
| Not active | — | `opencode-skill-pack\skills\` (duplicate), `.claude\agents\` (16 hyperresearch agents not discovered), `.claude\settings.json` hooks (inactive under OpenCode), `C:\Opencode\agent\` + `agent.zip` + Octop libs (inactive) |

---

## 3. Mapping method (A–F outcomes)

Every one of the 293 ECC skills was mapped to zero or more current equivalents by comparing **instructions, workflow phases, inputs/outputs, tools used, enforcement, verification behavior, scope, supported languages, and project integration** — not by name. Outcome classes:

- **A direct** — a current skill/agent has essentially the same purpose and workflow.
- **B functional** — no identical skill, but a combination of existing skills/agents/agents/MCPs provides substantially the same capability.
- **C partial** — the current system covers only part of the ECC capability.
- **D missing** — no meaningful current equivalent (capability relevant to this environment).
- **E irrelevant/incompatible** — not applicable to this environment, or cannot run under this runtime.
- **F redundant in ECC** — the ECC skill duplicates another ECC mechanism (or is deprecated), so it is not an independent missing capability.

`Type` in §5 collapses to the task vocabulary (direct / functional / partial / missing / incompatible / redundant); `Coverage` is full / substantial / partial / none, kept consistent with type (direct→full, functional→substantial, partial→partial, missing/incompatible/redundant→none).

## 4. Name-matching control (why the mapping is not naive)

Two deliberate non-matches and two deliberate matches illustrate the method:

```text
ECC: tdd-workflow                     → not "name-matched"; verified against OP/tdd,
                                        SP/test-driven-development, OP/ado-test-driven-development:
                                        all four run the same red→green→refactor loop      → A direct

ECC: taste / taste-distillation       → current OP/taste-design and OP/taste-skill share the
                                        word "taste" but are UI/anti-slop design systems,
                                        not video aesthetic pipelines                      → NOT a match (E)

ECC: react-performance                → current OP/react-best-practices carries frontmatter
                                        author: "Vercel Engineering" and ECC's own description
                                        cites the same vercel-labs/agent-skills source      → A direct (same corpus)

ECC: documentation-lookup             → current CFG configures the same context7 MCP server
                                        with the same "use current docs, not training data"
                                        contract                                          → A direct
```

---

## 5. Master mapping table (all 293, grouped by capability)

**Distribution of all 293 mappings (mechanically counted from the rows below):** direct 21 · functional 72 · partial 50 · missing 8 · incompatible 140 · redundant 2. Coverage follows type exactly (verified programmatically: 0 mismatches, every one of the 293 ECC skills appears exactly once).

### 5.1 Planning

| ECC Skill | ECC Purpose | Current Replacement | Type | Coverage | Evidence | Gap |
| --- | --- | --- | --- | --- | --- | --- |
| blueprint | One-line objective → multi-session, dependency-graphed build plan with context briefs | ce-plan + writing-plans + wayfinder + to-tickets | functional | substantial | OP/ce-plan, SP/writing-plans, OP/wayfinder, OP/to-tickets | No automatic parallel-step detection graph; planning artifacts are files, not a dependency DAG |
| intent-driven-development | Ambiguous change → verifiable acceptance criteria | requirements-clarity + spec-driven-development + kw-pm-write-spec + to-spec | functional | substantial | OP/requirements-clarity, OP/spec-driven-development, OP/kw-pm-write-spec, OP/to-spec | No dedicated pre-implementation criteria gate |
| plan-canvas | Present plans on a local HTML canvas for human annotation/approval | ce-plan + writing-plans + executing-plans (checkpoint review) | partial | partial | OP/ce-plan, SP/writing-plans, SP/executing-plans | No browser canvas, no click-to-annotate approval surface; human gate is conversational only |
| plan-orchestrate | Read plan → per-step agent chain prompts from an agent catalogue | ce-plan + to-tickets + task (subagent dispatch) + dispatching-parallel-agents | functional | substantial | OP/ce-plan, OP/to-tickets, SP/dispatching-parallel-agents | No generator that emits ready-to-paste orchestration prompts from a plan file |
| product-capability | PRD/roadmap ask → implementation-ready capability plan (constraints, invariants, interfaces) | kw-pm-write-spec + spec-driven-development + kw-eng-system-design | functional | substantial | OP/kw-pm-write-spec, OP/spec-driven-development, OP/kw-eng-system-design | Multi-service invariant surfacing is spread across three skills, not one artifact |
| product-lens | YC-style product diagnostic with go/no-go recommendation | kw-pm-product-brainstorming + ce-pov + kw-pm-synthesize-research | partial | partial | OP/kw-pm-product-brainstorming, OP/ce-pov | No codified PMF-scoring / PRODUCT-BRIEF.md go-no-go artifact |

### 5.2 TDD / Testing

| ECC Skill | ECC Purpose | Current Replacement | Type | Coverage | Evidence | Gap |
| --- | --- | --- | --- | --- | --- | --- |
| tdd-workflow | Fail-first red/green/refactor with 80%+ coverage across unit/integration/E2E | tdd + test-driven-development + ado-test-driven-development | direct | full | OP/tdd, SP/test-driven-development, OP/ado-test-driven-development | None material; ECC's coverage threshold is a prompt convention, not enforced |
| ai-regression-testing | Regression strategies for AI-assisted dev (sandbox API tests, AI blind spots) | kw-eng-testing-strategy + doubt-driven-development + ce-code-review | functional | substantial | OP/kw-eng-testing-strategy, OP/doubt-driven-development, OP/ce-code-review | No codified "same model wrote and reviewed it" blind-spot protocol |
| click-path-audit | Trace user-facing controls through state changes to find cancel-out bugs | webapp-testing + ce-test-browser + playwright browser tools | functional | substantial | OP/webapp-testing, OP/ce-test-browser (MCP playwright) | No scripted "full state-change sequence" audit pass |
| cpp-testing | GoogleTest/CTest configuration and diagnosis | — | incompatible | none | — | No C++ workload in this environment |
| csharp-testing | xUnit/FluentAssertions/mocking patterns | — | incompatible | none | — | No .NET workload |
| django-tdd | pytest-django TDD with factories and coverage | — | incompatible | none | — | No Django workload |
| e2e-testing | Playwright E2E patterns, Page Objects, flaky-test strategy | webapp-testing + browser-testing-with-devtools + ce-test-browser | functional | substantial | OP/webapp-testing, OP/browser-testing-with-devtools, OP/ce-test-browser | Page-Object conventions and artifact/CI recipes not codified |
| fsharp-testing | F# property-based testing | — | incompatible | none | — | No F# workload |
| golang-testing | Table-driven/fuzz/benchmark testing | — | incompatible | none | — | No Go workload |
| kotlin-testing | Kotest/MockK/coroutine testing | — | incompatible | none | — | No Kotlin workload |
| laravel-tdd | Laravel PHPUnit/Pest TDD | — | incompatible | none | — | No PHP workload |
| perl-testing | Test2::V0 / prove / Devel::Cover | — | incompatible | none | — | No Perl workload |
| python-testing | pytest fixtures, mocks, parametrize, coverage | tdd + ado-test-driven-development + kw-eng-testing-strategy | partial | partial | OP/tdd, OP/ado-test-driven-development, OP/kw-eng-testing-strategy | pytest-specific fixtures/factories/parametrization patterns not codified (pytest is the runner for autoclip/webcrawler/quant-research-engine) |
| quarkus-tdd | JUnit 5/Mockito/REST Assured for Quarkus | — | incompatible | none | — | No Java/Quarkus workload |
| react-testing | RTL/Vitest/MSW component testing + a11y assertions | webapp-testing + kw-des-accessibility-review (axe side only) | partial | partial | OP/webapp-testing, OP/kw-des-accessibility-review | No component-unit testing skill (RTL/MSW); only browser-level testing exists |
| rust-testing | Integration/property testing for Rust | — | incompatible | none | — | No Rust workload |
| springboot-tdd | JUnit/Testcontainers for Spring Boot | — | incompatible | none | — | No Java/Spring workload |
| windows-desktop-e2e | pywinauto/Win32 desktop E2E | — | incompatible | none | — | No desktop-app workload |
| healthcare-eval-harness | Patient-safety test gate blocking unsafe deploys | — | incompatible | none | — | No healthcare workload |

### 5.3 Debugging

| ECC Skill | ECC Purpose | Current Replacement | Type | Coverage | Evidence | Gap |
| --- | --- | --- | --- | --- | --- | --- |
| agent-introspection-debugging | Capture → diagnose → contained recovery → introspection report for agent runs | systematic-debugging + diagnosing-bugs + debugging-and-error-recovery + ce-debug | functional | substantial | SP/systematic-debugging, OP/diagnosing-bugs, OP/debugging-and-error-recovery, OP/ce-debug | No mandated "reproducible diagnosis instead of retry" artifact; applies to code defects as well as agent runs |
| network-bgp-diagnostics | BGP neighbor/route troubleshooting | — | incompatible | none | — | No network-gear workload |
| network-config-validation | Pre-deploy router/switch config checks | — | incompatible | none | — | No network-gear workload |
| network-interface-health | Interface error/duplex/flap diagnosis | — | incompatible | none | — | No network-gear workload |

### 5.4 Code Review

| ECC Skill | ECC Purpose | Current Replacement | Type | Coverage | Evidence | Gap |
| --- | --- | --- | --- | --- | --- | --- |
| ai-first-engineering | Review gates and ownership rules when agents write most code | constraint-driven-development + code-review-and-quality + ce-code-review | functional | substantial | OP/constraint-driven-development, OP/code-review-and-quality, OP/ce-code-review | No written team-level ownership/gate policy artifact |
| coding-standards | Baseline naming/readability/immutability conventions applied on review | code-review (Standards axis) + constraint-driven-development + kw-eng-code-review | functional | substantial | OP/code-review, OP/constraint-driven-development, OP/kw-eng-code-review | Standards axis reads `docs/agents/issue-tracker.md` conventions; no standalone cross-project baseline skill |
| codehealth-mcp | CodeScene structural health gates on edits/commits/PRs | kw-eng-tech-debt + ce-code-review + constraint-driven-development | partial | partial | OP/kw-eng-tech-debt, OP/ce-code-review | No continuous structural-metric tool and no delta gate; requires CodeScene MCP (not configured) |
| flutter-dart-code-review | Flutter/Dart review checklist | — | incompatible | none | — | No Flutter workload |
| plankton-code-quality | Write-time auto-format/lint/fix on every edit (hook-enforced) | — | missing | none | CFG (no hooks/permissions configured; enforcement audit: no PreToolUse layer) | Genuine enforcement gap: OpenCode has no write-time formatting hook engine |

### 5.5 Security

| ECC Skill | ECC Purpose | Current Replacement | Type | Coverage | Evidence | Gap |
| --- | --- | --- | --- | --- | --- | --- |
| security-review | Checklist for auth, user input, secrets, API endpoints, payments | security-and-hardening + AG (Security Architect / Senior SecOps / AppSec Engineer) | direct | full | OP/security-and-hardening, AG/security-architect + AG/senior-secops-engineer | None material; ECC's checklist is prompt-level too (neither enforces) |
| security-bounty-hunter | Prioritize remotely reachable, reportable vulnerabilities | security-and-hardening + AG (Penetration Tester) | partial | partial | OP/security-and-hardening, AG/penetration-tester | No bounty-qualification triage (reachability/noise filtering) workflow |
| security-scan | Scan agent config (.claude, settings, MCP, hooks) with AgentShield | — | missing | none | ECC/agent-shield not installed; no config auditor in current stack | Config-injection auditing is absent; enforcement audit flagged AgentShield as an offline-auditor candidate only |
| safety-guard | PreToolUse interception of destructive commands; directory freeze | — | missing | none | CFG (no permission config; `permission.ask` in ECC adapter is contract-violating per enforcement audit) | Genuine hard-guard gap: no rm -rf / force-push / DROP TABLE interception |
| defi-amm-security | Solidity AMM reentrancy/oracle/donation attack checklist | AG (Solidity Smart Contract Engineer) + security-and-hardening | partial | partial | AG/solidity-smart-contract-engineer, OP/security-and-hardening | No DeFi-specific attack-pattern checklist; no EVM project verified in workspace (UNVERIFIED relevance) |
| django-security | Django auth/CSRF/XSS/input security | — | incompatible | none | — | No Django workload (UNVERIFIED: not found in workspace) |
| healthcare-phi-compliance | PHI/PII classification, audit trails, leak vectors | — | incompatible | none | — | No healthcare workload |
| hipaa-compliance | HIPAA entrypoint | — | incompatible | none | — | No healthcare workload |
| laravel-security | Laravel auth/Eloquent/CSRF security | — | incompatible | none | — | No PHP workload |
| llm-trading-agent-security | Trading-agent spend limits/circuit breakers | — | incompatible | none | — | No trading-agent workload |
| perl-security | Perl taint mode/DBI/web security | — | incompatible | none | — | No Perl workload |
| quarkus-security | Quarkus JWT/OIDC/RBAC | — | incompatible | none | — | No Java workload |
| springboot-security | Spring Security authn/authz | — | incompatible | none | — | No Java workload |

### 5.6 Git / GitHub

| ECC Skill | ECC Purpose | Current Replacement | Type | Coverage | Evidence | Gap |
| --- | --- | --- | --- | --- | --- | --- |
| git-workflow | Branching, commit conventions, tidy history, merge vs rebase, conflicts | git-workflow-and-versioning + resolving-merge-conflicts + ce-worktree + SP/using-git-worktrees | direct | full | OP/git-workflow-and-versioning, OP/resolving-merge-conflicts, SP/using-git-worktrees | None material |
| github-ops | gh CLI issue triage, PR/CI/release management, security monitoring | ce-commit-push-pr + ce-babysit-pr + triage + lfg | functional | substantial | OP/ce-commit-push-pr, OP/ce-babysit-pr, OP/triage, OP/lfg | Release-management and CI-failure remediation playbooks not codified |
| opensource-pipeline | Fork → sanitize → package a private repo for safe public release | security-and-hardening (secrets) + git-workflow-and-versioning + ce-commit-push-pr | partial | partial | OP/security-and-hardening, OP/git-workflow-and-versioning | No chained forker/sanitizer/packager agents; no automated secret/fingerprint scrub pass |
| project-flow-ops | GitHub public layer + Linear internal execution layer | triage + ce-sweep + ce-babysit-pr + kw-eng-standup | partial | partial | OP/triage, OP/ce-sweep, OP/ce-babysit-pr | No Linear integration or issue↔PR linking rules |
| repo-scan | Bootstrap pointer that installs an external repo-scan skill | — | incompatible | none | — | Installs an external skill (out of scope for READ-ONLY audit; no repo-scan capability otherwise) |

### 5.7 Research

| ECC Skill | ECC Purpose | Current Replacement | Type | Coverage | Evidence | Gap |
| --- | --- | --- | --- | --- | --- | --- |
| deep-research | Cited multi-source research report (plan → search → deep-read → synthesize) | deep-research (13-agent pipeline) + hyperresearch (16-step pipeline) + research + last30days | direct | full | OP/deep-research, CL/hyperresearch, OP/research, OP/last30days | None; hyperresearch exceeds it (scholarly APIs, adversarial critics, cite-check) |
| research-ops | Evidence-first current-state research with confidence marking | research + hyperresearch + websearch/webfetch | functional | substantial | OP/research, CL/hyperresearch, BUILTIN/websearch | No single-skill "operations" wrapper; capability is spread |
| exa-search | Neural web/code/company search via Exa MCP | websearch + webfetch + hyperresearch search + context7 | functional | substantial | BUILTIN/websearch, CL/hyperresearch, CFG/context7 | No neural code/host/people search surface |
| search-first | Search npm/PyPI/MCP/skills/GitHub before writing custom code | source-driven-development + context7 MCP + websearch | functional | substantial | OP/source-driven-development, CFG/context7, BUILTIN/websearch | Package-ecosystem (npm/PyPI) search is manual, not a defined first step |
| data-scraper-agent | Scheduled, enriching data collection agent for public sources | ce-sweep + webfetch/webfetch + playwright tools + hyperresearch fetch | functional | substantial | OP/ce-sweep, BUILTIN/webfetch, hyperresearch MCP | No free-LLM enrichment loop or scheduled store-and-enrich pipeline |
| market-research | Market sizing, competitor comparison, due diligence with sources | kw-mkt-competitive-brief + kw-pm-competitive-brief + deep-research | functional | substantial | OP/kw-mkt-competitive-brief, OP/kw-pm-competitive-brief, OP/deep-research | TAM/SAM sizing templates not codified |
| benchmark-methodology | Weighted 9-dimension competitor profile scoring | kw-mkt-competitive-brief + kw-pm-competitive-brief | functional | substantial | OP/kw-mkt-competitive-brief, OP/kw-pm-competitive-brief | Fixed 9-dimension scoring rubric absent |
| competitive-platform-analysis | Scope, tier, and filter a competitor set | kw-mkt-competitive-brief + kw-pm-competitive-brief | functional | substantial | OP/kw-mkt-competitive-brief, OP/kw-pm-competitive-brief | Tiering criteria are free-form |
| competitive-report-structure | Assemble scored cards into a decision-grade report | kw-mkt-competitive-brief + kw-mkt-performance-report | functional | substantial | OP/kw-mkt-competitive-brief, OP/kw-mkt-performance-report | White-space/matrix report skeleton absent |
| prediction-market-oracle-research | Prediction markets as data/oracle signals | last30days (Polymarket source) + deep-research + websearch | partial | partial | OP/last30days, OP/deep-research | No source-grounded market-brief structure; domain framing absent |
| scientific-thinking-literature-review | Systematic literature review: screening → synthesis → citation checks | academic-pipeline + deep-research (lit-review mode) + hyperresearch | direct | full | OP/academic-pipeline, OP/deep-research, CL/hyperresearch | None material |
| scientific-thinking-scholar-evaluation | Structured evaluation of scholarly work and evidence quality | academic-paper-reviewer (5-seat panel) + hyperresearch-12-critics | direct | full | OP/academic-paper-reviewer, CL/hyperresearch-12-critics | None material |
| scientific-db-pubmed-database | PubMed/NCBI E-utilities literature workflows | hyperresearch scholar search (OpenAlex/CORE/ClinicalTrials/Europe PMC) | functional | substantial | CL/hyperresearch, CL/hyperresearch-2-width-sweep | Direct NCBI E-utilities/MeSH querying not wired |
| scientific-db-uspto-database | USPTO patent/trademark lookup | — | incompatible | none | — | No patent-research workload |
| scientific-pkg-gget | Genomic/BLAST-style queries via gget | — | incompatible | none | — | No bioinformatics workload |

### 5.8 Documentation

| ECC Skill | ECC Purpose | Current Replacement | Type | Coverage | Evidence | Gap |
| --- | --- | --- | --- | --- | --- | --- |
| architecture-decision-records | Numbered ADRs in docs/adr/ with alternatives, consequences, index | documentation-and-adrs + kw-eng-architecture | direct | full | OP/documentation-and-adrs, OP/kw-eng-architecture | None material |
| code-tour | CodeTour .tour files with file/line anchors for persona tours | gitdiagram + ce-explain + kw-eng-documentation | partial | partial | OP/gitdiagram, OP/ce-explain, OP/kw-eng-documentation | No .tour artifact format or anchored walkthrough generator |
| documentation-lookup | Current library docs via Context7 MCP instead of training data | context7 MCP + source-driven-development | direct | full | CFG/context7, OP/source-driven-development | None (identical mechanism) |
| living-docs-governance | Role-assign project docs and wire harness to canonical sources | documentation-and-adrs + domain-modeling (CONTEXT.md) + ce-compound-refresh + CLAUDE.md | functional | substantial | OP/documentation-and-adrs, OP/domain-modeling, OP/ce-compound-refresh, C:\Opencode\CLAUDE.md | No rot-detection cadence or constitution/map/status/history role schema |

### 5.9 Context Engineering

| ECC Skill | ECC Purpose | Current Replacement | Type | Coverage | Evidence | Gap |
| --- | --- | --- | --- | --- | --- | --- |
| context-budget | Audit context consumption across skills/agents/MCP; prioritize savings | context-engineering (no accounting) | partial | partial | OP/context-engineering, CFG (description-tax ≈29k tokens/session measured in enforcement audit) | No token-accounting/ledger tool producing per-component cost + savings plan |
| config-gc | GC stale skills/memory/hooks/permissions/MCP in ~/.claude | ce-setup + ce-compound-refresh | partial | partial | OP/ce-setup, OP/ce-compound-refresh | No config-wide staleness scanner or guided prune workflow |
| codebase-onboarding | Analyze codebase → onboarding guide, architecture map, starter CLAUDE.md | ce-explain + codebase-design + domain-modeling + kw-eng-documentation | functional | substantial | OP/ce-explain, OP/codebase-design, OP/domain-modeling, OP/kw-eng-documentation | No one-shot "generate onboarding guide" deliverable; CLAUDE.md authoring is manual |
| inherit-legacy-style | Scan implicit conventions → enforceable .ai-style-rules.md | context-engineering + domain-modeling + codebase-design + CLAUDE.md | partial | partial | OP/context-engineering, OP/domain-modeling, C:\Opencode\CLAUDE.md | Convention *enforcement* file has no hook to apply it (enforcement missing) |
| iterative-retrieval | Refine subagent context retrieval across passes | task (subagent prompts) + hyperresearch fetch waves + ce-work | functional | substantial | BUILTIN/task, CL/hyperresearch-2-width-sweep | No codified multi-pass retrieval refinement protocol |
| prompt-optimizer | Diagnose a draft prompt, route to commands/skills, emit optimized prompt | enhance-prompt (UI-specific) + writing-for-agents + skill-creator + ask-matt | partial | partial | OP/enhance-prompt, OP/writing-for-agents, OP/ask-matt | General-purpose prompt diagnosis/routing tool absent; existing ones are UI-prompt or agent-doc specific |
| rules-distill | Extract recurring principles from skills into rule files | ce-compound-refresh + writing-for-agents + writing-skills + context-engineering | functional | substantial | OP/ce-compound-refresh, OP/writing-for-agents, OP/writing-skills | No automated "same principle keeps recurring" detection |
| skill-scout | Search local/marketplace/GitHub/web for existing skills before creating | using-agent-skills + skill-creator + ask-matt | functional | substantial | OP/using-agent-skills, OP/skill-creator, OP/ask-matt | External skill-marketplace/GitHub search not codified |
| skill-stocktake | Batch subagent audit of skill quality (quick scan/full stocktake) | ce-compound-refresh + skill-creator + context-engineering | partial | partial | OP/ce-compound-refresh, OP/skill-creator | No batch quality audit with per-skill verdicts |
| strategic-compact | Compact at logical phase boundaries instead of arbitrary auto-compact | OpenCode built-in compaction + context-engineering | partial | partial | BUILTIN (auto-compact), OP/context-engineering | No phase-gated compaction trigger; auto-compact is size-triggered only |
| token-budget-advisor | Offer response depth (25/50/75/100%) before answering | — | missing | none | — | No response-depth negotiation mechanism (user must ask ad hoc); low marginal value |
| workspace-surface-audit | Audit repo/MCP/plugins/env surfaces; recommend setup | ce-setup + context-engineering + kw-eng-tech-debt | partial | partial | OP/ce-setup, OP/context-engineering | Recommends *ECC-native* additions; current stack has no equivalent "what should I install" audit |

### 5.10 Memory

| ECC Skill | ECC Purpose | Current Replacement | Type | Coverage | Evidence | Gap |
| --- | --- | --- | --- | --- | --- | --- |
| ck | Deterministic per-project memory CLI (/ck save/resume) + SessionStart brief injection | kw-prod-memory-management + ce-handoff/handoff + superpowers first-message injection | functional | substantial | OP/kw-prod-memory-management, OP/ce-handoff, SP plugin transform | No deterministic CLI for save/resume/list; injection is conversation-start only, not per-session brief regeneration |
| unified-memory | Cross-harness Memory Vault shared by Claude/Codex/OpenCode | kw-prod-memory-management + hyperresearch vault + ce-handoff | functional | substantial | OP/kw-prod-memory-management, CL/hyperresearch, OP/ce-handoff | No cross-harness vault (Codex/Cursor share nothing); single-harness memory only |
| continuous-learning-v2 | Instinct capture from sessions with confidence scoring → evolves into skills | ce-compound + ce-compound-refresh + writing-skills | functional | substantial | OP/ce-compound, OP/ce-compound-refresh, OP/writing-skills | No hook-driven automatic capture; learning requires the agent to invoke the skill |
| continuous-learning | Deprecated v1 learning extractor | (superseded by continuous-learning-v2) | redundant | none | ECC (deprecated marker in body) | Not an independent capability |
| growth-log | Extract reusable pattern (root cause → transferable rule) per task | ce-compound | direct | full | OP/ce-compound | None material (format differs; mechanism identical) |
| knowledge-ops | Knowledge base ingest/sync/dedupe/search across stores | hyperresearch vault (notes/index/search/lint/graph) + kw-prod-memory-management | functional | substantial | CL/hyperresearch + hyperresearch MCP tools | No multi-store sync (vector stores, Git repos) layer |

### 5.11 Orchestration

| ECC Skill | ECC Purpose | Current Replacement | Type | Coverage | Evidence | Gap |
| --- | --- | --- | --- | --- | --- | --- |
| orch-pipeline | Gated Research→Plan→TDD→Review→Commit engine with 2 human gates | ce-plan → ce-work → ce-code-review → ce-commit-push-pr (+ SP/executing-plans checkpoints) | functional | substantial | OP/ce-plan, OP/ce-work, OP/ce-code-review, OP/ce-commit-push-pr | Gates are conversational; no mechanical block on plan-unapproved or unreviewed commit |
| orch-add-feature | Orchestrate new feature end to end via ECC agents | ce-work + tdd + ce-code-review + ce-commit-push-pr | functional | substantial | OP/ce-work, OP/tdd, OP/ce-code-review | Same gate caveat; agent map is generic (239 role agents) not phase-bound |
| orch-build-mvp | Bootstrapping MVP from spec with generator-evaluator loop | spec-driven-development + ce-work + ce-prototype + ce-bakeoff | functional | substantial | OP/spec-driven-development, OP/ce-work, OP/ce-prototype, OP/ce-bakeoff | Thin-vertical-slice sequencing not codified |
| orch-change-feature | Change working behavior: update tests first, then code | tdd + ado-test-driven-development + ce-work | functional | substantial | OP/tdd, OP/ado-test-driven-development, OP/ce-work | None material |
| orch-fix-defect | Reproduce bug as failing regression test → fix to green | tdd + ce-debug + systematic-debugging + ce-work | functional | substantial | OP/tdd, OP/ce-debug, SP/systematic-debugging | Capability complete; ECC's phase-boundary enforcement is not |
| orch-refine-code | Behavior-preserving refactor with tests kept green | ce-simplify-code + ce-work + tdd + ce-code-review | functional | substantial | OP/ce-simplify-code, OP/ce-work, OP/tdd | "Green before/after" is instructed, not verified mechanically |
| parallel-execution-optimizer | Task → dependency-graph parallel lanes with isolated write surfaces | dispatching-parallel-agents + subagent-driven-development + to-tickets + wayfinder | functional | substantial | SP/dispatching-parallel-agents, SP/subagent-driven-development, OP/to-tickets, OP/wayfinder | No automated lane matrix or final verification table |
| claude-devfleet | Dispatch parallel coding agents in isolated worktrees, monitor reports | task (subagents) + dispatching-parallel-agents + ce-worktree | functional | substantial | BUILTIN/task, SP/dispatching-parallel-agents, OP/ce-worktree | No structured parallel-run report aggregation |
| dmux-workflows | Parallel agent sessions across harnesses via tmux/dmux | dispatching-parallel-agents + ce-worktree + task | functional | substantial | SP/dispatching-parallel-agents, OP/ce-worktree | No tmux pane manager for agents; parallelism is in-session subagents |
| dev-team | Multi-persona (PM/Architect/Developer/QA) session on one problem | task (multi-agent) + ce-bakeoff + ce-pov | functional | substantial | BUILTIN/task, OP/ce-bakeoff, OP/ce-pov | Persona roster is ad hoc (239 agents available but no fixed 4-role ritual) |
| team-builder | Discover agent personas, pick up to 5, dispatch in parallel | task (subagent_type) + dispatching-parallel-agents | functional | substantial | BUILTIN/task (agent list), SP/dispatching-parallel-agents | No interactive picker UI |
| team-agent-orchestration | Agent squads: work items, Kanban state, branch isolation, merge gates | subagent-driven-development + task + ce-worktree | partial | partial | SP/subagent-driven-development, OP/ce-worktree | No Kanban board state or merge-gate enforcement for multi-agent work |
| agentic-os | Persistent multi-agent OS: kernel, scheduled automation, state | OpenCode agents + kw-prod-task-management + ce-sweep (scheduled) | partial | partial | AG (239), OP/kw-prod-task-management, OP/ce-sweep | No session scheduler/state kernel inside the harness |
| autonomous-agent-harness | Fully autonomous agent with memory, scheduling, task queue | lfg + ce-work + ce-sweep | partial | partial | OP/lfg, OP/ce-work, OP/ce-sweep | No computer-use/task-queue primitives; Claude Code-specific |
| autonomous-loops | Autonomous loop patterns (compat shim) | (retained in ECC only; superseded by continuous-agent-loop) | redundant | none | ECC (body says retained for compatibility) | Not an independent capability |
| continuous-agent-loop | Autonomous loops with quality gates, evals, recovery | lfg + ce-work + constraint-driven-development | partial | partial | OP/lfg, OP/ce-work, OP/constraint-driven-development | Eval gates inside the loop are absent (see eval-harness §5.12) |
| dynamic-workflow-mode | Task-local harnesses, eval gates, reusable skill extraction | skill-creator + ce-work + writing-skills | partial | partial | OP/skill-creator, OP/writing-skills | Eval-gate primitive absent |
| enterprise-agent-ops | Lifecycle, observability, least-privilege scopes, kill switches | observability-and-instrumentation + shipping-and-launch + AG (SRE) | partial | partial | OP/observability-and-instrumentation, OP/shipping-and-launch, AG/sre | No kill switch / runtime lifecycle control for long-lived agents |
| gan-style-harness | Generator-Evaluator autonomous build harness | ce-bakeoff + ce-optimize + ce-prototype | partial | partial | OP/ce-bakeoff, OP/ce-optimize, OP/ce-prototype | No autonomous generator/evaluator alternation loop |
| loop-design-check | Design/review agent loops for spinning/Goodhart/wrong-answer modes | — | missing | none | — | No agent-loop design review checklist (marginal but unique) |
| ralphinho-rfc-pipeline | RFC → work-unit DAG with per-unit research/plan/test/review and merge queue | wayfinder + to-tickets + dispatching-parallel-agents + ce-worktree | partial | partial | OP/wayfinder, OP/to-tickets, SP/dispatching-parallel-agents | No RFC splitter, acceptance-test binding, or queued merge discipline |
| agent-harness-construction | Design agent action spaces, tool definitions, observation format | customize-opencode + skill-creator + mcp-builder + AG (Multi-Agent Systems Architect) | functional | substantial | BUILTIN/customize-opencode, OP/skill-creator, OP/mcp-builder, AG/multi-agent-systems-architect | No eval-driven action-space tuning method |
| agentic-engineering | Eval-first execution, decomposition, cost-aware model routing | ce-plan + ce-work + ce-optimize + task | functional | substantial | OP/ce-plan, OP/ce-work, OP/ce-optimize | Cost-aware model routing not configurable per task |

### 5.12 Verification

| ECC Skill | ECC Purpose | Current Replacement | Type | Coverage | Evidence | Gap |
| --- | --- | --- | --- | --- | --- | --- |
| verification-loop | Six-phase check (build, types, lint, tests, security grep, diff) → PASS/FAIL report | verification-before-completion + kw-eng-deploy-checklist + kw-data-validate-data | functional | substantial | SP/verification-before-completion, OP/kw-eng-deploy-checklist, OP/kw-data-validate-data | No structured PASS/FAIL artifact; security grep phase not standard |
| delivery-gate | Stop hook blocks finishing until checks pass (anti-rationalization) | verification-before-completion (prompt only) | partial | partial | SP/verification-before-completion | No Stop-time block: nothing prevents an unverified "done" claim (enforcement) |
| gateguard | Deny first Edit/Write/Bash until concrete facts are presented | — | missing | none | CFG (no PreToolUse/permission layer; enforcement audit) | Genuine hard-guard gap (fact-forcing gate) |
| hookify-rules | Declarative markdown rules matching bash/file/prompt/stop events → warn/block | superpowers `experimental.chat.messages.transform` (message injection only) | missing | none | SP plugin config in `C:\Users\flash\.config\opencode\opencode.jsonc` | No event-matching warn/block rule engine; only first-message injection is automatic |
| eval-harness | Eval-driven development: define evals, graders, track pass@k/pass^k | ce-retune (skill-corpus A/B only) | partial | partial | OP/ce-retune | No coding-session eval harness, graders, or reliability tracking — closest existing is test frameworks |
| agent-eval | Head-to-head comparison of coding agents on custom tasks | ce-bakeoff (competing solutions, not agents) | partial | partial | OP/ce-bakeoff | No agent-vs-agent benchmark with pass rate/cost/consistency |
| agent-self-evaluation | Post-task self-rating on 5 axes with evidence | verification-before-completion + ce-proof (adjacent) | partial | partial | SP/verification-before-completion, OP/ce-proof | No 1–5 scored self-rating rubric; and neither mechanism is enforced |
| agent-architecture-audit | 12-layer audit of agent/LLM application stack | ce-pov + code-review-and-quality + AG (AI Engineer) | partial | partial | OP/ce-pov, OP/code-review-and-quality, AG/ai-engineer | No layered agent-stack diagnostic checklist (memory pollution, hidden repair loops) |
| santa-method | Two independent reviewers must both pass + fix/re-review loop | code-review (two parallel sub-agents) + ce-code-review + doubt-driven-development | functional | substantial | OP/code-review, OP/ce-code-review, OP/doubt-driven-development | "Both must pass" is not a gate — findings are reported, not blocking |
| skill-comply | Measure whether skills/rules are actually followed (compliance rates) | — | missing | none | — | Nothing measures instruction adherence; this is the "prompt ≠ enforcement" measurement gap |
| benchmark | Perf baselines (CWV, API latency, build time) with regression detection | performance-optimization + performance-optimizer + kw-eng-deploy-checklist | functional | substantial | OP/performance-optimization, OP/performance-optimizer | No persisted before/after baseline store |
| benchmark-optimization-loop | Bounded measured optimize loop with correctness gate and promotion | ce-optimize | direct | full | OP/ce-optimize | None material |
| browser-qa | Post-deploy UI verification (console errors, CWV, forms, auth) | webapp-testing + ce-dogfood + playwright tools + ce-test-browser | functional | substantial | OP/webapp-testing, OP/ce-dogfood, OP/ce-test-browser | No post-deploy smoke run against a live URL by default |
| canary-watch | Monitor a deployed URL after releases (endpoints, SSE, assets) | kw-eng-deploy-checklist + shipping-and-launch + observability-and-instrumentation | partial | partial | OP/kw-eng-deploy-checklist, OP/shipping-and-launch | No continuous post-deploy watch/smoke automation |
| production-audit | Local-evidence production readiness audit | kw-eng-deploy-checklist + shipping-and-launch + ce-dogfood | functional | substantial | OP/kw-eng-deploy-checklist, OP/shipping-and-launch, OP/ce-dogfood | Severity-ranked "what breaks in prod" output format absent |
| terminal-ops | Evidence-first command execution with proof of verification | bash + verification-before-completion + kw-eng-debug | functional | substantial | BUILTIN/bash, SP/verification-before-completion | Proof artifact is conversational, not a log file |
| operator-approval-loop | Human approval contract for agent-drafted outbound messages | autoclip publish (unguarded) | partial | partial | autoclip MCP publish_clip (CFG/autoclip) | No hashed-draft/approval/claim protocol before outbound publishing |
| prediction-market-risk-review | Compliance/privacy/execution risk review of market workflows | kw-eng-code-review + security-and-hardening | partial | partial | OP/kw-eng-code-review, OP/security-and-hardening | Domain-specific risk rubric absent |
| django-verification | Django lint/type/test/security verification loop | verification-before-completion + kw-eng-deploy-checklist | partial | partial | SP/verification-before-completion | Django toolchain steps not codified — and no Django workload (also E) |
| laravel-verification | Laravel verification loop | verification-before-completion | partial | partial | SP/verification-before-completion | No PHP workload (also E) |
| quarkus-verification | Quarkus build/static-analysis/coverage loop | verification-before-completion | partial | partial | SP/verification-before-completion | No Java workload (also E) |
| springboot-verification | Spring Boot build/scan/coverage loop | verification-before-completion | partial | partial | SP/verification-before-completion | No Java workload (also E) |
| recursive-decision-ledger | Append-only decision ledger for recursive rollouts with promotion gates | — | incompatible | none | — | Tied to live-trading rollouts; no equivalent workload (UNVERIFIED) |

### 5.13 Other

#### 5.13.1 Languages/frameworks present in this environment (Python, Node, React/Next)

| ECC Skill | ECC Purpose | Current Replacement | Type | Coverage | Evidence | Gap |
| --- | --- | --- | --- | --- | --- | --- |
| python-patterns | PEP 8, idiomatic Python, type hints | constraint-driven-development + code-review (standards axis) | partial | partial | OP/constraint-driven-development, OP/code-review | No Python-specific style/typing reference skill (Python drives autoclip, webcrawler, quant-research-engine, evidence-engine) |
| backend-patterns | Node/Express/Next API + DB patterns | typed-service-contracts + api-and-interface-design + nextjs-app-router-patterns | functional | substantial | OP/typed-service-contracts, OP/api-and-interface-design, OP/nextjs-app-router-patterns | Express-specific recipes not codified |
| error-handling | Typed errors, retries, circuit breakers, user-facing messages | debugging-and-error-recovery + kw-eng-debug + typed-service-contracts | functional | substantial | OP/debugging-and-error-recovery, OP/kw-eng-debug, OP/typed-service-contracts | Retry/circuit-breaker reference patterns absent |
| api-design | REST resource naming, status codes, pagination, versioning | api-and-interface-design + kw-eng-system-design | functional | substantial | OP/api-and-interface-design, OP/kw-eng-system-design | Rate-limit/pagination conventions not spelled out |
| api-connector-builder | Add a provider by cloning the repo's existing integration pattern | api-and-interface-design + codebase-design + source-driven-development | functional | substantial | OP/api-and-interface-design, OP/codebase-design, OP/source-driven-development | "Match existing pattern exactly" discipline is generic, not integration-specific |
| contract-first | One authoritative OpenAPI/AsyncAPI/Protobuf/JSON-Schema contract | api-and-interface-design + typed-service-contracts + zod-validation-expert | functional | substantial | OP/api-and-interface-design, OP/typed-service-contracts, OP/zod-validation-expert | Generated consumer types + contract-verified integration step not automated |
| postgres-patterns | PostgreSQL schema design, indexing, RLS | kw-data-sql-queries + kw-data-write-query | functional | substantial | OP/kw-data-sql-queries, OP/kw-data-write-query | Schema/RLS design guidance not codified (queries are) |
| database-migrations | Forward-only, expand-contract, concurrent indexes, backfills | deprecation-and-migration + kw-eng-deploy-checklist | functional | substantial | OP/deprecation-and-migration, OP/kw-eng-deploy-checklist | Per-tool (Prisma/Drizzle/Kysely) recipes absent |
| deployment-patterns | CI/CD, Docker, health checks, rollback, readiness checklists | ci-cd-and-automation + shipping-and-launch + kw-eng-deploy-checklist | functional | substantial | OP/ci-cd-and-automation, OP/shipping-and-launch, OP/kw-eng-deploy-checklist | None material |
| docker-patterns | Dockerfile/Compose local dev, hardening, volumes, networking | ci-cd-and-automation + kw-eng-deploy-checklist | partial | partial | OP/ci-cd-and-automation, OP/kw-eng-deploy-checklist | No Dockerfile/Compose reference skill (containers are used but undocumented) |
| mcp-server-patterns | Build MCP servers (Node SDK, Zod, stdio/HTTP) | mcp-builder + AG (MCP Builder) | direct | full | OP/mcp-builder, AG/mcp-builder | None material |
| hexagonal-architecture | Ports & Adapters, dependency inversion, testable use cases | codebase-design + kw-eng-architecture + domain-modeling | functional | substantial | OP/codebase-design, OP/kw-eng-architecture, OP/domain-modeling | None material |
| react-patterns | React 18/19 hooks discipline, boundaries, forms, state trees | react-best-practices + nextjs-app-router-patterns + frontend-ui-engineering | functional | substantial | OP/react-best-practices, OP/nextjs-app-router-patterns, OP/frontend-ui-engineering | State-decision-tree and form-actions guidance spread across three skills |
| react-performance | Vercel 40+ React/Next perf rules (8 priority categories) | react-best-practices (same Vercel author/provenance) | direct | full | OP/react-best-practices (frontmatter author: Vercel Engineering) | None — same source corpus |
| nextjs-turbopack | Next 16 / Turbopack, caching, proxy.ts migration | nextjs-app-router-patterns + react-best-practices | partial | partial | OP/nextjs-app-router-patterns, OP/react-best-practices | Bundler/migration specifics absent |
| frontend-patterns | React/Next component + state management + perf patterns | frontend-ui-engineering + react-best-practices + ui-styling | functional | substantial | OP/frontend-ui-engineering, OP/react-best-practices, OP/ui-styling | None material |
| ui-to-vue | Screenshots/design exports → Vue 3 components | image-to-code-skill + react-components | partial | partial | OP/image-to-code-skill, OP/react-components | Output targets React/Vite, not Vue (no Vue workload here) |

#### 5.13.2 Languages/frameworks not present (incompatible)

| ECC Skill | ECC Purpose | Current Replacement | Type | Coverage | Evidence | Gap |
| --- | --- | --- | --- | --- | --- | --- |
| android-clean-architecture | Android/KMP module + layer rules | — | incompatible | none | — | No Android workload |
| angular-developer | Angular codegen + signals/DI guidance | — | incompatible | none | — | No Angular workload |
| bun-runtime | Bun runtime/packager/test runner | — | incompatible | none | — | No Bun workload |
| compose-multiplatform-patterns | KMP/Jetpack Compose UI | — | incompatible | none | — | No Kotlin workload |
| dart-flutter-patterns | Flutter state/navigation/DI | — | incompatible | none | — | No Flutter workload |
| dotnet-patterns | C#/.NET DI + async | — | incompatible | none | — | No .NET workload |
| fastapi-patterns | FastAPI/Pydantic service layout | typed-service-contracts (generic) | incompatible | none | — | No FastAPI project confirmed (UNVERIFIED) |
| golang-patterns | Idiomatic Go | — | incompatible | none | — | No Go workload |
| java-coding-standards | Java/Spring/Quarkus conventions | — | incompatible | none | — | No Java workload |
| jpa-patterns | JPA/Hibernate entities | — | incompatible | none | — | No Java workload |
| kotlin-coroutines-flows | Kotlin coroutines/Flow | — | incompatible | none | — | No Kotlin workload |
| kotlin-exposed-patterns | Exposed ORM | — | incompatible | none | — | No Kotlin workload |
| kotlin-ktor-patterns | Ktor server | — | incompatible | none | — | No Kotlin workload |
| kotlin-patterns | Idiomatic Kotlin | — | incompatible | none | — | No Kotlin workload |
| laravel-patterns | Laravel architecture/Eloquent | — | incompatible | none | — | No PHP workload |
| laravel-plugin-discovery | LaraPlugins.io package search | — | incompatible | none | — | No PHP workload |
| nestjs-patterns | NestJS modules/providers | — | incompatible | none | — | No NestJS workload |
| nuxt4-patterns | Nuxt 4 SSR/hydration | — | incompatible | none | — | No Vue/Nuxt workload |
| prisma-patterns | Prisma schema/queries | kw-data-sql-queries (SQL-level only) | incompatible | none | — | No Prisma project confirmed (UNVERIFIED) |
| pytorch-patterns | PyTorch training pipelines | — | incompatible | none | — | No PyTorch workload confirmed (UNVERIFIED) |
| quarkus-patterns | Quarkus 3 architecture | — | incompatible | none | — | No Java workload |
| rails-patterns | Rails 7.1+/8 patterns | — | incompatible | none | — | No Ruby workload |
| react-native-patterns | React Native/Expo | — | incompatible | none | — | No mobile workload |
| redis-patterns | Redis cache/lock/rate-limit | — | incompatible | none | — | No Redis workload confirmed (UNVERIFIED) |
| rust-patterns | Idiomatic Rust | — | incompatible | none | — | No Rust workload |
| springboot-patterns | Spring Boot architecture | — | incompatible | none | — | No Java workload |
| swift-actor-persistence | Swift actor persistence | — | incompatible | none | — | No Swift workload |
| swift-concurrency-6-2 | Swift 6.2 concurrency | — | incompatible | none | — | No Swift workload |
| swift-protocol-di-testing | Swift protocol DI testing | — | incompatible | none | — | No Swift workload |
| swiftui-patterns | SwiftUI architecture | — | incompatible | none | — | No Swift workload |
| vite-patterns | Vite config/build | — | incompatible | none | — | No Vite project confirmed (UNVERIFIED) |
| vue-patterns | Vue 3/Pinia/Nuxt | — | incompatible | none | — | No Vue workload |
| tinystruct-patterns | tinystruct Java framework | — | incompatible | none | — | Obscure framework, no workload |
| mysql-patterns | MySQL schema/index (deprecated) | kw-data-sql-queries (generic SQL) | incompatible | none | — | Deprecated in ECC and no MySQL workload |
| nodejs-keccak256 | Ethereum Keccak-256 correctness | — | incompatible | none | — | No EVM workload (UNVERIFIED) |
| evm-token-decimals | EVM decimal safety | — | incompatible | none | — | No EVM workload (UNVERIFIED) |
| clickhouse-io | ClickHouse analytics patterns | kw-data-sql-queries (PostgreSQL-first) | incompatible | none | — | No ClickHouse workload |

#### 5.13.3 Additional out-of-stack languages/frameworks

| ECC Skill | ECC Purpose | Current Replacement | Type | Coverage | Evidence | Gap |
| --- | --- | --- | --- | --- | --- | --- |
| cpp-coding-standards | C++ Core Guidelines, RAII, modern C++ | — | incompatible | none | — | No C++ workload (UNVERIFIED: none confirmed in workspace) |
| django-celery | Celery task queues in Django | — | incompatible | none | — | No Django/Celery workload confirmed (UNVERIFIED) |
| django-patterns | Django app layout, ORM, admin | — | incompatible | none | — | No Django workload confirmed (UNVERIFIED) |
| perl-patterns | Perl 5 idioms, testing, signatures | — | incompatible | none | — | No Perl workload |

#### 5.13.4 Domain / industry expertise (incompatible)

| ECC Skill | ECC Purpose | Current Replacement | Type | Coverage | Evidence | Gap |
| --- | --- | --- | --- | --- | --- | --- |
| carrier-relationship-management | Ocean/air carrier contracts, rate cards | — | incompatible | none | — | No logistics workload |
| cisco-ios-patterns | Cisco IOS/ASA config validation | — | incompatible | none | — | No network-vendor workload (diagnostics skills differ) |
| connections-optimizer | LinkedIn connections inbox triage | — | incompatible | none | — | No social-graph workload |
| counterparty-channel-discipline | Financial counterparty messaging rules | — | incompatible | none | — | No fintech comms workload |
| customs-trade-compliance | Export control / HS classification | — | incompatible | none | — | No trade-compliance workload |
| customer-billing-ops | Dunning, disputes, invoicing | — | incompatible | none | — | No billing-ops workload (UNVERIFIED) |
| energy-procurement | Utility tariff analysis / PPAs | — | incompatible | none | — | No energy workload |
| foundation-models-on-device | iOS/Android on-device model integration | — | incompatible | none | — | No mobile workload |
| healthcare-cdss-patterns | Clinical decision support patterns | — | incompatible | none | — | No clinical workload |
| healthcare-emr-patterns | HL7/FHIR, EHR integration | — | incompatible | none | — | No EHR workload |
| homelab-network-readiness | Homelab network assessment | — | incompatible | none | — | No homelab workload |
| homelab-network-setup | VLAN, DNS, VPN homelab setup | — | incompatible | none | — | No homelab workload |
| homelab-pihole-dns | Pi-hole DNS configuration | — | incompatible | none | — | No homelab workload |
| homelab-vlan-segmentation | VLAN segmentation for homelab | — | incompatible | none | — | No homelab workload |
| homelab-wireguard-vpn | WireGuard VPN setup | — | incompatible | none | — | No homelab workload |
| inventory-demand-planning | Forecasting, safety stock | — | incompatible | none | — | No supply-chain workload |
| investor-materials | Investor memo / update drafts | — | incompatible | none | — | No investor-relations workload |
| investor-outreach | Investor outreach sequences | — | incompatible | none | — | No fundraising workload |
| lead-intelligence | B2B lead enrichment scoring | — | incompatible | none | — | No sales workload |
| logistics-exception-management | Shipment exception handling | — | incompatible | none | — | No logistics workload |
| master-agreement-generator | Master service agreement drafts | — | incompatible | none | — | No legal-workload (legal skills are for law firms) |
| production-scheduling | Shop-floor scheduling | — | incompatible | none | — | No manufacturing workload |
| quality-nonconformance | Nonconformance / CAPA records | — | incompatible | none | — | No manufacturing workload |
| recsys-pipeline-architect | Recommendation system design | — | incompatible | none | — | No recsys workload |
| returns-reverse-logistics | Returns / reverse logistics | — | incompatible | none | — | No e-commerce ops workload |
| social-graph-ranker | Social engagement ranking | — | incompatible | none | — | No social-platform workload |
| visa-doc-translate | Visa document translation | — | incompatible | none | — | No immigration workload |
| ios-icon-gen | App icon generation pipeline | — | incompatible | none | — | No iOS workload |

#### 5.13.5 Marketing / content / platform (functional gaps, not installed)

| ECC Skill | ECC Purpose | Current Replacement | Type | Coverage | Evidence | Gap |
| --- | --- | --- | --- | --- | --- | --- |
| article-writing | Long-form article structure + voice | content-research-writer + ce-noslop + stop-slop | functional | substantial | OP/content-research-writer, OP/ce-noslop, OP/stop-slop | No SEO-keyword-first article outline (article-writing) |
| brand-discovery | Brand discovery questionnaire → positioning | brand + brandkit | functional | substantial | OP/brand, OP/brandkit | Positioning questionnaire flow not codified |
| brand-voice | Extract a reusable brand-voice spec | brand + kw-mkt-brand-review | functional | substantial | OP/brand, OP/kw-mkt-brand-review | Voice-extraction → spec file artifact missing |
| content-engine | Repeatable content production engine | kw-mkt-content-creation + content-research-writer | functional | substantial | OP/kw-mkt-content-creation, OP/content-research-writer | Calendar/engine loop not assembled |
| crosspost | Syndicate one post across platforms | (none assembled) | partial | partial | — | No cross-posting skill (publish MCPs exist separately) |
| marketing-campaign | Full campaign brief + calendar | kw-mkt-campaign-plan | direct | full | OP/kw-mkt-campaign-plan | None |
| seo | On-page SEO audit + keyword gap | kw-mkt-seo-audit | direct | full | OP/kw-mkt-seo-audit | None |
| social-publisher | Publish to social platforms | autoclip publish (Upload-Post) | functional | substantial | MCP autoclip publish_clip | Capable via MCP; skill-level caption logic absent |
| x-api | X/Twitter API operations | — | partial | partial | MCP autoclip (X via Upload-Post) | Direct X API skill not present |

#### 5.13.6 Design / frontend / motion (design skills present, ECC-specific ones not)

| ECC Skill | ECC Purpose | Current Replacement | Type | Coverage | Evidence | Gap |
| --- | --- | --- | --- | --- | --- | --- |
| accessibility | WCAG-oriented a11y review | kw-des-accessibility-review + frontend-ui-engineering | direct | full | OP/kw-des-accessibility-review, OP/frontend-ui-engineering | None material |
| design-system | Token architecture + component specs | design-system + kw-des-design-system + tailwind-design-system | direct | full | OP/design-system, OP/kw-des-design-system, OP/tailwind-design-system | None material |
| frontend-a11y | Frontend accessibility checklist | kw-des-accessibility-review | direct | full | OP/kw-des-accessibility-review | None material |
| frontend-design-direction | Visual direction / moodboards | taste-design + ui-ux-pro-max + taste-skill | functional | substantial | OP/taste-design, OP/ui-ux-pro-max, OP/taste-skill | Direction-board artifact not codified |
| frontend-slides | Slide decks from HTML | slides + pptx | direct | full | OP/slides, OP/pptx | None |
| liquid-glass-design | visionOS Liquid Glass styling | — | incompatible | none | — | No visionOS workload |
| make-interfaces-feel-better | Micro-interaction polish pass | frontend-ui-engineering + ui-styling + ce-polish | functional | substantial | OP/frontend-ui-engineering, OP/ui-styling, OP/ce-polish | None material |
| motion-advanced | Advanced motion design (GSAP) | ui-ux-pro-max (GSAP presets) | functional | substantial | OP/ui-ux-pro-max | Advanced choreography recipes not codified |
| motion-foundations | Motion design fundamentals | ui-ux-pro-max + frontend-ui-engineering | functional | substantial | OP/ui-ux-pro-max, OP/frontend-ui-engineering | None material |
| motion-patterns | Common motion patterns | ui-ux-pro-max | partial | partial | OP/ui-ux-pro-max | Pattern library (enter/exit/scroll) not enumerated |

#### 5.13.7 Media / video / image (incompatible — no such workload)

| ECC Skill | ECC Purpose | Current Replacement | Type | Coverage | Evidence | Gap |
| --- | --- | --- | --- | --- | --- | --- |
| blender-motion-state-inspection | Inspect Blender motion state | — | incompatible | none | — | No Blender workload |
| fal-ai-media | fal.ai image/video generation | — | incompatible | none | — | No media-gen workload (design skill uses Gemini) |
| manim-video | Math animation videos | — | incompatible | none | — | No animation workload |
| remotion-video-creation | Programmatic React video | — | incompatible | none | — | No programmatic-video workload (video editing exists) |
| taste | Taste grading of designs | taste-skill / taste-design (name-similar, different provenance) | incompatible | none | OP/taste-skill | ECC `taste` is a specific model-graded aesthetic harness — NOT the OpenCode `taste-*` skills (see §4) |
| taste-application | Apply taste rules to output | taste-skill | incompatible | none | — | Same: different skill family |
| taste-distillation | Distill taste rules from references | taste-design | incompatible | none | — | Same |
| tasteforge-video | Video taste evaluation | — | incompatible | none | — | No video-taste workload |
| ui-demo | UI demo clips | — | incompatible | none | — | No demo-clip workload |
| video-editing | Video editing workflows | autoclip clip_video / Short-Video Editing Coach (agent) | functional | substantial | MCP autoclip, AG Short-Video Editing Coach | Skill form absent; capability exists via MCP + agent |
| videodb | Video database indexing | — | incompatible | none | — | No video-DB workload |

#### 5.13.8 Engineering patterns / data / ML (no matching workload assembled)

| ECC Skill | ECC Purpose | Current Replacement | Type | Coverage | Evidence | Gap |
| --- | --- | --- | --- | --- | --- | --- |
| content-hash-cache-pattern | Content-hash caching | — | partial | partial | — | Caching guidance exists inside performance skills only |
| cost-aware-llm-pipeline | LLM cost-aware pipeline design | autoclip_list_providers (config-level) | partial | partial | MCP autoclip_list_providers | No cost-budget pipeline pattern |
| cost-tracking | Per-run token/cost accounting | hyperresearch `run report -j` (spend telemetry) | functional | substantial | CLAUDE.md run report | Only for research runs, not general |
| council | Multi-model council decision | ce-pov (oracle panel) | direct | full | OP/ce-pov | None material |
| council-multi-model | Multi-model parallel opinions | ce-pov | direct | full | OP/ce-pov | None material |
| dashboard-builder | Metric dashboards | kw-data-build-dashboard | direct | full | OP/kw-data-build-dashboard | None |
| data-throughput-accelerator | Batch throughput acceleration | — | incompatible | none | — | No high-throughput pipeline workload (UNVERIFIED) |
| latency-critical-systems | Latency-critical system design | performance-optimization + performance-optimizer | functional | substantial | OP/performance-optimization, OP/performance-optimizer | p99-specific playbooks absent |
| ml-adoption-playbook | ML adoption roadmap | — | incompatible | none | — | No ML-adoption workload |
| mle-workflow | ML engineering workflow | kw-data-statistical-analysis + kw-data-explore-data | partial | partial | OP/kw-data-statistical-analysis | MLOps pipeline (training/serving) absent |
| regex-vs-llm-structured-text | Regex vs LLM for text extraction | — | partial | partial | — | Decision framework not codified (CE skills cover the judgment generically) |

#### 5.13.9 Tooling / environments not configured (incompatible)

| ECC Skill | ECC Purpose | Current Replacement | Type | Coverage | Evidence | Gap |
| --- | --- | --- | --- | --- | --- | --- |
| esign-field-placement | E-signature field placement | — | incompatible | none | — | No e-sign workload |
| flox-environments | Flox reproducible envs | — | incompatible | none | — | No Flox tooling |
| generating-python-installer | PyInstaller packaging | — | incompatible | none | — | No desktop-installer workload (UNVERIFIED) |
| google-workspace-ops | Drive/Gmail/Calendar ops | — | incompatible | none | — | No Google Workspace integration configured (UNVERIFIED) |
| i18n-sync | Locale file synchronisation | — | incompatible | none | — | No i18n workload confirmed (UNVERIFIED) |
| ito-baskets | ITO investment baskets | — | incompatible | none | — | No ITO workload (quant-research-engine ≠ ITO) |
| ito-compute | ITO compute allocation | — | incompatible | none | — | No ITO workload |
| ito-inference | ITO inference allocation | — | incompatible | none | — | No ITO workload |
| ito-training | ITO training allocation | — | incompatible | none | — | No ITO workload |
| jira-integration | Jira issue operations | — | incompatible | none | — | No Jira configured (to-tickets targets local/tracker) |
| kubernetes-patterns | K8s manifests/operators | — | incompatible | none | — | No Kubernetes workload confirmed (UNVERIFIED) |
| mailtrap-email-integration | Mailtrap test email | — | incompatible | none | — | No email-integration workload |
| netmiko-ssh-automation | Network device SSH automation | — | incompatible | none | — | No network-device workload |
| nutrient-document-processing | PDF parsing/editing SDK | pdf + docx | functional | substantial | OP/pdf, OP/docx | Nutrient SDK-specific APIs absent |
| uncloud | Multi-cloud resource control | — | incompatible | none | — | No cloud-account integration configured (UNVERIFIED) |

#### 5.13.10 ECC-internal / harness-specific (incompatible by design)

| ECC Skill | ECC Purpose | Current Replacement | Type | Coverage | Evidence | Gap |
| --- | --- | --- | --- | --- | --- | --- |
| agent-payment-x402 | x402 agent payments (deprecated) | — | incompatible | none | — | Deprecated; no payment workload |
| agent-sort | Route skills to agents (ECC plugin) | — | incompatible | none | — | ECC plugin internal; OpenCode agents pre-assigned |
| automation-audit-ops | Audit ECC automation rules | audit_ecc_enforcement.md (one-off) | incompatible | none | C:\Opencode\audit_ecc_enforcement.md | No recurring automation auditor |
| configure-ecc | ECC installer/configurator | — | incompatible | none | — | ECC not installed as framework (decision) |
| ecc-guide | ECC documentation router | — | incompatible | none | — | ECC not installed |
| ecc-recipes | ECC task recipes | — | incompatible | none | — | ECC not installed |
| ecc-tools-cost-audit | ECC tool-cost audit | — | incompatible | none | — | ECC not installed |
| email-ops | Email operations | — | incompatible | none | — | No email MCP configured (UNVERIFIED) |
| finance-billing-ops | Finance/billing ops | — | incompatible | none | — | No billing system configured (UNVERIFIED) |
| hermes-imports | Hermes import migration | — | incompatible | none | — | ECC-specific migration |
| messages-ops | Message delivery ops | — | incompatible | none | — | ECC-specific |
| nanoclaw-repl | NanoClaw REPL control | — | incompatible | none | — | ECC-specific harness |
| nasiko-control-plane | Nasiko control plane | — | incompatible | none | — | ECC-specific harness |
| openclaw-persona-forge | OpenClaw persona creation | — | incompatible | none | — | ECC-specific harness |
| terminal-opener | Codex terminal opener | playwright_browser_* (browser only) | incompatible | none | MCP playwright | Codex-specific; no terminal-UI automation configured |
| unified-notifications-ops | Notification routing (OpenCode mentioned) | — | partial | partial | ecc flags opencode_mention=5 | Mentions OpenCode but no notification integration configured (UNVERIFIED) |

---

## 6. Capability groups

Each group: the ECC skills in it (full rows in §5), the current equivalents, what remains uncovered.

### Planning

- **ECC skills (6):** blueprint, intent-driven-development, plan-canvas, plan-orchestrate, product-capability, product-lens
- **→ current equivalents:** ce-plan, writing-plans, plan-writing, spec-driven-development, requirements-clarity, kw-pm-write-spec, to-spec, kw-eng-system-design, wayfinder, to-tickets, ce-brainstorm, brainstorming, interview-me, grill-me, to-questionnaire, ce-strategy
- **→ remaining gaps:** dependency-graphed multi-session build plan carrying per-step context briefs (blueprint, functional); a browser canvas where a human approves the plan and an unfinished plan blocks stopping (plan-canvas, partial — the *hook* part is unique); no hard pre-implementation acceptance-criteria gate (intent-driven-development). ECC's planning is prompt-level too; only plan-canvas has a real hook.

### TDD / Testing

- **ECC skills (19):** tdd-workflow, ai-regression-testing, click-path-audit, e2e-testing, python-testing, react-testing, cpp-testing, csharp-testing, fsharp-testing, golang-testing, kotlin-testing, laravel-tdd, perl-testing, quarkus-tdd, rust-testing, springboot-tdd, django-tdd, windows-desktop-e2e, healthcare-eval-harness
- **→ current equivalents:** tdd, ado-test-driven-development, SP test-driven-development, browser-testing-with-devtools, webapp-testing, ce-test-browser, kw-eng-testing-strategy, ce-work, code-review-and-quality
- **→ remaining gaps:** nothing material for this environment. tdd-workflow is A direct (verified red→green→refactor equivalence, §4); python-testing and react-testing are partial only at the recipe level (pytest fixtures / Testing Library) — both languages have the *practice* fully covered; 13 of the 19 target stacks with no workload here (incompatible).

### Debugging

- **ECC skills (4):** agent-introspection-debugging, network-bgp-diagnostics, network-config-validation, network-interface-health
- **→ current equivalents:** ce-debug, diagnosing-bugs, systematic-debugging, debugging-and-error-recovery, kw-eng-debug, ce-optimize, performance-optimizer, AG Incident Responder
- **→ remaining gaps:** agent-introspection-debugging's unique part is the *mandated artifact* — capture → contained recovery → written introspection report instead of retry-and-hope; current debugging skills demand diagnosis but do not require a persisted report. The three network skills are E (no network-gear workload).

### Code Review

- **ECC skills (5):** ai-first-engineering, coding-standards, codehealth-mcp, flutter-dart-code-review, plankton-code-quality
- **→ current equivalents:** code-review (two parallel sub-agents: Standards + Spec), ce-code-review, code-review-and-quality, kw-eng-code-review, receiving-code-review, requesting-code-review, ce-resolve-pr-feedback, constraint-driven-development, AG Code Reviewer
- **→ remaining gaps:** write-time auto-format/lint on every edit (plankton-code-quality, missing — enforcement, not capability: prettier/eslint exist as commands but nothing applies them on edit); continuous structural-metric gates (codehealth-mcp, partial — needs CodeScene MCP, not configured).

### Security

- **ECC skills (13):** security-review, security-bounty-hunter, security-scan, safety-guard, defi-amm-security, django-security, healthcare-phi-compliance, hipaa-compliance, laravel-security, llm-trading-agent-security, perl-security, quarkus-security, springboot-security
- **→ current equivalents:** security-and-hardening, kw-eng-code-review (security axis), AG Security Architect / Senior SecOps Engineer / AppSec Engineer / Penetration Tester / Cloud Security Architect / Blockchain Security Auditor
- **→ remaining gaps:** safety-guard (destructive-command interception — hard-guard, missing), security-scan (agent-config/AgentShield audit — missing), bounty-qualification triage (partial). 8 of 13 are language/domain-specific with no workload (incompatible).

### Git / GitHub

- **ECC skills (5):** git-workflow, github-ops, opensource-pipeline, project-flow-ops, repo-scan
- **→ current equivalents:** git-workflow-and-versioning, resolving-merge-conflicts, ce-worktree, SP using-git-worktrees, ce-commit-push-pr, ce-babysit-pr, triage, lfg, ce-sweep, kw-eng-standup
- **→ remaining gaps:** release-management/CI-failure playbooks (github-ops, functional), sanitized fork-for-public-release chain (opensource-pipeline, partial), Linear issue↔PR linking (project-flow-ops, partial). repo-scan is an installer shim (incompatible).

### Research

- **ECC skills (15):** deep-research, research-ops, exa-search, search-first, data-scraper-agent, market-research, benchmark-methodology, competitive-platform-analysis, competitive-report-structure, prediction-market-oracle-research, scientific-thinking-literature-review, scientific-thinking-scholar-evaluation, scientific-db-pubmed-database, scientific-db-uspto-database, scientific-pkg-gget
- **→ current equivalents:** deep-research (13-agent pipeline), CL hyperresearch (16-step, scholar APIs, adversarial critics, cite-check), research, last30days, content-research-writer, hyperresearch MCP tools, BUILTIN websearch/webfetch, context7 (docs)
- **→ remaining gaps:** none material — hyperresearch exceeds ECC's deep-research on scholarly sourcing and citation checking. ECC-only pieces are wrappers (research-ops' confidence marking, exa-search's specific MCP — Exa is not configured, partial).

### Documentation

- **ECC skills (4):** architecture-decision-records, code-tour, documentation-lookup, living-docs-governance
- **→ current equivalents:** documentation-and-adrs, domain-modeling, kw-eng-documentation, documentation-lookup's context7 MCP is configured directly in `opencode.json`, knowledge-ops' role is served by the hyperresearch vault
- **→ remaining gaps:** ADR capture is deprecated inside ECC itself; code-tour (repo tour generator, partial) and living-docs-governance (stale-doc rotation, functional but ungoverned) are the only open items.

### Context Engineering

- **ECC skills (12):** context-budget, config-gc, codebase-onboarding, inherit-legacy-style, iterative-retrieval, prompt-optimizer, rules-distill, skill-scout, skill-stocktake, strategic-compact, token-budget-advisor, workspace-surface-audit
- **→ current equivalents:** context-engineering, ce-setup, codebase-design, domain-modeling, writing-for-agents, using-agent-skills, skill-creator, writing-skills, enhancing prompt skills (enhance-prompt, prompt-related kw/ce skills), ce-compound, CE handoff
- **→ remaining gaps:** token-budget-advisor (response-depth negotiation, missing — low value), context-budget/config-gc/skill-stocktake/workspace-surface-audit (partial: audits exist as one-off reports, not repeatable tools). Codebase onboarding and style inheritance are functional.

### Memory

- **ECC skills (6):** ck, unified-memory, continuous-learning, continuous-learning-v2, growth-log, knowledge-ops
- **→ current equivalents:** kw-prod-memory-management, ce-handoff / handoff, hyperresearch vault (notes/index/search/lint/graph rank), SP first-message injection (superpowers transform), ce-compound, todowrite
- **→ remaining gaps:** deterministic save/resume/list CLI with per-session brief regeneration (ck, functional not direct), cross-harness vault shared with Codex/Cursor (unified-memory, functional/single-harness only), multi-store sync (knowledge-ops, functional). continuous-learning is redundant inside ECC (superseded by v2).

### Orchestration

- **ECC skills (23):** orch-pipeline, orch-add-feature, orch-build-mvp, orch-change-feature, orch-fix-defect, orch-refine-code, parallel-execution-optimizer, claude-devfleet, dmux-workflows, dev-team, team-builder, team-agent-orchestration, agentic-os, autonomous-agent-harness, autonomous-loops, continuous-agent-loop, dynamic-workflow-mode, enterprise-agent-ops, gan-style-harness, loop-design-check, ralphinho-rfc-pipeline, agent-harness-construction, agentic-engineering
- **→ current equivalents:** ce-plan, ce-work, wayfinder, to-tickets, task (subagent dispatch), dispatching-parallel-agents, subagent-driven-development, ce-worktree, using-git-worktrees, lfg, 239 role agents, AG Agents Orchestrator / Multi-Agent Systems Architect
- **→ remaining gaps:** loop-design-check (spinning/Goodhart loop review checklist, missing, marginal), cost-aware model routing per task (agentic-engineering, functional), merge gates on team kanban (team-agent-orchestration, partial). autonomous-loops is redundant inside ECC (superseded by continuous-agent-loop).

### Verification

- **ECC skills (23):** verification-loop, delivery-gate, gateguard, hookify-rules, eval-harness, agent-eval, agent-self-evaluation, agent-architecture-audit, santa-method, skill-comply, benchmark, benchmark-optimization-loop, browser-qa, canary-watch, production-audit, terminal-ops, operator-approval-loop, prediction-market-risk-review, django-verification, laravel-verification, quarkus-verification, springboot-verification
- **→ current equivalents:** verification-before-completion, kw-eng-deploy-checklist, shipping-and-launch, kw-data-validate-data, ce-retune, ce-bakeoff, webapp-testing, ce-dogfood, ce-test-browser, performance-optimization, ce-optimize, doubt-driven-development, ce-proof, bash
- **→ remaining gaps:** gateguard (fact-forcing first-edit gate, missing), hookify-rules (declarative event rule engine, missing), skill-comply (instruction-adherence measurement, missing), eval-harness (pass@k grading harness, partial), delivery-gate/santa-method (capability present, blocking absent), operator-approval-loop (publish approval protocol, partial — autoclip publish is unguarded).

### Other

- **ECC skills (158):** the in-stack language/framework set (17), out-of-stack languages (41), domain/industry expertise (28), marketing/content (9), design/frontend/motion (10), media/video (11), engineering patterns/data/ML (11), unconfigured tooling (15), ECC-internal harness skills (16) — full rows in §5.13.
- **→ current equivalents:** where a workload exists (Python, Node, React/Next, MCP servers, docs/PDF, marketing via kw-*, design via design-system/kw-des-*/ui-ux-pro-max): see §5.13.1 / §5.13.5 / §5.13.6.
- **→ remaining gaps:** none relevant — every row in §5.13.3–§5.13.4 and §5.13.7–§5.13.10 is incompatible *because the workload, tool, or harness does not exist here*, not because a capability is missing. The only in-stack partials are python-patterns, docker-patterns, nextjs-turbopack, error-handling/api-design recipes (all functional/substantial, §5.13.1).

---

## 7. Identify the actual gaps

### Genuine ECC capabilities currently missing

All three inclusion criteria applied: ECC actually provides it; current stack has no substantially equivalent mechanism; the capability is relevant here. **8 of 293 skills qualify** (type = missing). No adoption is recommended automatically — each row states whether it is worth implementing.

| ECC skill | What it does | Why the current stack does not replace it | Worth adopting? |
| --- | --- | --- | --- |
| safety-guard | PreToolUse interception of destructive commands (`rm -rf`, `git push --force`, `DROP TABLE`) plus directory freeze | No permission configuration exists at all; nothing blocks a destructive command before it runs. Enforcement audit confirmed `permission.ask` in the ECC adapter is contract-violating, so ECC itself would not give this on OpenCode either | **Yes — as a native OpenCode permission rule**, not as an ECC skill. This is one of the three hard-guard patterns the enforcement audit already flagged for cherry-picking |
| gateguard | Deny the first Edit/Write/Bash until concrete facts are presented (fact-forcing gate) | No PreToolUse/permission layer exists; SP verification-before-completion is instructions only | Marginal — **only if** unverified claims are an observed problem; otherwise verification-before-completion plus code review covers the intent |
| hookify-rules | Declarative markdown rules matching bash/file/prompt/stop events → warn or block | The only automatic mechanism is superpowers' first-message injection; there is no event-matching rule engine | **Yes — this is the single highest-leverage gap**, because it is the substrate that would make delivery-gate, safety-guard, plankton-code-quality and plan-canvas work. Native OpenCode permission/hooks config, not ECC |
| plankton-code-quality | Write-time auto-format/lint/fix applied to every edit | Formatters/linters exist as commands; nothing runs them on write | Yes, cheap — a native write-time hook (or a "run lint after edit" instruction) closes it |
| security-scan | Scan agent configuration (.claude, settings, MCP, hooks) for injection risks with AgentShield | No config auditor exists in the current stack | **Yes** — enforcement audit already recommended AgentShield as an offline CLI auditor (no runtime integration needed) |
| skill-comply | Measure whether skills/rules are actually followed (compliance rates) | Nothing measures instruction adherence; this is precisely the "prompt ≠ enforcement" blind spot both audits identified | Worth building *after* an enforcement layer exists — measuring adherence to instructions that are not enforced yields noise |
| loop-design-check | Design/review agent loops for spinning, Goodharting, wrong-answer modes | No agent-loop review checklist; ce-plan/wayfinder cover plans, not loop failure modes | Marginal — unique but low frequency; fold into an existing orchestration skill if ever needed |
| token-budget-advisor | Offer response depth (25/50/75/100%) before answering | No depth-negotiation mechanism | **No** — low marginal value; the user can ask for depth directly |

### Near-gaps (capability present, workflow or enforcement incomplete) — 50 partial

Not "missing", but explicitly incomplete. The material ones: **delivery-gate** and **santa-method** (capability exists, blocking does not — findings are reported, never gating), **eval-harness** / **agent-eval** / **agent-self-evaluation** / **agent-architecture-audit** (no scoring, grading, or pass@k tracking), **operator-approval-loop** (autoclip publish has no approval protocol), **codehealth-mcp** (no structural-metric gate), **canary-watch** (no post-deploy watch), **plan-canvas** (no approval canvas), **context-budget** / **config-gc** / **skill-stocktake** (one-off reports, not tools), **opensource-pipeline** (no secret-scrub chain), **prompt-optimizer** (capability present, no rewrite loop).

---

## 8. Identify false gaps

```text
ECC: deep-research
→ initially appears missing (a "deep research" skill sounds like a flagship)
→ actually covered by: CL/hyperresearch (16-step pipeline), OP/deep-research (13-agent), OP/research, OP/last30days, hyperresearch MCP tools
→ reason: hyperresearch already runs scholarly APIs (OpenAlex/CORE/DOAB/RePEc), adversarial critics, and cite-check — strictly beyond ECC's version. A direct, not a gap.

ECC: documentation-lookup
→ initially appears missing (docs-at-decision-time)
→ actually covered by: context7 MCP configured in `C:\Opencode\opencode.json` (same server ECC configures) + OP/source-driven-development
→ reason: identical tool, identical contract ("current docs, not training data"). A direct (§4).

ECC: react-performance
→ initially appears missing (a React perf skill)
→ actually covered by: OP/react-best-practices
→ reason: same provenance — frontmatter author "Vercel Engineering", MIT, the same vercel-labs/agent-skills corpus. A direct (§4).

ECC: tdd-workflow
→ initially appears ambiguous (name collision with OP/tdd)
→ actually covered by: OP/tdd, SP/test-driven-development, OP/ado-test-driven-development
→ reason: verified by reading all four — the same red→green→refactor loop, not a name match. A direct (§4).

ECC: security-review
→ initially appears missing (checklist form)
→ actually covered by: OP/security-and-hardening + AG Security Architect / Senior SecOps / AppSec Engineer
→ reason: ECC's own version is a prompt-level checklist too; neither enforces. A direct with no enforcement delta.

ECC: github-ops / project-flow-ops
→ initially appears missing (PR/issue automation)
→ actually covered by: OP/ce-commit-push-pr, OP/ce-babysit-pr, OP/triage, OP/lfg, OP/ce-sweep, OP/ce-... (gh CLI runs on demand)
→ reason: capability exists; only the release/Linear playbooks are uncodified. Functional.

ECC: knowledge-ops / unified-memory / ck
→ initially appears missing (persistent memory)
→ actually covered by: CL/hyperresearch vault (notes, index, search, lint, graph), OP/kw-prod-memory-management, OP/ce-handoff, SP first-message injection
→ reason: memory exists and is richer (vault + PageRank); only determinism (CLI) and cross-harness sharing are absent. Functional.

ECC: council / council-multi-model
→ initially appears missing (multi-model critique)
→ actually covered by: OP/ce-pov (oracle panel that consults other models and reconciles opinions)
→ reason: same decision pattern. A direct.

ECC: verification-loop / terminal-ops / production-audit
→ initially appears missing (a verification harness)
→ actually covered by: SP/verification-before-completion, OP/kw-eng-deploy-checklist, OP/shipping-and-launch, OP/kw-data-validate-data, bash
→ reason: the six-phase check exists as instructions; only the PASS/FAIL artifact format is missing. Functional — and the enforcement half is missing in *both* systems.

ECC: 41 out-of-stack language skills + 28 domain skills + 16 ECC-internal skills
→ initially appear missing (85 rows with no replacement)
→ actually covered by: nothing — because there is no corresponding workload, tool, or harness in this environment
→ reason: incompatible, not missing. Counting them as gaps would be the audit's main failure mode.
```

---

## 9. Identify overlap inside current OpenCode

Where one ECC capability has multiple current replacements:

```text
ECC: tdd-workflow
        ↓
        current: OP/tdd
        current: SP/test-driven-development
        current: OP/ado-test-driven-development
        current: OP/kw-eng-testing-strategy
        current: AG Test Automation Engineer
        (5 entry points; consolidation candidate)

ECC: coding-standards / ai-first-engineering
        ↓
        current: OP/code-review (Standards axis)
        current: OP/ce-code-review
        current: OP/code-review-and-quality
        current: OP/kw-eng-code-review
        current: SP/requesting-code-review + SP/receiving-code-review
        current: OP/ce-resolve-pr-feedback
        current: AG Code Reviewer
        (7 entry points; the strongest consolidation candidate)

ECC: agent-introspection-debugging
        ↓
        current: OP/ce-debug
        current: OP/diagnosing-bugs
        current: SP/systematic-debugging
        current: OP/debugging-and-error-recovery
        current: OP/kw-eng-debug
        current: OP/ce-optimize
        (6 entry points for one diagnosis loop)

ECC: deep-research / research-ops
        ↓
        current: CL/hyperresearch
        current: OP/deep-research
        current: OP/research
        current: OP/last30days
        current: OP/content-research-writer
        (5 entry points; hyperresearch alone subsumes the rest)

ECC: blueprint / plan-orchestrate / product-capability
        ↓
        current: OP/ce-plan
        current: SP/writing-plans
        current: OP/plan-writing
        current: OP/spec-driven-development
        current: OP/kw-pm-write-spec
        current: OP/to-spec
        current: OP/wayfinder + OP/to-tickets
        (8 entry points; planning is the most over-provisioned group)

ECC: verification-loop / delivery-gate
        ↓
        current: SP/verification-before-completion
        current: OP/kw-eng-deploy-checklist
        current: OP/shipping-and-launch
        current: OP/kw-data-validate-data
        current: OP/ce-test-browser
        (5 entry points; none of them blocks)

ECC: security-review
        ↓
        current: OP/security-and-hardening
        current: OP/kw-eng-code-review (security axis)
        current: AG Security Architect / Senior SecOps / AppSec Engineer / Penetration Tester
        (5 entry points, 4 of them agents)
```

### Over-coverage summary

For each major capability: ECC equivalent → number of current replacements → competing entry points → whether consolidation would make sense.

| Capability | ECC skills | Current replacements | Competing entry points | Consolidation? |
| --- | --- | --- | --- | --- |
| Planning | 6 | 16 | ce-plan / writing-plans / spec-driven-development / wayfinder / to-tickets / kw-pm-write-spec | **Yes** — pick ce-plan (repo) + writing-plans (SP) as the pair; the rest overlap heavily |
| TDD / Testing | 19 | 9 | tdd / ado-test-driven-development / SP test-driven-development | Yes — SP and OP/tdd are interchangeable; keep one as default |
| Debugging | 4 | 7 | ce-debug / diagnosing-bugs / SP systematic-debugging / kw-eng-debug | Yes — SP systematic-debugging is the process, ce-debug the loop; merge mentally, not physically |
| Code Review | 5 | 8 | code-review / ce-code-review / code-review-and-quality / kw-eng-code-review | **Yes — highest value**: 4 of these are the same act with different checklists |
| Security | 13 | 5 | security-and-hardening + 4 security agents | Low urgency — agents are complementary to the skill |
| Git / GitHub | 5 | 10 | git-workflow-and-versioning / ce-commit-push-pr / ce-babysit-pr / triage / lfg | Mild — ce-commit-push-pr already chains most of it |
| Research | 15 | 7 | hyperresearch / deep-research / research | **Yes** — hyperresearch alone covers deep-research + research-ops + knowledge-ops |
| Documentation | 4 | 4 | documentation-and-adrs / kw-eng-documentation | No — roughly 1:1 |
| Context Engineering | 12 | 10 | context-engineering / ce-setup / writing-for-agents / skill-creator | Mild — skill-creator + writing-skills overlap |
| Memory | 6 | 6 | kw-prod-memory-management / hyperresearch vault / ce-handoff | Mild — vault and memory-management serve different layers |
| Orchestration | 23 | 9 | ce-plan → ce-work → task dispatch chain | Low — the chain is sequential, not competing |
| Verification | 23 | 7 | verification-before-completion / kw-eng-deploy-checklist / shipping-and-launch | **Yes** — and none of them enforces, so consolidating instruction-only skills buys little without an enforcement layer |

**Net:** the current stack is *over-provisioned in prompt-level instructions* (planning, code review, verification, research) and *under-provisioned in enforcement* (nothing blocks, nothing gates, nothing measures) — identical to the enforcement audit's finding.

---

## 10. Final architectural conclusion

### Q1 — Does the current OpenCode environment already cover most ECC skill functionality?

**Yes.** Of 293 ECC skills: **93 (31.7%)** are already covered at full or substantial level (21 direct + 72 functional), **50 (17.1%)** partially, **140 (48.5%)** are incompatible with this environment (no workload/tool/harness), 2 are redundant inside ECC itself, and **8 (2.7%)** are genuinely missing. Counting only the skills that *could* apply (293 − 140 incompatible − 2 redundant = 151), **93/151 = 62%** are already substantially covered and only **8/151 = 5.3%** are absent. The capability overlap is largest exactly where ECC is strongest on paper — planning, code review, testing, verification, research.

### Q2 — Which ECC skills are genuinely unique?

Eight, with three tiers:

1. **Genuinely worth having:** `safety-guard`, `hookify-rules`, `security-scan` (AgentShield), `plankton-code-quality` — all four are *enforcement/write-time* mechanisms, not knowledge.
2. **Unique but marginal:** `gateguard`, `skill-comply`, `loop-design-check`.
3. **Unique but low value:** `token-budget-advisor`.

Everything else that looked unique collapses into an existing capability on reading (§8).

### Q3 — Which ECC skills are merely differently packaged versions of existing capabilities?

**93 direct + functional**, most visibly: `deep-research`, `documentation-lookup`, `react-performance`, `tdd-workflow`, `security-review`, `council`/`council-multi-model`, `marketing-campaign`, `seo`, `mcp-server-patterns`, `accessibility`, `design-system`, `benchmark-optimization-loop`, `growth-log`, plus the whole planning and verification families (different packaging of ce-plan / writing-plans and verification-before-completion respectively). §8 lists the twelve most instructive cases; §9 shows where the packaging produced *multiple* current equivalents per ECC skill.

### Q4 — If ECC skills were imported, how much would actually be new versus duplication?

Of 293 skills imported wholesale:

- **~3% (8 skills)** would add genuine new capability — and all eight are enforcement patterns, four of which must be implemented natively anyway because ECC's own OpenCode adapter cannot enforce (enforcement audit).
- **~32% (93 skills)** would duplicate what is already there at substantial level.
- **~17% (50 skills)** would add recipes/details to capabilities that already exist — partial new *content*, not new capability.
- **~48% (142 skills)** would be dead weight: 140 incompatible with this environment + 2 redundant inside ECC.
- **Cost side:** 293 skill descriptions ≈ 29k tokens/session of standing context (enforcement audit measurement), plus the `~/.claude`-oriented, hooks-oriented, slash-command-oriented instructions that do not execute under OpenCode.

**Net: a few percent new capability — all of it in the enforcement layer — against a large standing context and maintenance cost.**

### Q5 — Is there any ECC skill worth selectively adopting despite not installing ECC?

Yes — **four, and none as a skill import**; each should be re-implemented natively or taken as an offline tool:

1. **`security-scan` → AgentShield as an offline CLI auditor** (`ecc-agentshield`, scanned, no runtime hook). Already recommended by the enforcement audit; closes the config-injection blind spot.
2. **`safety-guard` → native OpenCode permission rules** for destructive commands (`rm -rf`, `git push --force`, `DROP TABLE`), i.e. one of the three hard-guard patterns flagged for cherry-picking. The *pattern*, not the ECC file.
3. **`hookify-rules` → a native event-rule layer** (warn/block on bash/file/stop events). This is the substrate that would also deliver `delivery-gate`, `plan-canvas`'s pending-plan block and `plankton-code-quality`.
4. **`plankton-code-quality` → write-time lint/format**, implementable as the first rule on top of (3).

Explicitly **not** recommended: `gateguard` and `loop-design-check` (marginal), `token-budget-advisor` (low value), `skill-comply` (meaningless before an enforcement layer exists), and all 140 incompatible skills.

### Q6 — Does this audit change the previous conclusion "Do not install ECC"?

**NO.**

- The skill catalog — the one argument that could have changed the verdict — yields **8 genuinely missing capabilities out of 293**, and every one of them is an *enforcement* pattern that ECC cannot deliver on OpenCode anyway: the enforcement audit already established that the ECC OpenCode adapter only logs/tracks/injects, `permission.ask` violates the plugin contract, six event handlers are likely dead, and `stop-format-typecheck` always exits 0.
- The four items worth taking (§5 of Q6 above) are worth taking **as native patterns or an offline CLI**, which requires no installation and no framework.
- Nothing in the catalog addresses the unchanged cost side: ~29k tokens/session of descriptions, Claude-specific instruction surface (77 of 293 skills Claude-specific, 36 hook-dependent, 37 MCP-dependent), and the maintenance of a framework whose adapter is enforcement-free.
- The catalog actually *strengthens* the earlier judgment: 48% of the catalog is irrelevant to this environment, so its apparent size is not evidence of capability depth here.

**Verdict unchanged: do not install ECC. Cherry-pick the four native patterns above.**

---

## 11. Important distinction

```text
CAPABILITY   — the knowledge/instruction to perform a task
WORKFLOW     — the ordered phases, artifacts and hand-offs around it
ENFORCEMENT  — a mechanism that makes the workflow unavoidable
```

Worked examples from this audit (each documented rather than asserted):

**1. Verification**

```text
Capability:   equivalent — SP/verification-before-completion covers ECC verification-loop's check list
Workflow:     partially equivalent — no structured PASS/FAIL artifact, no six-phase ordering
Enforcement:  missing — in BOTH systems on OpenCode; ECC blocks only under Claude hooks
              (block-no-verify), delivery-gate has no Stop-hook equivalent here
```

**2. Code review (santa-method)**

```text
Capability:   equivalent — OP/code-review runs two independent sub-agents (Standards + Spec)
Workflow:     partially equivalent — ECC requires fix → re-review → both-pass loop
Enforcement:  missing — findings are reported, nothing blocks a merge on failure
```

**3. Destructive-command safety (safety-guard)**

```text
Capability:   missing — no skill instructs the agent to refuse rm -rf / force-push
Workflow:     missing
Enforcement:  missing — no PreToolUse/permission layer exists at all
```

**4. Planning (blueprint vs ce-plan)**

```text
Capability:   equivalent — both produce a multi-step build plan
Workflow:     partially equivalent — no dependency DAG, no per-step context briefs
Enforcement:  missing — and ECC's plan-canvas Stop-block does not exist here either
```

**5. Research (deep-research vs hyperresearch)**

```text
Capability:   equivalent (current exceeds ECC: scholarly APIs, critics, cite-check)
Workflow:     equivalent (16 steps vs ECC's plan→search→read→synthesize)
Enforcement:  not applicable — research has no gating step; `run verify` is a ship-gate check,
              i.e. the closest thing either system has
```

The rule this audit followed: **skills are classified as equivalent only when all three lines are written out.** That is why 72 mappings are "functional" rather than "direct" — capability matches, workflow or enforcement does not.

---

## 12. Final summary

### ECC Skills Covered

Substantially covered today (93 of 293): the entire Research group (deep-research, research-ops, market-research, the scientific-thinking set), Security's core (security-review, the language/domain checks are irrelevant), all of Git/GitHub's basics (git-workflow direct), Documentation (documentation-lookup direct), TDD/Testing for the stacks in use (tdd-workflow direct, e2e, ai-regression, click-path-audit), the verification instructions (verification-loop, benchmark-optimization-loop direct, browser-qa, production-audit, terminal-ops), Code Review's knowledge side (ai-first-engineering, coding-standards), Planning's knowledge side (intent-driven-development, plan-orchestrate, product-capability), Memory (ck, unified-memory, growth-log, knowledge-ops), Context Engineering's knowledge side (codebase-onboarding, inherit-legacy-style, iterative-retrieval, prompt-optimizer, rules-distill, skill-scout), Orchestration's dispatch chain (the six orch-* skills via ce-plan/ce-work/task), design/marketing direct hits (accessibility, design-system, marketing-campaign, seo, council), mcp-server-patterns, and the in-stack framework set (react-performance, backend-patterns, error-handling, api-design, deployment-patterns, hexagonal-architecture).

### ECC Skills Partially Covered

50 skills — capability present, workflow or enforcement incomplete (full list in §7's near-gaps): delivery-gate, santa-method, eval-harness, agent-eval, agent-self-evaluation, agent-architecture-audit, canary-watch, operator-approval-loop, plan-canvas, codehealth-mcp, opensource-pipeline, project-flow-ops, context-budget, config-gc, skill-stocktake, workspace-surface-audit, strategic-compact, prompt-optimizer, python-testing, react-testing, python-patterns, docker-patterns, nextjs-turbopack, ui-to-vue, crosspost, x-api, unified-notifications-ops, plus the four framework verification loops (django/laravel/quarkus/springboot — also irrelevant) and the team/agent harness set (team-agent-orchestration, agentic-os, autonomous-agent-harness, continuous-agent-loop, dynamic-workflow-mode, enterprise-agent-ops, gan-style-harness, ralphinho-rfc-pipeline, agentic-engineering).

### ECC Skills Actually Missing

**8 (2.7%):** safety-guard, hookify-rules, security-scan, plankton-code-quality, gateguard, skill-comply, loop-design-check, token-budget-advisor — with adoption verdicts in §7 and Q5. Four are worth acting on; four are marginal or premature.

### Current OpenCode Overlap

Where multiple current skills/agents replace one ECC capability: Code Review (7 entry points), Planning (8–16), Research (5, one of which subsumes the rest), Debugging (6), Verification (5, none enforcing), Security (5), TDD (5), Git (10). Full mapping in §9. Consolidation is worth doing for **Code Review, Research and Planning**; it would free standing context without losing capability. Overlap is concentrated in prompt-level instruction skills, never in enforcement — the stack has **zero** competing enforcement mechanisms because it has **zero** enforcement mechanisms.

### ECC Skills Worth Cherry-Picking

Four, none as skill imports:

1. `security-scan` → AgentShield offline config auditor.
2. `safety-guard` → native OpenCode permission rules for destructive commands.
3. `hookify-rules` → native event-rule layer (warn/block on bash/file/stop).
4. `plankton-code-quality` → write-time lint/format as rule #1 on top of (3).

Deliberately excluded: gateguard, skill-comply, loop-design-check (marginal/premature), token-budget-advisor (low value), and all 140 incompatible skills.

### Final Decision

**The ECC skill catalog provides no reason to install ECC.** It confirms the previous verdict: 62% of the applicable catalog is already covered, 48% of the whole catalog is irrelevant to this environment, and the only genuinely new capabilities (8) are enforcement patterns that ECC's OpenCode adapter cannot enforce — which is exactly what the enforcement audit found independently. The catalog's real value is as a **checklist of four native patterns to implement** (§ Q5), not as a framework to adopt.

