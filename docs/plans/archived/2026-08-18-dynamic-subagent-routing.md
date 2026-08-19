# Dynamic Subagent Routing Implementation Plan

> **For implementers:** Execute tasks in order unless dependencies allow otherwise. Mark a task complete only after its validation succeeds. Reflect minor implementation differences in the relevant task. Ask the user before changing requirements, Out of Scope, or public contracts.

## Problem Statement

The Pi subagent definitions currently use `general`, `explore`, and `review` names and inherit the parent model and thinking level. Pinning a model in each agent definition would conflate role with task complexity: the same explorer or reviewer may need Luna, Terra, or Sol depending on scope and failure impact. Pi-subagents supports per-invocation `model` and `thinking` parameters, but its compact tool description does not teach the parent agent a persistent routing policy.

## Goal

Expose three consistently named roles—`worker`, `explorer`, and `reviewer`—while keeping their model and thinking settings unpinned. Teach the parent agent to choose Luna, Terra, or Sol and the lowest sufficient thinking level for every subagent invocation, with the existing parent Sol High configuration as a quality-safe fallback. Keep the parent-facing routing instructions and all maintained subagent prompts in Japanese so the local policy is easy to revise later.

## Out of Scope

- Implementing a deterministic classifier or modifying the `@tintinweb/pi-subagents` package.
- Changing the parent model or parent thinking level.
- Changing the available model list in `config/.pi/agent/settings.json`.
- Combining exploration and review into one role.
- Changing agent tool permissions, review isolation, nested-agent behavior, scheduling, concurrency, or join mode.
- Optimizing for monetary cost; routing prioritizes latency while limiting quality loss.

## Requirements and Decisions

### Requirements

- **R1:** The advertised custom agent types are `worker`, `explorer`, and `reviewer`; the old `general`, `explore`, and `review` files no longer define custom types.
- **R2:** Preserve the current role boundaries: worker handles general execution, explorer performs read-oriented codebase analysis, and reviewer performs isolated read-oriented change review.
- **R3:** Write the parent-facing agent descriptions, the worker/explorer/reviewer prompt bodies, their headings, and their maintained output guidance in Japanese. Keep model IDs, setting keys, tool names, paths, and other machine-readable identifiers unchanged.
- **R4:** Do not set `model` or `thinking` in any agent frontmatter, so invocation parameters remain authoritative and omission continues to inherit the parent defaults.
- **R5:** Give the parent a Japanese persistent routing policy that requires explicit `model` and `thinking` arguments for normal subagent launches and chooses among the exact enabled Sol, Terra, and Luna model IDs.
- **R6:** Route clear, narrow, repeatable, or easily verified work to Luna; normal exploration and implementation to Terra Medium; complex tracing, debugging, and review to Terra High; and ambiguous, cross-cutting, high-impact, security-sensitive, or failed lower-tier work to Sol High.
- **R7:** Use the lowest sufficient thinking level. Low is reserved for deterministic work, Medium is the default, High is used for multi-step checking and edge cases, and XHigh/Max are not automatic defaults.
- **R8:** If the parent intentionally omits routing parameters, the existing parent Sol High settings remain the fallback.
- **R9:** Enable pi-subagents model scope so caller-selected models outside Pi's exact enabled-model list fail instead of running unexpectedly.
- **R10:** Preserve all unrelated working-tree changes, including the existing modification to `config/.pi/agent/settings.json`.

### Implementation Decisions

- **D1:** Agent types represent stable behavior, tool access, and output contracts; model and thinking represent per-task compute allocation.
- **D2:** Use `worker`, `explorer`, and `reviewer` so all role names describe actors and end in `-er`.
- **D3:** Use a custom Agent tool description rather than global AGENTS instructions, keeping the routing policy local to pi-subagents orchestration.
- **D4:** Keep routing prompt-driven. The extension does not gain a Codex-style deterministic router; the parent LLM selects explicit tool arguments from the persisted policy.
- **D5:** Treat Terra Medium as the uncertain/default route and escalate after uncertainty or failed verification rather than defaulting every subagent to Sol.
- **D6:** Prefer natural Japanese technical prose over literal translation. Preserve behavioral constraints and output contracts while translating, and leave only machine-readable identifiers and conventional code terms in English.

### Contracts

For a new non-resume `Agent` invocation, the parent should normally provide both:

