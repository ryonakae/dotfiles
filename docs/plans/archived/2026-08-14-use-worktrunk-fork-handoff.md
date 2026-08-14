# use-worktrunk Fork Handoff Implementation Plan

> **For implementers:** Execute tasks in order unless dependencies allow otherwise. Mark a task complete only after its validation succeeds. Reflect minor implementation differences in the relevant task. Ask the user before changing requirements, Out of Scope, or public contracts.

## Problem Statement

`use-worktrunk` currently creates or selects a worktree without changing the current Agent session, reports the absolute path, and asks the user to start a new session. That preserves cwd and project-context correctness, but it does not tell users how to carry the current conversation into an independent worker session. The intended workflow is parallel development: one coordinator session remains in its current worktree while each new branch/worktree receives a separate Agent session.

## Goal

After a normal Agent-issued Worktrunk worktree creation, keep the creator session in place and report an actionable, client-specific command that forks the current conversation into the new worktree for Pi, Claude Code, Codex, or OpenCode.

## Out of Scope

- Automatically launching the forked Agent process or a Zellij/tmux pane.
- Moving the current Agent session into the new worktree.
- Resuming the same session ID concurrently in two processes.
- Replacing Worktrunk with Claude Code's native worktree management.
- Broadening the Skill trigger from explicit Worktrunk/worktree operations to every generic branch request.
- Changing Worktrunk path configuration, Safehouse grants, ignored-file copy rules, hook approval behavior, merge, remove, or prune semantics.
- Adding runtime scripts, a client registry, or persistent state.

## Requirements and Decisions

### Requirements

- **R1:** A normal Agent-session worktree creation must continue to use `--no-cd --format=json`, validate an absolute worktree path, and leave the creator session in its current worktree.
- **R2:** After successful creation, the result must explain that parallel development uses an independent forked session rather than the same session ID resumed concurrently.
- **R3:** The result must provide the correct fork command for the current client:
  - Pi: run from the target worktree and use `pi --fork <session-id>`.
  - Claude Code: run from the target worktree and use `claude --resume <session-id> --fork-session`.
  - Codex: use `codex fork -C <worktree-path> <session-id>`.
  - OpenCode: use `opencode <worktree-path> --session <session-id> --fork`.
- **R4:** Commands must use the validated absolute worktree path and shell-escape path and session-ID values.
- **R5:** The Skill must not execute the fork command automatically. It reports the command and stops unless the user explicitly requested an existing `--execute`, multiplexer, or sub-agent handoff workflow.
- **R6:** If the current client cannot be identified confidently, report all four labeled commands rather than guessing. If a reliable current session ID is unavailable, use an explicit `<session-id>` placeholder and say that it must be replaced; do not inspect session transcripts, credentials, or denied paths to discover it.
- **R7:** Claude Code guidance must use CLI `--fork-session`, not the in-session `/fork` command, because `/fork` may invoke Claude Code's own worktree isolation instead of the Worktrunk-managed path.
- **R8:** Existing Safehouse, exact-copy, approval, dirty-remove, and explicit `--execute` behavior must remain unchanged.

### Implementation Decisions

- **D1:** Treat the creator as a coordinator and the fork as a worker. This preserves the parallel-development reason for adopting worktrees.
- **D2:** Fork, rather than resume, is the cross-client contract. Pi and OpenCode bind ordinary resume to the prior session directory; Codex can override cwd on resume but fork avoids sharing one active session ID; Claude Code can move a session but should preserve the coordinator for parallel work.
- **D3:** Keep the adapter instruction-only. Client-specific commands belong in `SKILL.md`; no executable dispatch layer is introduced.
- **D4:** Extend the existing evaluation contract vertically: update the real Pi creation case first, then add one analysis-only command case for each remaining client, one known-client/missing-ID case, and one unknown-client case.
- **D5:** Compare the revised Skill against a snapshot of the current Skill for the changed handoff cases. Run the revised Skill against the complete persisted suite, including every pre-existing Safehouse and explicit-handoff case.

### Contracts

After successful normal creation, the user-visible report contains:

1. Worktrunk result and validated absolute path.
2. A statement that the current session remains in its current worktree.
3. A statement that the fork creates an independent session for parallel work.
4. One client-specific, shell-safe fork command, or a labeled four-command fallback when client identity is unknown.
5. A note that `<session-id>` must be replaced when no reliable ID is available.

The command shapes are:

```text
Pi:          cd <worktree-path> && pi --fork <session-id>
Claude Code: cd <worktree-path> && claude --resume <session-id> --fork-session
Codex:       codex fork -C <worktree-path> <session-id>
OpenCode:    opencode <worktree-path> --session <session-id> --fork
```

