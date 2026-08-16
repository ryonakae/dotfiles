# use-worktrunk Safehouse Delegation Implementation Plan

> **For implementers:** Execute tasks in order unless dependencies allow otherwise. Mark a task complete only after its validation succeeds. Reflect minor implementation differences in the relevant task. Ask the user before changing requirements, Out of Scope, or public contracts.

## Problem Statement

`use-worktrunk` currently attempts a fail-closed partial `wt step copy-ignored` inside Agent Safehouse by constructing an exact-file allowlist from two dry-runs. This cannot complete the user-visible workflow when `.env`, credentials, recursive directories, or other policy-denied paths are selected. It also leaves a partially initialized worktree and makes the adapter responsible for race handling and copy planning that belongs outside the sandbox.

The same boundary affects Worktrunk operations that exchange or remove ignored files. The adapter needs one simple contract: inspect safe metadata inside Agent Safehouse, but ask the user to execute operations that may copy, exchange, or delete policy-denied worktree content from their normal fish shell.

## Goal

Replace Agent-side partial copy behavior with a concise delegation boundary, preserve safe Worktrunk operations and existing fork guidance, and update the persisted evaluation contract so the new behavior is objectively reviewable.

## Out of Scope

- Changing Agent Safehouse grants, deny rules, or wrapper behavior.
- Explaining how copied `.env` files are consumed after Worktrunk finishes.
- Parsing arbitrary hook scripts such as custom `cp`, `rsync`, or project setup scripts to infer secret-file access.
- Treating `.worktreeinclude` alone as evidence that copying will occur.
- Adding executable helper scripts, persistent state, a policy parser, or a client registry.
- Automatically launching Agents through Worktrunk `--execute`, Zellij, tmux, or another non-interactive shell.
- Changing official Worktrunk command semantics, approval behavior, force behavior, or hook timing defaults.
- Optimizing the Skill description or running a broad trigger benchmark.

## Requirements and Decisions

### Requirements

- **R1:** Before an actual `wt` operation, continue to read the official `worktrunk` Skill and current command help. General Worktrunk questions remain official-Skill-only.
- **R2:** Inside Agent Safehouse, never run `wt step copy-ignored`, including `--dry-run`. If the user explicitly requests ignored-file copying, or the effective creation hooks directly invoke `wt step copy-ignored`, delegate the relevant workflow to the user's normal fish shell.
- **R3:** When a new worktree and ignored-file copy form one requested workflow, do not create a partial worktree first. Delegate creation, copy, and optional Agent startup together. A tracked `.worktreeinclude` without an explicit copy request or direct copy hook does not trigger delegation.
- **R4:** Delegated copy guidance omits dry-run, preserves the user's source, target, include, exclude, and other non-conflicting options, and never invents `--yes`, force flags, or `--foreground`. If a blocking delegated step fails after creation, leave the worktree in place and do not launch the Agent. Configured `post-start` work remains non-blocking and does not gate Agent startup unless the user consents to moving it to `pre-start`.
- **R5:** After successful delegated creation, start the next Agent only from the interactive fish wrapper so it re-enters Safehouse. Remove Agent-CLI `--execute` from a delegated workflow, move its trailing Agent arguments shell-safely to the separate client wrapper command, and explain the sequential handoff; preserve a user-requested `--execute` for general non-Agent commands when no Safehouse delegation is required.
- **R6:** Respect hook timing as configuration intent: `pre-start` copy is blocking; `post-start` copy is non-blocking. Only when the user explicitly requires a `post-start` copy to finish before Agent startup, propose moving it to `pre-start`; edit either project or user configuration only after explicit consent.
- **R7:** Delegate `wt step promote`, `wt remove`, live `wt step prune`, and `wt merge` when it will remove the worktree. Permit `wt merge --no-remove` inside Safehouse when the user explicitly supplied that flag. Permit `wt step prune --dry-run` inside Safehouse, summarize candidates, and obtain confirmation before reporting the normal-shell live command.
- **R8:** Preserve Worktrunk defaults for background removal and destructive flags. Do not add `--foreground`, `--force`, `--force-delete`, or `--yes` unless the user explicitly requested and approved the applicable behavior.
- **R9:** Before an Agent-side worktree creation, inspect target-tree path names through Git metadata and evaluate them against the final ordered Safehouse policy for the planned destination. Delegate creation when a tracked target path is effectively denied or the final policy result cannot be established. Do not read file content or probe denied filesystem paths.
- **R10:** If the planned path is outside the current session's write grants, delegate creation rather than proposing a Worktrunk user-config or Safehouse-policy change.
- **R11:** If delegated `promote`, removal, merge cleanup, or prune affects the current Agent worktree, stop the current session after reporting the command and require a new Agent session for further work. Unaffected sessions may continue.
- **R12:** On delegated-command failure, use a supplied exit status or ask for it when absent, and request only redacted error lines; do not request full hook output that may contain secrets.
- **R13:** Preserve existing ordinary-switch behavior: safe Agent-side switches use `--no-cd --format=json` and validate the absolute path. When the switch creates a new worktree, leave the creator as coordinator and report a client-specific independent fork command without executing it. Selection of an existing worktree reports its path and requires a new session but does not add coordinator/fork semantics intended only for creation.
- **R14:** Keep the adapter focused on Worktrunk boundaries. Do not add general warnings about whether a subsequent Agent can read copied files.

