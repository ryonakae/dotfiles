# Plan and Implement Skills Implementation Plan

> **For implementers:** Execute tasks in order unless dependencies allow otherwise. Mark a task complete only after its validation succeeds. Reflect minor implementation differences in the relevant task. Ask the user before changing requirements, Out of Scope, or public contracts.

## Problem Statement

The current workflow uses `dig` and `writing-plans` successfully, but implementation requires repeatedly restating the same execution policy: follow the agreed specification, use TDD where applicable, update progress, create and push atomic commits, perform an independent review, and archive a completed plan. The planner name is also longer than desired, while `commit-push` already describes natural-language commit-only and commit-plus-push behavior but is hidden from model invocation.

## Goal

Provide a concise `dig → plan → implement` workflow, with `dig → implement` available when the user explicitly chooses direct implementation. Make `commit-push` naturally invokable with a safe push boundary, and encode implementation completion, review, progress, and archival rules in one reusable orchestration skill.

## Out of Scope

- Changing the `dig`, `tdd`, `doc-updater`, or reviewer agent implementations.
- Adding or running new skill eval suites in this change.
- Changing Hermes Agent's historical `writing-plans → plan` migration note.
- Automatically deciding to skip planning without a user instruction to start implementation.
- Introducing a compatibility alias or empty replacement for `writing-plans`.
- Modifying unrelated current worktree changes, including `AGENTS.md`, Claude/Pi settings, Herdr/Zed settings, or the removed Pi hook files.

## Requirements and Decisions

### Requirements

- **R1:** Rename the `writing-plans` skill and directory to `plan` without losing its plan-only behavior, references, or existing eval definitions.
- **R2:** Add an `implement` skill that accepts either an active implementation plan or settled requirements from the current conversation.
- **R3:** Apply Red → Green TDD to behavior that can be automatically tested; for documentation, configuration, or other non-testable work, record the reason and use the specified alternative validation.
- **R4:** Create reviewable atomic commits during implementation and push after each commit. Use one plan task per commit by default, with justified merge/split exceptions reflected in the plan.
- **R5:** Keep an active plan current by updating progress, material file differences, minor implementation differences, and validation outcomes after each validated task. In direct mode, use visible todos only when the work has enough meaningful steps; otherwise use chat progress.
- **R6:** Always perform a final independent review. Add per-task self-review for multi-task, cross-component, public-contract, migration, concurrency, authentication/authorization, security-sensitive, or otherwise high-risk changes.
- **R7:** Automatically fix blocking/high review findings that remain in scope, ask before specification or public-contract changes, and use judgment for minor findings. Revalidate and re-review fixes.
- **R8:** Archive a plan only after all final validation and review gates pass, preserving its filename under `docs/plans/archived/`, and commit/push the archive as a separate final commit.
- **R9:** Allow unrelated unstaged changes to remain, but stop before implementation when they overlap target files or when pre-existing staged changes make ownership ambiguous. Never include unrelated changes in implementation commits.
- **R10:** On an unresolved blocker, leave incomplete changes uncommitted and unpushed, keep them locally, and record the failure, cause, and restart condition in the active plan when one exists.
- **R11:** Make `commit-push` naturally invokable: commit-only language commits without pushing; explicit commit-plus-push language pushes; push-only language does not invoke the skill; ambiguous language does not authorize push.
- **R12:** Update the shared agent instructions to describe `dig → plan → implement` and the user-selected direct `dig → implement` path.
- **R13:** Preserve existing planner eval fixtures and expectations during the rename, changing only identity/path references required by the new name; do not add or execute evals in this change.

### Implementation Decisions