```text
model: openai-codex/gpt-5.6-{luna|terra|sol}
thinking: low|medium|high
```

The agent frontmatter must not override either value. Resume behavior remains managed by pi-subagents and is not re-routed as a new task.

## Current Context

### Confirmed

- `resolveAgentInvocationConfig()` uses `agentConfig?.model ?? params.model` and `agentConfig?.thinking ?? params.thinking`; frontmatter therefore overrides invocation parameters.
- The current `general.md`, `explore.md`, and `review.md` definitions do not pin either field.
- `subagents.json` currently uses `toolDescriptionMode: "compact"`, disables default agents, and disables scheduling.
- Pi's current enabled-model list contains exact entries for `openai-codex/gpt-5.6-luna`, `openai-codex/gpt-5.6-terra`, and `openai-codex/gpt-5.6-sol`.
- Pi's parent defaults are Sol High.
- The working tree contains unrelated user changes that must remain untouched.
- Agent definitions are deployed as individual symlinks under `~/.pi/agent/agents/`; renaming source files leaves the old links broken until the repository's link-maintenance scripts run.

### Assumptions

- Translating and restructuring the role prompts for maintainability does not change their established permission boundaries or core responsibilities.

## File Structure

- Rename: `config/.pi/agent/agents/general.md` → `config/.pi/agent/agents/worker.md` — general execution role.
- Rename: `config/.pi/agent/agents/explore.md` → `config/.pi/agent/agents/explorer.md` — codebase exploration role.
- Rename: `config/.pi/agent/agents/review.md` → `config/.pi/agent/agents/reviewer.md` — isolated review role.
- Create: `config/.pi/agent/agent-tool-description.md` — parent-visible dynamic routing policy and live agent list.
- Modify: `config/.pi/agent/subagents.json` — enable custom description mode and model scope.
- Verify only: `config/.pi/agent/settings.json` — confirm the exact allowed models without editing its existing user change.
- Create then archive after validation: `docs/plans/2026-08-18-dynamic-subagent-routing.md`.

## Testing Decisions

- **Test seam:** Static configuration and frontmatter consumed by pi-subagents, plus the custom Agent tool description consumed at the next Pi session.
- **Behavior:** Verify exact role filenames/display names, absence of pinned routing fields, presence of routing tiers and exact model IDs, valid JSON settings, enabled model scope, and preservation of the existing enabled-model list.
- **Prior art:** pi-subagents documents `toolDescriptionMode: "custom"`, dynamic placeholders, per-call `model`/`thinking`, and opt-in `scopeModels` in its installed README.
- **Avoid:** Do not start an interactive Pi session, rewrite package code, or normalize unrelated JSON/settings content.

## Progress

- [x] Task 1: Rename the three stable role definitions.
- [x] Task 2: Add parent-driven model and thinking routing with scope enforcement.
- [x] Task 3: Validate the effective configuration and archive this plan.

Implementation-time minor file differences must be reflected in the relevant task. Ask the user before changing requirements, Out of Scope, or the routing contract above.

## Tasks

### Task 1: Rename stable agent roles

**Covers:** R1–R4, R10, D1, D2, D6

**Objective:** Pi discovers exactly the intended `worker`, `explorer`, and `reviewer` custom role files while their existing behavior and permission boundaries remain intact.

**Files:**
- Rename: `config/.pi/agent/agents/general.md` → `config/.pi/agent/agents/worker.md`
- Rename: `config/.pi/agent/agents/explore.md` → `config/.pi/agent/agents/explorer.md`
- Rename: `config/.pi/agent/agents/review.md` → `config/.pi/agent/agents/reviewer.md`

**Dependencies:** None.

**Implementation notes:**
- Update `display_name` to match the new actor names and write every parent-visible role description in Japanese.
- Add a concise Japanese worker prompt covering bounded implementation, verification, and reporting without over-specializing the role.
- Translate explorer's replacement prompt and maintained output guidance into natural Japanese while preserving its built-in read/search/bash tool list and analysis contract.
- Translate reviewer's replacement prompt, severity definitions, and output contract into natural Japanese while preserving its built-in read/search/bash tool list and `isolated: true` setting.
- Keep model IDs, frontmatter keys, tool names, paths, and literal configuration values in their machine-readable form.
- Do not pin a model or thinking level in any role.