### Implementation Decisions

- **D1:** Delegation is operation-based, not existence-based. The Agent does not determine whether `.env` or another denied ignored file actually exists.
- **D2:** All Agent-side real and dry-run ignored copying is removed rather than retaining a safe-file exception.
- **D3:** Direct `copy-ignored` hooks and explicit copy requests are recognized; arbitrary shell hook semantics are not analyzed.
- **D4:** The user's act of executing the reported normal-shell command is the execution confirmation. Copy dry-run is not required. Prune is the exception because it is a bulk destructive operation with a metadata-only dry-run.
- **D5:** Ordered Safehouse rules remain canonical. The Skill does not duplicate filename lists and fails closed when final policy evaluation is uncertain.
- **D6:** Existing client-specific fork command forms remain unchanged for ordinary Agent-side creation. Delegated creation uses the same client selection/session-ID rules but requires invocation from the interactive fish shell rather than Worktrunk `--execute`.

### Contracts

| Operation | Agent Safehouse behavior |
|---|---|
| Existing-worktree selection | Execute with `--no-cd --format=json`, validate/report the path, and require a new session without creator/coordinator fork semantics |
| New creation, writable path, no effectively denied tracked path, no explicit/direct-hook copy | Execute with `--no-cd --format=json` and report independent fork guidance |
| Explicit `copy-ignored`, or creation with direct copy hook | Do not execute dry-run or real copy; report the normal-fish workflow from its first mutating step |
| Creation outside current grant or with an effectively denied tracked path | Do not create; report normal-fish creation and Agent startup |
| `promote`, `remove`, live `prune`, merge with cleanup | Do not execute; report the original normal-shell command without adding flags |
| `prune --dry-run` | Execute and summarize; ask for confirmation before reporting live prune command |
| Explicit `merge --no-remove` | May execute inside Safehouse |
| General non-Agent `--execute`, with no other delegation trigger | Preserve official handoff behavior |
| Agent CLI `--execute` in a delegated workflow | Remove from the Worktrunk command and report a subsequent interactive-fish Agent command |

A delegated creation report must order blocking commands so later steps run only after earlier success. It must not automatically execute them. A `post-start` direct copy hook remains background work and cannot gate Agent startup unless the user explicitly requires completion and consents to moving it to `pre-start`.

## Current Context

### Confirmed