- **D1:** Use the concise skill names `plan` and `implement`.
- **D2:** The user selects the route. Calling `plan` creates a saved plan; saying to start implementation without calling `plan` selects direct mode. `implement` must not independently decide to skip a plan.
- **D3:** An imperative implementation request is authorization for the implementation workflow's atomic commits and pushes. Planning, review, explanation, or discussion requests do not authorize implementation.
- **D4:** Resolve a plan in this order: an explicitly specified path, the plan created or selected in the current conversation, then the sole unarchived file in `docs/plans/`. Ask one question if multiple candidates remain. If the user explicitly chose direct implementation, do not infer a plan.
- **D5:** Treat test seams recorded in a plan or settled during `dig` as confirmed. If direct mode lacks a material test seam or public-contract decision, stop and ask rather than inventing it.
- **D6:** Reuse the `tdd` and `commit-push` skills instead of copying their detailed rules. `implement` owns sequencing, gates, progress, blocker behavior, and completion semantics.
- **D7:** Remove `disable-model-invocation` from `commit-push`; its description and trigger policy become the safety boundary. An internal call from `implement` explicitly selects commit-plus-push mode.
- **D8:** Use a reviewer subagent in a separate context for final review. If the runtime cannot provide an independent review context, report the limitation and do not archive the plan as fully complete.
- **D9:** Do not retain an obsolete `writing-plans` directory or alias after updating managed skill symlinks.

### Contracts

#### Skill routing

| User intent | Skill behavior |
|---|---|
| Ask questions, stress-test a design, or clarify requirements | `dig`; no planning or implementation |
| Ask to create/save an implementation plan | `plan`; plan file only |
| Ask to start/continue/finish implementation | `implement`; plan mode if selected/resolvable, otherwise user-selected direct mode |
| Ask only for review, explanation, or implementation advice | Do not start `implement` side effects |

#### Commit/push routing

| User intent | `commit-push` behavior |
|---|---|
| `コミットして`, `commit` | Commit only; do not push |
| `コミットプッシュして`, `コミットして push して` | Commit and push |
| `/skill:commit-push` without arguments | Commit and push |
| `pushして` without a commit request | Do not invoke `commit-push` |
| Ambiguous wording | Do not push without clarification or a separate explicit authorization |
| Internal use by `implement` | Commit and push after a deliverable passes its gate |

#### Implementation completion

- A task is complete only after its focused validation succeeds and its progress record is current.
- An implementation is complete only after relevant full validation succeeds, independent review has no unresolved blocking/high finding, accepted review fixes are revalidated, the final worktree contains no implementation-owned residue, and any active plan is archived in a separate pushed commit.
- Test failure, unavailable required review, unresolved specification change, push failure, or an ownership conflict prevents completion and plan archival.

## Current Context

### Confirmed

- `config/.agents/skills/writing-plans/SKILL.md` already defines plan-only behavior, task-level progress, final validation, and archival under `docs/plans/archived/`.
- Its existing support files are `references/plan-document-reviewer-prompt.md` and `evals/evals.json`.
- The eval file identifies the skill as `writing-plans`; its prompts and expectations otherwise describe behavior that remains valid after the rename.
- `config/.agents/skills/commit-push/SKILL.md` already contains commit-only, commit-plus-push, push-only exclusion, atomic staging, documentation update, and safe worktree rules.
- `disable-model-invocation: true` currently prevents Pi from exposing `commit-push` for natural model invocation.
- `config/.agents/AGENTS.md` currently names `writing-plans` and does not describe the `implement` execution phase or the direct route.
- Global managed skills are sourced from `config/.agents/skills/` and distributed to `~/.agents/skills/` and `~/.claude/skills/` by `scripts/create-skills-symlink.sh`.
- Existing `~/.agents/skills/writing-plans` and `~/.claude/skills/writing-plans` links point to the managed directory and will become broken after the rename unless replaced.
- The `tdd` skill is externally managed through `config/skills-lock.json`.
- The worktree currently has unrelated unstaged changes. None is under the planned skill directories or `config/.agents/AGENTS.md`; they must remain untouched.
- The planning base commit is `477a6943d071b9ec53d71f68b1950b6f04869c0d`. Path-scoped diff validation uses this object so unrelated unstaged changes do not affect completion.

### Assumptions