These are report contracts, not commands the Skill executes automatically.

## Current Context

### Confirmed

- `config/.agents/skills/use-worktrunk/SKILL.md` is 91 lines and instruction-only.
- Section 4 already applies `--no-cd --format=json`, validates the absolute path, stops before implementation, and exempts explicit `--execute`, multiplexer, and sub-agent handoffs.
- Eval 1 exercises real Worktrunk creation and currently checks only a generic new-session instruction.
- Evals 2–8 cover exact ignored-file copy, outside-Safehouse paths, hook guidance, approval refusal, dirty removal, explicit execute handoff, and inherited negation.
- The persisted suite currently has 8 evals and 39 expectations.
- Pi 0.83.0 opens a resumed session using the cwd stored in its session header; `pi --fork` copies history into a new session whose cwd is the launch directory.
- Claude Code 2.1.220 supports `--fork-session` with `--resume` and starts the fork in the launch directory.
- Codex CLI 0.145.0 exposes `fork -C <DIR>`.
- OpenCode 1.18.6 creates a fork in the launch project directory when `[project]`, `--session`, and `--fork` are combined.
- Existing unrelated changes under `writing-plans`, `config/.claude/settings.json`, and `config/.pi/agent/settings.json` must remain untouched.

### Assumptions

- Eval fixture session IDs are inert test values used only to verify reported command construction; the eval harness does not execute nested Agent CLIs.

## File Structure

- Modify: `config/.agents/skills/use-worktrunk/SKILL.md` — add the cross-client fork handoff decision and reporting contract.
- Modify: `config/.agents/skills/use-worktrunk/evals/evals.json` — update Pi creation expectations and add Claude Code, Codex, and OpenCode handoff cases.
- Modify: `config/.agents/skills/use-worktrunk/evals/fixtures.md` — define deterministic session ID, client, path, and non-execution fixtures for the new cases.
- Create: `docs/plans/2026-08-14-use-worktrunk-fork-handoff.md` — record this implementation plan.
- Temporary only: `config/.agents/skills/use-worktrunk-workspace/` — old/new evaluation outputs; remove after review and verification.

## Testing Decisions

- **Test seam:** Evaluate observable Agent output after a real Worktrunk creation for Pi and after a supplied successful-creation result for the other clients and fallback cases.
- **Behavior:** The creator stays put, the output includes the validated path, exactly the correct client-specific fork command, and no nested Agent process is started. Fallback cases cover a missing reliable session ID and an unknown client; at least one uses an absolute path containing spaces to require shell-safe quoting.
- **Prior art:** Reuse Eval 1's isolated Worktrunk fixture and Eval 7's distinction between ordinary switch and explicit handoff.
- **Avoid:** Do not execute nested interactive Agent CLIs in evals, inspect real session stores, assert internal client-detection implementation, or weaken existing Worktrunk/Safehouse checks.

## Progress

- [x] Task 1: Add the Pi fork-handoff contract and make the Skill satisfy it.
- [x] Task 2: Add Claude Code, Codex, and OpenCode fork-handoff contracts one client at a time.
- [x] Task 3: Compare the revised Skill with the old Skill and complete regression validation.

Implementation-time minor file differences must be reflected in the relevant task. Ask the user before changing requirements, Out of Scope, or the command/report contracts above.

## Tasks

### Task 1: Implement the Pi tracer-bullet handoff

**Covers:** R1, R2, R3 (Pi), R4, R5, R6, D1, D3, D4

**Objective:** A real ordinary Worktrunk creation from a Pi evaluation session reports an independent Pi fork command rooted at the validated worktree path without launching it.

**Files:**
- Modify: `config/.agents/skills/use-worktrunk/evals/evals.json`
- Modify: `config/.agents/skills/use-worktrunk/evals/fixtures.md`
- Modify: `config/.agents/skills/use-worktrunk/SKILL.md`

**Dependencies:** Existing Eval 1 fixture and Section 4 ordinary-switch behavior.

**Implementation notes:**
- RED: extend Eval 1 with a deterministic `{{SESSION_ID}}`, identify the fixture client as Pi, require the exact Pi command, and require that no nested Agent CLI ran.
- Confirm the old Skill fails only the new fork-specific assertions while preserving its existing creation behavior.
- GREEN: add a concise handoff subsection after the ordinary-switch rules. Keep `--no-cd --format=json` and all explicit handoff exceptions unchanged.
- Add persisted Eval 12 for a known Pi client without a reliable session ID. Require `<session-id>` replacement guidance and prove from the transcript that no session store, transcript, credential, or denied path was inspected.