- `config/.agents/skills/use-worktrunk/SKILL.md` is instruction-only and currently implements a two-dry-run exact-file copy procedure.
- `config/.agents/skills/use-worktrunk/evals/evals.json` contains 13 evals and 60 expectations; Evals 2 and 8 encode the old partial-copy design.
- `config/.agents/skills/use-worktrunk/evals/fixtures.md` contains a race helper and exact-copy fixtures that become obsolete.
- Worktrunk supports `merge --no-remove`, `hook post-start --foreground`, `step prune --dry-run`, and background worktree removal.
- Worktrunk background hook command records do not provide a reliable completion status; hook placement is therefore treated as the blocking/non-blocking contract.
- The repository's fish `pi`, `claude`, `codex`, and `opencode` functions launch those clients through Agent Safehouse. Worktrunk child shells cannot be assumed to load those functions.
- `config/.claude/settings.json` has a pre-existing unrelated modification and must remain untouched.

### Assumptions

- The current eval JSON format remains the persisted behavior specification; no new runtime harness format is introduced.

## File Structure

- Create: `docs/plans/2026-08-16-use-worktrunk-safehouse-delegation.md` — implementation and validation contract.
- Modify: `config/.agents/skills/use-worktrunk/SKILL.md` — replace partial-copy mechanics with the delegation decision matrix.
- Modify: `config/.agents/skills/use-worktrunk/evals/evals.json` — replace stale copy/path/removal expectations and add focused boundary cases.
- Modify: `config/.agents/skills/use-worktrunk/evals/fixtures.md` — remove race fixtures and document deterministic delegation/preflight fixtures.

## Testing Decisions

- **Test seam:** Persisted eval prompts and observable Agent behavior, plus deterministic structural checks on the Skill and eval files.
- **Behavior:** Cover ordinary safe creation, explicit copy delegation, copy-hook creation delegation, outside-grant creation, tracked-deny preflight, delegated promote/remove/merge cleanup, allowed `merge --no-remove`, prune dry-run/live split, Agent-CLI `--execute` separation, post-start timing, and existing fork reports.
- **Prior art:** Retain ordinary creation and client-fork Evals 1 and 9–13; revise Evals 2, 3, 6, and 8; retain Eval 7 for general non-Agent `--execute`; add Evals 14–19 for copy-hook timing, destructive-operation boundaries, prune, delegated Agent-CLI handoff, redacted failure reporting, and existing-worktree selection.
- **Avoid:** Do not create or probe `.env`, credentials, secret directories, or private-key fixtures. Do not execute delegated destructive commands during evals. Do not make the eval contract depend on exact Markdown headings or implementation wording.
- **Evaluation depth:** The user already completed a detailed design review through `dig`; use targeted changed-case Agent evaluations and independent review rather than a new human eval-viewer round. Record objective expectation results and block completion on any failed revised-Skill expectation.

## Progress

- [x] Task 1: Replace stale eval contracts with the agreed delegation behavior.
- [x] Task 2: Simplify `SKILL.md` while preserving safe operations and fork guidance.
- [x] Task 3: Validate the revised behavior and archive this plan.

Implementation-time minor file differences must be reflected in the relevant task. Ask the user before changing requirements, Out of Scope, or the operation/report contracts above.

## Tasks

### Task 1: Replace the partial-copy evaluation contract

**Covers:** R2–R12, D1–D5

**Objective:** The persisted eval suite fails the old partial-copy behavior and specifies the new normal-shell boundary without requiring denied-path fixtures.

**Files:**
- Modify: `config/.agents/skills/use-worktrunk/evals/evals.json`
- Modify: `config/.agents/skills/use-worktrunk/evals/fixtures.md`

**Dependencies:** Existing eval IDs and fixture isolation conventions.