- The current runtimes can load a named `tdd` skill and provide an independent reviewer subagent in normal use. The fallback behavior for a missing reviewer is explicitly non-completion rather than silent self-review.
- Skill symlink migration can be performed with exact-path checks so unrelated broken links are not removed.

## File Structure

- Move: `config/.agents/skills/writing-plans/` → `config/.agents/skills/plan/` — preserve planner instructions, review reference, and existing eval data under the concise name.
- Modify: `config/.agents/skills/plan/SKILL.md` — change identity/description references while retaining plan-only and archival contracts.
- Modify: `config/.agents/skills/plan/evals/evals.json` — change `skill_name` to `plan`; preserve existing cases.
- Preserve: `config/.agents/skills/plan/references/plan-document-reviewer-prompt.md` — retain the planner review contract unless path-relative wording requires a mechanical update.
- Modify: `config/.agents/skills/commit-push/SKILL.md` — enable natural invocation and tighten intent/push authorization rules, including use from `implement`.
- Create: `config/.agents/skills/implement/SKILL.md` — orchestrate implementation modes, TDD, progress, commit/push, review, blockers, and archival.
- Modify: `config/.agents/AGENTS.md` — document the concise planning/implementation workflow and route ownership.
- Replace managed links: `~/.agents/skills/writing-plans`, `~/.claude/skills/writing-plans` → corresponding `plan` links, and add corresponding `implement` links. These are deployment state, not tracked repository files.

## Testing Decisions

- **Test seam:** Agent Skills metadata, workflow contracts in the three `SKILL.md` files, preserved planner eval JSON, shared instruction references, and managed skill symlink targets.
- **Behavior:** Verify exact names, trigger boundaries, plan/direct routing, TDD exceptions, progress gates, commit/push authorization, independent review, blocker handling, and archive ordering through static contract inspection.
- **Prior art:** Follow the existing `writing-plans` structure and the explicit trigger matrix in `commit-push`; retain existing planner evals as regression artifacts without executing them.
- **Avoid:** Do not invoke an LLM eval harness, manufacture a test runner, perform real test commits/pushes as a trigger test, or modify unrelated worktree state.

## Progress

- [x] Task 1: Rename the planner and migrate its shared workflow references
- [x] Task 2: Enable safe natural-language `commit-push` invocation
- [x] Task 3: Add the end-to-end `implement` orchestration skill

Implementation-time minor file differences and validation outcomes must be reflected in the relevant task. Ask the user before changing requirements, Out of Scope, or the routing/completion contracts above.

## Tasks

### Task 1: Rename the planner and migrate its shared workflow references

**Covers:** R1, R12, R13, D1, D2, D9

**Objective:** Make `plan` the sole planner skill name while preserving current plan-only behavior, support files, eval definitions, and the documented upstream workflow.

**Files:**
- Move: `config/.agents/skills/writing-plans/` → `config/.agents/skills/plan/`
- Modify: `config/.agents/skills/plan/SKILL.md`
- Modify: `config/.agents/skills/plan/evals/evals.json`
- Preserve or mechanically update: `config/.agents/skills/plan/references/plan-document-reviewer-prompt.md`
- Modify: `config/.agents/AGENTS.md`

**Dependencies:** None.

**Implementation notes:**
- Keep the plan-only mutation boundary, destination format, task/coverage structure, progress rules, review guidance, and archive rules unchanged unless this plan explicitly requires integration wording.
- Make the description specific enough to trigger on requests to create or save an implementation plan, without triggering on casual discussion about a plan.
- Update the shared instruction from `writing-plans` to `plan`. Add the full `implement` route in Task 3 rather than describing a skill that does not yet exist.
- Preserve all existing eval cases and expectations; only identity/path wording made stale by the rename may change.
- Do not edit the Hermes migration-history reference because it describes Hermes's own versioned rename.