**Test cases:**
- Successful Pi worktree creation → report absolute path and `cd <path> && pi --fork <session-id>`; do not edit the worktree or launch Pi.
- Missing reliable session ID → report the Pi command with `<session-id>` and explain replacement; do not inspect session storage.

**Complete when:**
- Eval 1 passes every creation and fork assertion against the revised Skill; if the old Skill infers the Pi command without an explicit contract, record that assertion as non-discriminating rather than weakening the prompt.
- A deterministic instruction-contract check proves the old Skill lacks client-specific fork guidance and the revised Skill contains it.
- Eval 12 passes placeholder and no-probing assertions against the revised Skill and exposes the old Skill's missing guidance.
- Existing Eval 1 creation, JSON, no-edit, and stop behavior still passes.

**Validation:**
- Run paired old/new Evals 1 and 12 in fresh owned fixtures.
- Expected: both versions preserve safe creation behavior where applicable; only the revised Skill emits the exact Pi fork guidance, handles a missing ID without probing, and avoids automatic execution.

### Task 2: Add the remaining client handoff contracts

**Covers:** R2, R3 (Claude Code, Codex, OpenCode), R4–R8, D2–D4

**Objective:** The Skill gives the correct independent-fork command for each supported Agent and avoids client-native behavior that would bypass the Worktrunk-managed worktree.

**Files:**
- Modify: `config/.agents/skills/use-worktrunk/evals/evals.json`
- Modify: `config/.agents/skills/use-worktrunk/evals/fixtures.md`
- Modify: `config/.agents/skills/use-worktrunk/SKILL.md`

**Dependencies:** Task 1 handoff subsection and report structure.

**Implementation notes:**
- Add one analysis-only eval at a time for Claude Code (Eval 9), Codex (Eval 10), and OpenCode (Eval 11). Each receives a validated absolute worktree path and deterministic source session ID and must not execute a command.
- Claude Code must use `--resume ... --fork-session`; reject `/fork`, `--worktree`, and same-session `/cd`/`EnterWorktree` guidance for this parallel-worker case.
- Codex must use `fork -C`; reject `resume -C` for the parallel-worker default.
- OpenCode must combine target project path, `--session`, and `--fork`; reject plain `--session` and session move as the default.
- Add mandatory Eval 13 for an unknown client. It uses a validated absolute worktree path and inert session ID containing spaces, requires all four labeled commands with exact shell-safe quoting, and requires the Agent not to guess a client or execute any command.

**Test cases:**
- Claude Code creation result → exact CLI fork-session command at target path; no Claude-native worktree creation.
- Codex creation result → exact `codex fork -C` command; no resume of the active coordinator ID.
- OpenCode creation result → exact project-path `--session ... --fork` command; no plain resume or move.
- Unknown client with quoting-sensitive path and session ID → all four labeled and correctly quoted commands; no guessed client and no automatic execution.
- Explicit `--execute` handoff → existing Eval 7 remains unchanged and does not receive a redundant manual fork instruction.

**Complete when:**
- Each known-client case passes its command-specific assertions against the revised Skill; baseline cases that infer the correct command are recorded as non-discriminating.
- The comparison still demonstrates concrete baseline gaps in canonical command forms or fallback behavior without making prompts artificially prescriptive.
- Eval 13 passes unknown-client, all-command, and exact-quoting assertions against the revised Skill and exposes the old Skill's missing fallback.
- Eval 7 still preserves explicit handoff.
- `SKILL.md` remains below 200 lines and instruction-only.

**Validation:**
- Run Evals 9–11 and 13 as paired revised/old-Skill evals.
- Expected: revised Skill passes every client command, fallback, quoting, and non-execution assertion; old Skill lacks the new concrete guidance.

### Task 3: Validate the complete adapter contract

**Covers:** R1–R8, D5

**Objective:** Demonstrate that fork guidance improves ordinary creation without regressing the existing Worktrunk and Safehouse safety contract.

**Files:**
- Verify: `config/.agents/skills/use-worktrunk/SKILL.md`
- Verify: `config/.agents/skills/use-worktrunk/evals/evals.json`
- Verify: `config/.agents/skills/use-worktrunk/evals/fixtures.md`
- Update: `docs/plans/2026-08-14-use-worktrunk-fork-handoff.md` — mark progress and reconcile actual validation.
- Temporary: `config/.agents/skills/use-worktrunk-workspace/`

**Dependencies:** Tasks 1 and 2.