**Implementation notes:**
- First revise the changed eval expectations while the old Skill is still present. Confirm the old Skill text contains behavior forbidden by the new contract (`copy-ignored --dry-run`, exact-file approval, or path-config workaround).
- Eval 2 becomes create-plus-explicit-copy delegation. It asserts no Agent-executed `copy-ignored`, no dry-run/probe/partial copy, one reported normal-fish real-copy command, preserved `--from`/`--to`/`--require-include` options, sequential creation/copy/fork ordering, no invented flags, and blocking-failure/no-launch guidance.
- Eval 3 changes outside-grant handling from config advice to normal-shell creation plus interactive-fish Agent startup.
- Eval 6 changes dirty remove from Agent execution to non-executing normal-shell delegation, original flags, no invented `--foreground`/force, and current-session stop when the current worktree is targeted.
- Eval 7 remains the general non-Agent explicit `--execute` regression.
- Eval 8 becomes tracked-deny preflight based on Git tree names and ordered policy rules; it also covers uncertain final-policy evaluation by delegation.
- Eval 14 compares direct `pre-start` and `post-start` copy hooks: both creation commands are delegated, pre-start gates startup, post-start does not, and moving post-start requires consent.
- Eval 15 covers `promote`, default merge cleanup, and explicit `merge --no-remove`, including current-worktree session handling.
- Eval 16 covers Agent-executed `prune --dry-run`, candidate summary/confirmation, and user-executed live prune without invented flags.
- Eval 17 covers removal of Agent CLI `--execute` from a delegated create/copy workflow, exact transfer of its trailing prompt payload, and subsequent interactive-fish wrapper startup.
- Eval 18 covers a simulated blocking delegated-command failure: leave the worktree, do not launch the Agent, and request only exit status plus redacted error lines.
- Eval 19 materializes a primary worktree already on `existing-eval`, executes safe selection with `--no-cd --format=json`, archives raw JSON, verifies the absolute primary path, and omits new-creation coordinator/fork semantics and tracked-tree creation preflight.
- Changed operation evals explicitly require the official Skill and current relevant `wt <command> --help` to be read before deciding or reporting a command.
- Keep IDs 1–19 unique and document every placeholder in fixtures.

**Test cases:**
- Eval 2 create plus explicit copy → no Agent-executed Worktrunk copy command; report one normal-shell real-copy command with original options; no partial destination changes; later blocking commands are success-gated.
- Eval 3 outside current grant → no config or policy proposal; normal-shell switch and client wrapper guidance.
- Eval 6 dirty remove and Eval 15 current-worktree operations → no mutation in the evaluated Agent; report session stop only when the current worktree is affected.
- Eval 8 target Git tree contains an effectively denied tracked path → no checkout/probe; normal-shell delegation.
- Eval 14 pre-start versus post-start copy → blocking and non-blocking launch semantics remain distinct.
- Eval 15 promote/default merge versus explicit `merge --no-remove` → delegated destructive operations and permitted no-remove merge are distinguished.
- Eval 16 prune dry/live → metadata-only dry-run may execute; live prune waits for confirmation and runs only in normal shell.
- Eval 7 general command `--execute` → preserved; Eval 17 Agent-CLI `--execute` in a delegated workflow → separated into interactive fish startup.
- Eval 18 blocking failure → no Agent startup and no request for unredacted/full output.
- Eval 19 existing selection → actual isolated selection, archived valid JSON matching the primary path, and new-session guidance without creation-only preflight or coordinator/fork claims.

**Complete when:**
- The eval and fixture files are valid and internally consistent.
- No fixture requires creating or reading a denied path.
- Every operation in the Contracts table has at least one expectation.
- R1, R3, R4, R8, R11, and R12 each have an explicit expectation rather than relying on prose review.
- A deterministic pre-change check demonstrates that the old Skill violates the revised copy/path contract.