**Test cases:**
- Planner source exists only at `config/.agents/skills/plan/` → Pi-compatible frontmatter name is `plan` and the old managed directory is absent.
- A planning request → description selects `plan` and the body prohibits implementation, commits, pushes, and non-plan mutations.
- Existing eval data → parses as JSON, declares `skill_name: plan`, retains four cases, and is byte-equivalent after JSON normalization to the planning-base version except for the agreed `skill_name` change.
- Shared agent workflow → references `plan`, not `writing-plans`.
- Managed skill links → remove only the two links whose raw `readlink` target exactly equals this repository's old managed directory; no stale `writing-plans` link remains after new links are created.

**Implementation result:**
- Moved the complete planner tree, including all existing eval fixture files, to `config/.agents/skills/plan/`.
- Updated only the skill metadata, eval identity, and shared workflow reference; normalized eval content matches the planning-base version after excluding `skill_name`.
- All Task 1 validation commands passed.

**Complete when:**
- The renamed skill has valid `name` and `description` frontmatter and all relative references resolve.
- No obsolete `writing-plans` reference remains in the renamed skill or `config/.agents/AGENTS.md`.
- Existing planner behavior and eval content remain materially unchanged.
- Focused validation succeeds without touching unrelated changes.

**Validation:**
- Run: `test -f config/.agents/skills/plan/SKILL.md && test ! -e config/.agents/skills/writing-plans`
- Expected: Exit 0; only the concise planner directory exists.
- Run: `rg -n '^name: plan$|^description:' config/.agents/skills/plan/SKILL.md`
- Expected: Both required frontmatter fields are present, with `name: plan` exactly once.
- Run: `jq -e '.skill_name == "plan" and (.evals | length == 4)' config/.agents/skills/plan/evals/evals.json`
- Expected: `true` and exit 0.
- Run: `bash -lc 'diff -u <(git show 477a6943d071b9ec53d71f68b1950b6f04869c0d:config/.agents/skills/writing-plans/evals/evals.json | jq "del(.skill_name)") <(jq "del(.skill_name)" config/.agents/skills/plan/evals/evals.json)'`
- Expected: No diff and exit 0; no prompt, expectation, fixture, name, or case was changed beyond `skill_name`.
- Run: `! rg -n 'writing-plans' config/.agents/skills/plan config/.agents/AGENTS.md`
- Expected: No matches and exit 0.

### Task 2: Enable safe natural-language `commit-push` invocation

**Covers:** R4, R9, R11, D3, D6, D7

**Objective:** Let commit requests select `commit-push` naturally while preserving explicit push authorization and all existing staging/ownership protections.

**Files:**
- Modify: `config/.agents/skills/commit-push/SKILL.md`

**Dependencies:** Task 1 only for final workflow naming; implementation can otherwise be reviewed independently.

**Implementation notes:**
- Remove `disable-model-invocation: true` so Pi exposes the skill metadata to the model.
- Keep the description within the Agent Skills limit and make commit-only, commit-plus-push, push-only exclusion, and ambiguity behavior explicit.
- Treat `/skill:commit-push` with no arguments as commit plus push, preserving current behavior.
- Add an explicit orchestration contract: `implement` supplies commit-plus-push authorization after a deliverable passes validation.
- Retain session change-set ownership, staged-change ambiguity, no hunk guessing, documentation update, Conventional Commits, and destructive-operation protections.
- Avoid language that implies a plain push request should create a new commit.

**Test cases:**
- `コミットして` → skill is applicable, commits the intended change set, and stops before push.
- `コミットプッシュして` or `コミットして push して` → commits and pushes.
- `pushして` → description excludes the skill; no new commit is implied.
- Ambiguous commit wording without push authorization → push is not performed.
- Validated internal `implement` checkpoint → commit-plus-push mode is explicit.

**Implementation result:**
- Removed `disable-model-invocation` and aligned the description with commit-only, commit + push, push-only exclusion, and ambiguity behavior.
- Added explicit commit + push authorization for validated deliverables delegated by `implement`.
- Preserved the existing staging ownership and destructive-operation safeguards; all Task 2 validation commands passed.