**Test cases:**
- List the agent directory → only `worker.md`, `explorer.md`, and `reviewer.md` are present among these role definitions.
- Inspect frontmatter → display names match filenames, descriptions are Japanese, and no `model` or `thinking` key exists.
- Inspect prompt bodies → all three roles have maintainable Japanese instructions while machine-readable identifiers remain intact.
- Inspect role constraints → explorer and reviewer retain their previous tool boundaries; reviewer remains isolated.

**Complete when:**
- All three new files exist and all three old files do not.
- Role-specific prompt content and constraints are preserved.
- Focused structural validation succeeds.

**Validation:**
- Run: `test -f config/.pi/agent/agents/worker.md && test -f config/.pi/agent/agents/explorer.md && test -f config/.pi/agent/agents/reviewer.md && test ! -e config/.pi/agent/agents/general.md && test ! -e config/.pi/agent/agents/explore.md && test ! -e config/.pi/agent/agents/review.md`
- Expected: exit 0.
- Run: `rg -n '^display_name: (Worker|Explorer|Reviewer)$' config/.pi/agent/agents/{worker,explorer,reviewer}.md`
- Expected: one matching display name in each file.
- Run: `! rg -n '^(model|thinking):' config/.pi/agent/agents/{worker,explorer,reviewer}.md`
- Expected: exit 0 with no matches.

### Task 2: Add dynamic routing policy

**Covers:** R3–R9, D3–D6

**Objective:** The parent sees a concise, persistent policy and normally supplies the lowest-sufficient model and thinking level on each new subagent launch.

**Files:**
- Create: `config/.pi/agent/agent-tool-description.md`
- Modify: `config/.pi/agent/subagents.json`

**Dependencies:** Task 1 names are final so the live agent-list placeholder advertises the correct roles.

**Implementation notes:**
- Write the complete custom Agent tool description and routing policy in natural Japanese.
- Use the supported `{{compactTypeList}}` placeholder so Japanese role descriptions remain synchronized with agent files.
- Explain that routing depends on task shape and failure impact, not agent type alone.
- Include exact model IDs and concrete Luna/Terra/Sol criteria.
- Require explicit model/thinking arguments for new launches, while documenting intentional omission as Sol High inheritance.
- Direct the parent to escalate when a lower tier reports uncertainty or verification fails.
- Preserve `disableDefaultAgents: true` and `schedulingEnabled: false`; change only `toolDescriptionMode` and add `scopeModels`.

**Test cases:**
- Parse `subagents.json` → custom description and model scope are enabled; existing unrelated keys remain unchanged.
- Inspect the custom description → Japanese instructions include all three exact model IDs, Low/Medium/High guidance, fallback behavior, and escalation.
- Inspect enabled models → exactly the intended family entries remain available for scope validation.

**Complete when:**
- The custom tool description is valid Japanese Markdown with a live role-list placeholder.
- The routing policy is actionable without tying a role to one model.
- Scope enforcement is enabled and JSON validation succeeds.

**Validation:**
- Run: `jq -e '.disableDefaultAgents == true and .schedulingEnabled == false and .toolDescriptionMode == "custom" and .scopeModels == true' config/.pi/agent/subagents.json`
- Expected: prints `true` and exits 0.
- Run: `for model in luna terra sol; do rg -Fq "openai-codex/gpt-5.6-$model" config/.pi/agent/agent-tool-description.md || exit 1; done; rg -Fq '{{compactTypeList}}' config/.pi/agent/agent-tool-description.md`
- Expected: exit 0.
- Run: `jq -e '.enabledModels | sort == ["openai-codex/gpt-5.6-luna", "openai-codex/gpt-5.6-sol", "openai-codex/gpt-5.6-terra"]' config/.pi/agent/settings.json`
- Expected: prints `true` and exits 0 without modifying the file.

### Task 3: Validate and archive

**Covers:** R1–R10, D1–D6

**Objective:** Static checks and diff inspection confirm that Pi will load the intended roles and routing policy without touching unrelated changes.

**Files:**
- Verify: `config/.pi/agent/agents/worker.md`
- Verify: `config/.pi/agent/agents/explorer.md`
- Verify: `config/.pi/agent/agents/reviewer.md`
- Verify: `config/.pi/agent/agent-tool-description.md`
- Verify: `config/.pi/agent/subagents.json`
- Verify only: `config/.pi/agent/settings.json`
- Refresh: `~/.pi/agent/agents/*.md` — remove the three broken old links and create links for the renamed roles with the repository scripts.
- Move: `docs/plans/2026-08-18-dynamic-subagent-routing.md` → `docs/plans/archived/2026-08-18-dynamic-subagent-routing.md`