**Validation:**
- Run: `jq -e '.skill_name == "use-worktrunk" and ([.evals[].id] == [range(1; 20)]) and ([.evals[].id] | length == (unique | length)) and all(.evals[]; (.prompt | length) > 0 and (.expected_output | length) > 0 and (.expectations | length) > 0)' config/.agents/skills/use-worktrunk/evals/evals.json`
- Expected: exit 0.
- Run: `set -o pipefail; jq -r '.evals[].prompt' config/.agents/skills/use-worktrunk/evals/evals.json | rg -o '\{\{[A-Z0-9_]+\}\}' | sort -u | while IFS= read -r placeholder; do rg -Fq "$placeholder" config/.agents/skills/use-worktrunk/evals/fixtures.md || { echo "undocumented: $placeholder" >&2; exit 1; }; done`
- Expected: exit 0 with no undocumented placeholder.
- Run before editing `SKILL.md`: `rg -n 'copy-ignored.*--dry-run|approved files|既存grant内を使うWorktrunk user config' config/.agents/skills/use-worktrunk/SKILL.md`
- Expected: exit 0 and output proving the old contract conflicts with revised Evals 2 and 3.

### Task 2: Replace partial copy mechanics with the delegation matrix

**Covers:** R1–R14, D1–D6

**Objective:** `SKILL.md` clearly distinguishes Agent-executable metadata/safe operations from normal-shell operations and no longer contains exact-copy race machinery.

**Files:**
- Modify: `config/.agents/skills/use-worktrunk/SKILL.md`

**Dependencies:** Task 1 revised behavioral contract.

**Implementation notes:**
- Preserve the official-Skill dependency, current relevant `wt <command> --help` inspection, Worktrunk defaults, approvals, current-session `--no-cd --format=json`, absolute-path validation, and creation-only client-specific independent-fork guidance.
- Distinguish existing-worktree selection from new creation: both report a validated path and require a new session, but tracked-tree preflight and coordinator/fork language apply only to creation.
- Replace the ignored-copy section with a short trigger-and-delegate flow. Read effective Worktrunk config/hooks and canonical Safehouse policy only to classify the operation; do not inspect ignored-file existence.
- Add a compact operation matrix for copy, tracked-deny/outside-path creation, promote, remove, merge, and prune.
- Keep final ordered policy evaluation for tracked Git tree names, including later allow rules; delegate on uncertainty.
- State that direct `post-start` copy remains non-blocking. Require consent before moving either project or user hooks to `pre-start` when completion was explicitly requested.
- For delegated creation, report sequential normal-fish commands and invoke the client wrapper only after successful blocking steps. Do not use Agent CLI `--execute` or automatic multiplexer handoff; preserve any trailing Agent payload by moving it shell-safely to the client wrapper's supported initial-prompt form.
- Keep failure reporting limited to exit status and redacted error lines, and stop before any automatic retry.
- Do not add general `.env`-consumption guidance.

**Test cases:**
- Reading the Skill yields one unambiguous action for every Contracts-table row, including separate selection and creation behavior.
- Search confirms official Skill/current-help inspection remains explicit and no two-dry-run, exact-negation, approved-file, race, or partial-copy algorithm remains.
- Existing ordinary Pi/Claude/Codex/OpenCode fork command shapes remain present and non-executing.

**Complete when:**
- The Skill is instruction-only, below 200 lines, and contains no stale partial-copy procedure.
- All revised eval expectations are represented by a concise instruction.
- General Worktrunk behavior remains delegated to the official Skill rather than duplicated.

**Validation:**
- Run: `test "$(wc -l < config/.agents/skills/use-worktrunk/SKILL.md | tr -d ' ')" -lt 200`
- Expected: exit 0.
- Run: `test -z "$(find config/.agents/skills/use-worktrunk -type f -path '*/scripts/*' -print)"`
- Expected: exit 0.
- Run: `! rg -n 'approved file|exact negation|2回目|initial plan|final invocation|race' config/.agents/skills/use-worktrunk/SKILL.md`
- Expected: exit 0.

### Task 3: Validate changed behavior and archive the plan

**Covers:** R1–R14, D1–D6

**Objective:** Objective checks and independent review show that the simpler delegation contract is complete, non-contradictory, and does not regress ordinary handoff guidance.