**Complete when:**
- The skill is model-visible and its description/body agree on all trigger cases.
- Push remains opt-in except for direct no-argument skill invocation and the explicit `implement` orchestration contract.
- Existing safe staging and worktree ownership rules are unchanged.
- Focused static validation succeeds.

**Validation:**
- Run: `! rg -n '^disable-model-invocation:' config/.agents/skills/commit-push/SKILL.md`
- Expected: No matches and exit 0.
- Run: `for pattern in 'commit-only' 'commit + push' 'push だけ' 'implement'; do rg -Fq -- "$pattern" config/.agents/skills/commit-push/SKILL.md || exit 1; done`
- Expected: Exit 0 only when every trigger boundary and the internal orchestration mode are represented.
- Run: `rg -n '対象外 staged|hunk 単位|push --force|git diff --cached' config/.agents/skills/commit-push/SKILL.md`
- Expected: Existing ownership and destructive-operation safeguards remain present.

### Task 3: Add the end-to-end `implement` orchestration skill

**Covers:** R2–R10, R12, D2–D8

**Objective:** Turn an imperative implementation request into a safe, resumable workflow that reaches tested, reviewed, pushed completion and archives an active plan only after all gates pass.

**Files:**
- Create: `config/.agents/skills/implement/SKILL.md`
- Modify: `config/.agents/AGENTS.md`

**Dependencies:** Task 1 provides `plan`; Task 2 provides naturally visible `commit-push` with an internal commit-plus-push contract; the externally managed `tdd` skill remains installed.

**Implementation notes:**
- Put all trigger guidance in the description: use for start/continue/finish implementation requests; do not use for planning, review-only, explanation, or design discussion.
- Keep exact `Plan mode` and `Direct mode` labels and explicit `Preflight`, `Delivery loop`, `Final review`, `Plan archive`, and `Blockers` sections so the two routes and all completion gates can be inspected deterministically.
- State that invoking implementation authorizes validated atomic commits and pushes. Do not broaden that authorization to force push, history rewriting, unrelated changes, or speculative scope.
- Implement two explicit input modes:
  - Plan mode resolves the plan by D4 and uses its requirements, tasks, validation, progress, and archive contract.
  - Direct mode uses settled conversation decisions only after the user chooses implementation; it creates no plan file and uses todos only when warranted by task size.
- Preflight must read applicable agent instructions, inspect status/diffs, identify implementation-owned files, and enforce R9 before editing.
- Load and follow the `tdd` skill for automatically testable behavior. Treat a recorded seam as confirmed; stop for a missing material seam rather than inventing one. For non-testable work, retain an explicit alternative validation and reason.
- Work in vertical deliverables. After focused validation, update the plan when present, optionally perform per-task self-review according to R6, then invoke `commit-push` in commit-plus-push mode. Default to one task per commit and record justified exceptions.
- After all deliverables, run final validation and invoke a separate-context reviewer with the plan or settled requirements, actual diff/commit range, and test results. Apply R7, then rerun affected and final validation and re-review until no blocking/high finding remains or a specification decision blocks progress.
- If independent review is unavailable, validation fails, push fails, or a blocker remains, report incomplete status and do not archive.
- For a completed plan, update all final validation state, move it without renaming to `docs/plans/archived/`, and create/push a separate archive commit.
- Keep the skill as an orchestration layer; link to or name `tdd` and `commit-push` rather than duplicating their detailed test-quality or staging rules.

**Test cases:**
- One active plan and `実装開始して` → resolve the plan, execute tasks in order, update progress, commit/push validated deliverables, independently review, then archive in a separate pushed commit.
- Settled small change and `このまま実装して` without a selected plan → direct mode, no plan creation/archive, same TDD/commit/review gates.
- Multiple unarchived plans without a conversation selection → ask one disambiguating question before editing.
- Overlapping unstaged or pre-existing staged changes → stop before editing or staging; unrelated unstaged changes remain untouched.
- Testable behavior → observe a failing test before minimal implementation; non-testable config/docs change → state why and run the exact alternative validation.
- High-risk task → perform task-level self-review plus final independent review; small local task with strong tests → final independent review only.
- Blocking/high review finding within scope → fix, validate, commit/push, and re-review; required contract change → ask the user.
- Failed validation or unavailable independent review → leave the plan active and do not claim completion.
- Unresolved mid-task blocker → leave incomplete work local and uncommitted/unpushed, recording restart context when a plan exists.