**Implementation notes:**
- Use a snapshot of the pre-change Skill as the baseline.
- Run changed Evals 1 and 9–13 as paired revised/old-Skill evaluations. Run the revised Skill against the complete suite of Evals 1–13, so Evals 2–8 revalidate exact copy, Safehouse path handling, hook guidance, approval refusal, dirty removal, explicit `--execute`, and inherited-negation behavior.
- Grade command text, shell quoting, absolute path, no auto-execution, coordinator preservation, and no-probing assertions from transcripts and outputs, not result claims alone.
- Request an independent review focused on command correctness, same-session/fork confusion, explicit-handoff regression, and scope creep.
- Remove only owned temporary eval workspaces and fixtures after normal Worktrunk cleanup and ownership checks.

**Test cases:**
- Complete eval JSON has unique contiguous IDs and all placeholders documented in fixtures.
- All changed handoff cases pass with the revised Skill.
- Revised-Skill runs for Evals 2–8 pass every existing safety and explicit-handoff expectation; their prompts and expectations remain unchanged except for unavoidable metadata count updates.
- No scripts, registries, runtime state, denied-path probes, `--yes`, or force behavior are introduced.

**Complete when:**
- Paired changed-case benchmark and grading are complete.
- Revised-Skill results for every Eval 1–13 pass, including Evals 2, 3, 5, and 8 Safehouse-sensitive behavior and Eval 7 explicit handoff.
- Independent review has no blocking issue.
- Machine validation, `git diff --check`, and target-file scope checks pass.
- Owned temporary eval artifacts are removed.

**Actual result:**
- Revised Skill: handoff Evals 1 and 9–13 `26/26`; all Evals 1–13 `60/60`.
- Baseline comparison on the neutral handoff prompts: `12/26`.
- Independent review: no findings, `Ready to merge: Yes`.

**Validation:**
- Run: `jq -e` checks for the final eval IDs, unique IDs, documented placeholders, and non-empty expectations.
- Run: `test "$(wc -l < config/.agents/skills/use-worktrunk/SKILL.md | tr -d ' ')" -lt 200`.
- Run: `test -z "$(find config/.agents/skills/use-worktrunk -type f -path '*/scripts/*' -print)"`.
- Run: `git diff --check` and a target-path diff review.
- Expected: all checks exit 0; unrelated pre-existing changes remain untouched.

## Requirement Coverage

| Requirement / Decision | Task | Verification |
|---|---|---|
| R1 | Task 1, Task 3 | Real Eval 1 creation preserves JSON/no-cd/absolute-path behavior |
| R2 | Task 1, Task 2 | Output states coordinator/worker fork semantics |
| R3 | Task 1, Task 2 | Four client-specific command assertions |
| R4 | Task 1, Task 2 | Exact validated path and shell-safe command grading |
| R5 | Task 1–Task 3 | Transcript shows no nested Agent CLI execution |
| R6 | Task 1, Task 2 | Mandatory Eval 12 missing-ID and Eval 13 unknown-client assertions |
| R7 | Task 2 | Claude case rejects `/fork` and `--worktree` |
| R8 | Task 2, Task 3 | Eval 7 and existing safety-contract checks remain unchanged |
| D1 | Task 1 | Creator stays in current worktree and reports worker fork |
| D2 | Task 2 | Resume/move alternatives rejected as parallel default |
| D3 | Task 1–Task 3 | No runtime scripts/state and line-count check |
| D4 | Task 1, Task 2 | One-client-at-a-time Red→Green history |
| D5 | Task 3 | Old/new paired benchmark plus complete-suite machine validation |

## Final Validation

- [x] Changed Evals 1 and 9–13 pass with revised Skill; baseline gaps and non-discriminating cases are documented.
- [x] Revised-Skill runs pass every Eval 1–13, including Safehouse-sensitive Evals 2, 3, 5, and 8 and explicit-handoff Eval 7 (`60/60`).
- [x] Complete eval JSON and fixture placeholder checks pass.
- [x] `SKILL.md` remains instruction-only and below 200 lines.
- [x] `git diff --check` passes.
- [x] Independent review reports no blocker.
- [x] Temporary workspace and both owned fixture roots are removed after review.
- [x] Requirement Coverage has no unverified item.
- [x] Plan and actual changes are consistent after independent review.

## Risks and Open Questions

- Fork CLI syntax is version-sensitive. This change targets the installed versions recorded under Current Context and should keep commands localized for future updates.
- Full-history forks may carry irrelevant coordinator context. A fresh session with a concise handoff remains a user-selected alternative, but changing the default away from fork is outside this change.
- Automatic pane/session launch would require terminal-multiplexer orchestration and explicit process ownership rules; it remains out of scope.
- No unresolved requirement blocks implementation.