**Files:**
- Verify: `config/.agents/skills/use-worktrunk/SKILL.md`
- Verify: `config/.agents/skills/use-worktrunk/evals/evals.json`
- Verify: `config/.agents/skills/use-worktrunk/evals/fixtures.md`
- Move after all validation passes: `docs/plans/2026-08-16-use-worktrunk-safehouse-delegation.md` → `docs/plans/archived/2026-08-16-use-worktrunk-safehouse-delegation.md`

**Dependencies:** Tasks 1 and 2.

**Implementation notes:**
- Create an owned temporary evaluation root with `EVAL_WORKSPACE=$(mktemp -d /tmp/use-worktrunk-eval.XXXXXX)` and `printf 'owned-by=use-worktrunk-eval\n' > "$EVAL_WORKSPACE/.owned"`. Store only eval prompts, outputs, and grading there; never place a sibling workspace under `config/.agents/skills/`.
- Write `$EVAL_WORKSPACE/substitutions.json` as an object keyed by eval ID, using each eval section's fixture values rather than one global branch/path map. Before launching evaluators, render each source prompt by exact string substitution into `$EVAL_WORKSPACE/results/eval-<ID>/prompt.md`, save the same ID-specific object as `substitutions.json` beside it, and fail if any `{{...}}` token remains. These persisted files are the exact prompts evaluated; no evaluator reconstructs substitutions from prose.
- Launch fresh, non-inheriting general Agent evaluators with one Agent per changed eval ID. Each reads the revised Skill, official Worktrunk Skill, persisted resolved `prompt.md`, its ID-specific `substitutions.json`, `evals.json`, and `fixtures.md`; executes no user-delegated command; and writes both `result.md` and a complete chronological `transcript.md` of every read/help/write action under `$EVAL_WORKSPACE/results/eval-<ID>/`. Eval 19 is the only changed case that executes a Worktrunk operation: the isolated, non-mutating existing-primary selection, whose raw JSON is archived. Run regression inspection separately for IDs 1, 4, 5, 7, and 9–13.
- Launch one independent review/grader Agent after all result files exist. It compares changed IDs 2, 3, 6, 8, and 14–19 with every persisted expectation and writes `$EVAL_WORKSPACE/grading.json` as `{ "evals": [{ "id": 2, "expectations": [{ "text": "...", "passed": true, "evidence": "..." }] }] }`. Each `text` must be copied exactly from that eval's persisted expectation list, in order and without duplication. Evidence must quote the result or identify the exact Skill instruction; claims without evidence fail.
- Report the changed-case passed/total expectation count. Regression inspection must explicitly confirm ordinary creation/current-help loading, hook timing, approval refusal, general non-Agent explicit handoff, and all four client fork command forms.
- Request a separate independent code review focused on contradictions between full-workflow delegation, post-start non-blocking semantics, destructive-operation boundaries, existing selection versus creation, and session handoff.
- Review the actual diff and preserve the unrelated `config/.claude/settings.json` modification.
- After grading and review are recorded in the session, verify `$EVAL_WORKSPACE/.owned`, remove only that temporary root, and confirm it is absent.

**Test cases:**
- Every revised changed-case expectation passes with evidence.
- Ordinary safe creation still requires current help, emits `--no-cd --format=json`, and reports an independent fork command; existing selection remains distinct.
- General hook guidance remains free of unrelated Safehouse discussion.
- No evaluator or implementation command performs copy/promote/remove/live-prune/default-merge operations inside Safehouse; Eval 19 alone performs safe existing-primary selection and archives JSON.

**Complete when:**
- JSON, placeholder, line-count, no-script, and stale-language checks pass.
- Changed IDs 2, 3, 6, 8, and 14–19 pass every persisted expectation in `grading.json`.
- Regression inspection and independent code review report no blocking finding.
- `git diff --check` passes and only intended files plus the pre-existing user change are modified.
- The owned temporary eval root is removed.
- The plan is reconciled with actual implementation, all Final Validation items pass, and the plan is moved to `docs/plans/archived/` without renaming.