**Implementation result:**
- Added `config/.agents/skills/implement/SKILL.md` with explicit Plan mode and Direct mode, ownership preflight, TDD delegation, validated delivery commits, risk-based self-review, independent final review, blocker handling, and post-review archival.
- Updated `config/.agents/AGENTS.md` with the user-selected `dig → plan → implement` and `dig → implement` routes.
- Clarified that Plan archive checks exclude the archive action itself to avoid a circular completion gate; all Task 3 static validation commands passed.
- The first independent review found two workflow gaps: an inconsistent push authorization condition and a missing final implementation-owned residue gate. Both were corrected and passed focused validation before re-review.
- Re-review found that committing substantive residue could create a new unreviewed HEAD. The residue gate now loops back through final validation and independent review, while review records and the final plan archive remain administrative exceptions.

**Complete when:**
- Metadata selects imperative implementation requests and excludes non-mutating discussion/review requests.
- Both plan and direct modes have unambiguous entry, progress, validation, commit/push, review, blocker, and completion behavior.
- The workflow composes `tdd` and `commit-push` without copying their detailed rule sets.
- Plan archival cannot occur before successful final validation and independent review.
- `config/.agents/AGENTS.md` clearly presents both user-selected routes.
- Focused static validation succeeds.

**Validation:**
- Run: `test -f config/.agents/skills/implement/SKILL.md && rg -n '^name: implement$|^description:' config/.agents/skills/implement/SKILL.md`
- Expected: The skill exists with both required frontmatter fields and exact name.
- Run: `for pattern in 'Plan mode' 'Direct mode' 'Preflight' 'Delivery loop' 'Final review' 'Plan archive' 'Blockers' 'TDD' 'commit-push'; do rg -Fq -- "$pattern" config/.agents/skills/implement/SKILL.md || exit 1; done`
- Expected: Exit 0 only when both routes, every required orchestration phase, TDD delegation, and commit delegation are represented.
- Run: `rg -n 'dig.*plan.*implement|dig.*implement' config/.agents/AGENTS.md`
- Expected: Both user-selected routes are documented.
- Run: `git diff -- config/.agents/skills/implement/SKILL.md config/.agents/AGENTS.md`
- Expected: No implementation trigger authorizes planning/review-only requests, no unrelated shared instruction is changed, and the workflow gates match R2–R10.

## Requirement Coverage

| Requirement / Decision | Task | Verification |
|---|---|---|
| R1, R13, D1, D9 | Task 1 | Directory/name checks, JSON identity/count check, stale-reference search |
| R2, D2, D4 | Task 3 | Plan/direct mode cases and metadata inspection |
| R3, D5, D6 | Task 3 | TDD and alternative-validation contract inspection |
| R4, D3, D7 | Tasks 2–3 | Commit trigger matrix and implementation checkpoint flow |
| R5 | Task 3 | Progress behavior in plan/direct cases |
| R6, D8 | Task 3 | Risk-based task review and mandatory independent final review cases |
| R7 | Task 3 | Review fix, user-confirmation, revalidation, and re-review cases |
| R8 | Tasks 1 and 3 | Planner archive contract preservation and implementation archive gate |
| R9 | Tasks 2–3 | Existing ownership safeguards and implementation preflight case |
| R10 | Task 3 | Blocker case and non-completion gate |
| R11 | Task 2 | Static trigger matrix inspection |
| R12 | Tasks 1 and 3 | Shared instruction searches for both supported routes |

## Final Validation