**Dependencies:** Tasks 1 and 2.

**Implementation notes:**
- Run all focused validations together.
- Use `scripts/remove-broken-symlinks.sh -y` to remove the broken old role links, then create only the four task-owned symlinks (`worker`, `explorer`, `reviewer`, and `agent-tool-description.md`) directly. Do not run the repository-wide creator because the working tree contains unrelated untracked config files that it could also deploy.
- Inspect only the task-related diff and confirm unrelated pre-existing changes remain present and unmodified.
- Pi registers the tool description and type schema at session start; report that a new Pi session is required for runtime loading rather than claiming an in-session reload.

**Test cases:**
- Focused diff → only intended role, routing, setting, and plan changes belong to this task.
- Complete validation command → all file, frontmatter, JSON, model-list, policy, and deployed-symlink assertions pass.
- Home agent directory → old role links are absent and each new link resolves to its corresponding `config/` source.
- New-session limitation → final report explicitly identifies runtime loading as not exercised in the current session.

**Complete when:**
- Every focused validation exits 0.
- The task diff matches the plan and no unrelated change was overwritten.
- The completed plan is archived.

**Validation:**
- Run: `jq empty config/.pi/agent/subagents.json config/.pi/agent/settings.json && test -f config/.pi/agent/agent-tool-description.md && ! rg -n '^(model|thinking):' config/.pi/agent/agents/{worker,explorer,reviewer}.md`
- Expected: exit 0 with no routing fields in agent frontmatter.
- Run: `for role in worker explorer reviewer; do test "$(readlink "$HOME/.pi/agent/agents/$role.md")" = "$PWD/config/.pi/agent/agents/$role.md" || exit 1; done`
- Expected: exit 0 and each deployed link resolves to the renamed source.
- Run: `git diff -- config/.pi/agent/agents config/.pi/agent/agent-tool-description.md config/.pi/agent/subagents.json docs/plans/2026-08-18-dynamic-subagent-routing.md`
- Expected: only the planned role renames, routing description, subagent setting changes, and plan are shown.

## Requirement Coverage

| Requirement / Decision | Task | Verification |
|---|---|---|
| R1, D2 | Task 1 | New/old filename and display-name assertions |
| R2, D1 | Task 1 | Tool, isolation, and prompt diff inspection |
| R3, D6 | Tasks 1–2 | Japanese role descriptions, prompt bodies, output guidance, and routing policy inspection |
| R4 | Tasks 1–2 | No frontmatter `model`/`thinking`; policy requires invocation values |
| R5–R8, D3–D5 | Task 2 | Custom description content assertions |
| R9 | Task 2 | `scopeModels == true` and exact enabled-model list |
| R10 | Tasks 1–3 | Focused diff and preservation of existing settings content |

## Final Validation

- [x] All Task 1 role-structure commands exit 0.
- [x] All Task 2 routing and JSON commands exit 0.
- [x] `jq empty config/.pi/agent/subagents.json config/.pi/agent/settings.json` exits 0.
- [x] Focused diff matches the planned scope and preserves unrelated changes.
- [x] Home symlinks for `worker`, `explorer`, and `reviewer` resolve to the renamed source files and no broken old role link remains.
- [x] Runtime reload: N/A in the current Pi session because Agent tool registration occurs at session start; verify the advertised roles on the next Pi session.
- [x] Requirement Coverage has no unaddressed item.
- [x] The plan and actual changes are consistent.
- [x] After all checks succeed, move this plan unchanged to `docs/plans/archived/2026-08-18-dynamic-subagent-routing.md`.

## Risks and Open Questions

- Prompt-driven routing is probabilistic; it is less deterministic than a harness-level Codex router. Explicit tool arguments, model scope, a concrete default, and escalation guidance reduce this risk.
- `scopeModels` recognizes exact enabled-model entries. The current settings satisfy that constraint, but later glob-only edits could make scope checking a no-op.
- A current Pi session retains its already registered Agent tool description and type schema until the next session.
- Open questions: none.