**Actual result:**
- Revised Skill: 116 lines, instruction-only, with no stale partial-copy/race algorithm.
- Changed Evals 2, 3, 6, 8, and 14–19: `51/51` persisted expectations passed with exact-text grading and complete per-eval transcripts.
- Eval 19 executed isolated existing-primary selection and archived valid JSON with `action=existing`, branch `existing-eval`, and the matching absolute path; the fixture remained clean with one primary worktree and unchanged evaluator cwd.
- Regression inspection for Evals 1, 4, 5, 7, and 9–13 passed the preserved ordinary-creation, hook, approval, general `--execute`, and client-fork contracts.
- Independent final review: no findings; `Ready to merge: Yes`.

**Validation:**
- Run the exact schema, placeholder, line-count, no-script, and stale-language commands from Tasks 1 and 2.
- Expected: every command exits 0.
- Run before evaluation: `test -f "$EVAL_WORKSPACE/substitutions.json" && jq -e '."2".FEATURE_BRANCH == "copy-delegation-eval" and ."3".FEATURE_BRANCH == "outside-eval" and ."6".DIRTY_BRANCH == "dirty-eval" and ."8".FEATURE_BRANCH == "tracked-deny-eval" and ."14".FEATURE_BRANCH == "hook-copy-eval" and ."15".SIBLING_BRANCH == "sibling-eval" and (."16".PRUNE_CANDIDATES | contains("current-eval")) and ."17".FEATURE_BRANCH == "agent-execute-eval" and ."18".COPY_EXIT_STATUS == "1" and ."19".EXISTING_BRANCH == "existing-eval"' "$EVAL_WORKSPACE/substitutions.json" >/dev/null && for id in 2 3 6 8 14 15 16 17 18 19; do test -s "$EVAL_WORKSPACE/results/eval-$id/prompt.md"; test -f "$EVAL_WORKSPACE/results/eval-$id/substitutions.json"; jq -e --arg id "$id" --slurpfile all "$EVAL_WORKSPACE/substitutions.json" '. == $all[0][$id]' "$EVAL_WORKSPACE/results/eval-$id/substitutions.json" >/dev/null; ! rg -n '\{\{[^}]+\}\}' "$EVAL_WORKSPACE/results/eval-$id/prompt.md"; done`
- Expected: exit 0; every evaluated prompt uses its exact per-eval fixture substitutions with no unresolved placeholder.
- Run after evaluation: `for id in 2 3 6 8 14 15 16 17 18 19; do test -s "$EVAL_WORKSPACE/results/eval-$id/result.md"; test -s "$EVAL_WORKSPACE/results/eval-$id/transcript.md"; rg -q '## Actions' "$EVAL_WORKSPACE/results/eval-$id/transcript.md"; rg -q '## Final response' "$EVAL_WORKSPACE/results/eval-$id/transcript.md"; done`
- Expected: exit 0; each eval has a complete action transcript and final response.
- Run: `jq -n -e --slurpfile spec config/.agents/skills/use-worktrunk/evals/evals.json --slurpfile grade "$EVAL_WORKSPACE/grading.json" '($grade[0].evals | map(.id)) == [2,3,6,8,14,15,16,17,18,19] and all($grade[0].evals[]; . as $g | ($spec[0].evals[] | select(.id == $g.id) | .expectations) as $expected | ($g.expectations | map(.text)) == $expected and ($g.expectations | length) == ($expected | length) and all($g.expectations[]; .passed == true and (.evidence | length) > 0))'`
- Expected: exit 0; grading contains each persisted expectation exactly once, in order, with passing evidence.
- Run: `EXPECTED=$(jq '[.evals[] | select(.id == 2 or .id == 3 or .id == 6 or .id == 8 or (.id >= 14 and .id <= 19)) | .expectations[]] | length' config/.agents/skills/use-worktrunk/evals/evals.json); ACTUAL=$(jq '[.evals[].expectations[] | select(.passed == true)] | length' "$EVAL_WORKSPACE/grading.json"); test "$ACTUAL" -eq "$EXPECTED"`
- Expected: exit 0; report `$ACTUAL/$EXPECTED`.
- Run: `git diff --check && git status --short`
- Expected: no whitespace errors; only the three Skill files, this plan/archive move, and pre-existing `config/.claude/settings.json` appear.
- Run after recording results: `EVAL_REAL=$(realpath "$EVAL_WORKSPACE"); case "$EVAL_REAL" in /private/tmp/use-worktrunk-eval.*|/tmp/use-worktrunk-eval.*) ;; *) echo "unexpected eval root: $EVAL_REAL" >&2; exit 1;; esac; test "$(cat "$EVAL_REAL/.owned")" = owned-by=use-worktrunk-eval && rm -r -- "$EVAL_REAL" && test ! -e "$EVAL_REAL"`
- Expected: exit 0 and only the canonical owned temporary root with the expected prefix is removed.