- [x] `git diff --check 477a6943d071b9ec53d71f68b1950b6f04869c0d..HEAD -- config/.agents/skills/plan config/.agents/skills/implement config/.agents/skills/commit-push config/.agents/AGENTS.md docs/plans/2026-08-19-plan-and-implement-skills.md docs/plans/archived/2026-08-19-plan-and-implement-skills.md` — Passed: no whitespace errors in implementation-owned committed paths; unrelated worktree changes are excluded.
- [x] `test -f config/.agents/skills/plan/SKILL.md && test -f config/.agents/skills/implement/SKILL.md && test -f config/.agents/skills/commit-push/SKILL.md && test ! -e config/.agents/skills/writing-plans` — Passed: all three final skill entrypoints exist and the old planner path does not.
- [x] `jq -e '.skill_name == "plan" and (.evals | length == 4)' config/.agents/skills/plan/evals/evals.json` — Passed: existing planner eval definitions survived the rename.
- [x] `! rg -n 'writing-plans' config/.agents/skills/plan config/.agents/skills/implement config/.agents/skills/commit-push config/.agents/AGENTS.md` — Passed: no stale shared-workflow references.
- [x] `! rg -n '^disable-model-invocation:' config/.agents/skills/commit-push/SKILL.md` — Passed: `commit-push` is model-visible.
- [x] `rg -n '^name: (plan|implement|commit-push)$' config/.agents/skills/{plan,implement,commit-push}/SKILL.md` — Passed: exactly one correct name exists for each skill.
- [x] Manually checked every row of **Skill routing** against the three descriptions and trigger sections — Passed: planning, imperative implementation, review-only/explanation, commit-only, commit-plus-push, push-only, and ambiguous intents select the documented behavior.
- [x] Manually checked every bullet of **Implementation completion** and R2–R10 against `implement/SKILL.md` — Passed after review fixes: every required gate is explicit and detailed TDD/staging rules remain delegated.
- [x] Removed only `$HOME/.agents/skills/writing-plans` and `$HOME/.claude/skills/writing-plans` after their raw `readlink` targets exactly matched this repository's old managed directory — Passed: both old paths are absent as links.
- [x] `sh scripts/create-skills-symlink.sh` — Passed: new `plan` and `implement` links were created; unrelated links were skipped.
- [x] `test "$(readlink "$HOME/.agents/skills/plan")" = "$PWD/config/.agents/skills/plan" && test "$(readlink "$HOME/.claude/skills/plan")" = "$PWD/config/.agents/skills/plan" && test "$(readlink "$HOME/.agents/skills/implement")" = "$PWD/config/.agents/skills/implement" && test "$(readlink "$HOME/.claude/skills/implement")" = "$PWD/config/.agents/skills/implement"` — Passed: every new link targets the matching managed directory.
- [x] Used Pi 0.83.0 `DefaultResourceLoader` after symlink migration — Passed with no diagnostics: `plan`, `implement`, and model-visible `commit-push` were discovered; `writing-plans` was absent.
- [x] Automated LLM eval execution — `N/A`: explicitly deferred by user because of runtime cost; existing planner eval definitions are preserved only.
- [x] Requirement Coverage has no unmatched item.
- [x] The plan and actual changed files agree, and all pre-existing unrelated worktree changes remain untouched.
- [ ] An independent reviewer reports no unresolved blocking/high issue in the implementation diff.
- [ ] After every preceding item succeeds, move this file without renaming to `docs/plans/archived/2026-08-19-plan-and-implement-skills.md`, commit the move separately, and push it.

## Risks and Open Questions

- Natural model invocation for `implement` and `commit-push` increases the importance of precise descriptions. Static contract review is required because LLM trigger evals are intentionally deferred.
- Renaming a managed skill directory breaks existing home-directory symlinks until exact old links are removed and replacement links are created. Migration must avoid broad cleanup of unrelated broken links.
- The final independent-review guarantee depends on runtime delegation support. A runtime without it must leave the work incomplete rather than silently weakening the gate.
- No unresolved product or workflow decision remains.