## Requirement Coverage

| Requirement / Decision | Task | Verification |
|---|---|---|
| R1 | Task 2, Task 3 | Official-Skill loading and general hook-guidance regression |
| R2–R4 | Task 1, Task 2, Task 3 | Explicit-copy and create-plus-copy delegation evals; stale-copy search |
| R5 | Task 1–Task 3 | Delegated Agent-CLI `--execute` and interactive-fish handoff eval |
| R6 | Task 1, Task 2 | Pre/post-start copy timing eval and consent requirement |
| R7–R8 | Task 1–Task 3 | Promote/remove/merge/prune matrix evals and flag assertions |
| R9 | Task 1–Task 3 | Tracked-deny Git metadata preflight eval |
| R10 | Task 1–Task 3 | Outside-grant delegation eval |
| R11 | Task 1–Task 3 | Current-worktree impact report assertions |
| R12 | Task 1, Task 2 | Redacted failure-report expectation |
| R13 | Task 1–Task 3 | Ordinary creation/client-fork regressions plus Eval 19 existing-selection behavior |
| R14 | Task 2, Task 3 | Scope review and absence of general `.env` guidance |
| D1–D5 | Task 1–Task 3 | Eval design, no-probe contract, and canonical-policy checks |
| D6 | Task 2, Task 3 | Existing and delegated fork-handoff cases |

## Final Validation

- [x] `jq -e` eval schema and unique-ID validation succeeds.
- [x] Eval placeholders are documented by `fixtures.md` or the harness contract.
- [x] `SKILL.md` is instruction-only, below 200 lines, and contains no stale partial-copy algorithm.
- [x] All targeted revised-Skill expectations pass (`51/51`).
- [x] Ordinary creation, hook guidance, approval, explicit general handoff, and four client-fork regressions pass inspection.
- [x] Eval 19 safe existing-primary selection passes with archived raw JSON and clean fixture verification.
- [x] Independent review has no blocking finding (`Ready to merge: Yes`).
- [x] `git diff --check` succeeds.
- [x] Requirement Coverage has no unverified item.
- [x] Plan and actual changes agree, including eval-specific substitutions, transcripts, and runtime selection evidence.
- [x] Only after every item above succeeds, move this file unchanged to `docs/plans/archived/2026-08-16-use-worktrunk-safehouse-delegation.md`.

## Risks and Open Questions

- Direct hook detection can miss a custom script that internally copies ignored files. Arbitrary script analysis is explicitly out of scope; ordinary Safehouse refusal handling remains the fallback.
- Worktrunk CLI options may change. The adapter continues to require current official Skill/help inspection before execution.
- Ordered Seatbelt rule evaluation is reasoning over the canonical policy, not a new parser. Ambiguity delegates the operation rather than guessing.
- No unresolved requirement blocks implementation.
