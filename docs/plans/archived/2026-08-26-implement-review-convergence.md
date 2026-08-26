# Implement Review Convergence Workflow Implementation Plan

> **For implementers:** Execute tasks in order unless dependencies allow otherwise. Mark a task complete only after its validation succeeds and its local atomic commit exists. For this self-hosting change, keep every implementation commit local until the final review, validation, plan archive, and one final push, even though the pre-change `implement` skill still says to push each task immediately. Reflect minor implementation differences in the relevant task. Ask the user before changing requirements, Out of Scope, or public contracts.

## Problem Statement

The current `implement` skill couples atomic commits to immediate pushes, runs final validation before independent review, allows unbounded full re-reviews, and gives reviewers insufficient constraints for severity, compatibility, and scope. In the motivating Plan-mode implementation, task 4 onward spent about 123 minutes in long-running subagents while Rust tests and builds took only seconds. Four generations of newly discovered High findings caused repeated fixes, validation, and broad re-review. One reviewer also treated an unreleased intermediate pane-state schema from an earlier commit in the same implementation as a compatibility contract, leading to a migration that was later removed after more than 30 minutes of avoidable work.

The execution agent amplified the problem by overusing independent high-capability reviewers at task level, accepting reviewer severity without checking the agreed requirements, failing to reject the intermediate-schema compatibility claim early, and not escalating when review stopped converging. The revised skill must therefore constrain workflow and evidence where consistency matters while leaving model selection and internal implementation choices to runtime judgment.

## Goal

Revise `config/.agents/skills/implement/SKILL.md` into a convergent delivery state machine that:

- creates validated atomic commits locally per deliverable;
- performs one evidence-constrained independent review before publication;
- bounds automatic correction and scoped re-review to two cycles per invocation;
- reuses still-valid validation results and runs only invalidated or deferred checks;
- archives the Plan locally and publishes the complete commit stack with one final push;
- escalates contract decisions and valid out-of-scope review discoveries without inventing requirements; and
- is verified with persistent Skill Creator eval definitions, an old-skill baseline, quantitative grading, benchmark analysis, and human review.

## Out of Scope

- Modifying `config/.agents/skills/commit-push/SKILL.md`, `config/.agents/skills/plan/SKILL.md`, the externally managed `tdd` skill, reviewer agent definitions, or global model-routing rules.
- Changing `config/.agents/skills/implement/agents/openai.yaml` or enabling implicit model invocation.
- Requiring, recommending, creating, or switching to a feature branch or PR workflow.
- Adding wall-clock timers, polling loops, background monitoring shells, or fixed elapsed-time stop conditions.
- Fixing reviewer models, thinking levels, or provider-specific tiers in the skill.
- Defining repository-wide compatibility policy, release criteria, migration defaults, or public-contract semantics that belong in a Plan or settled Direct-mode requirements.
- Allowing amend, rebase, squash, force push, or other history rewriting for review corrections.
- Automatically fixing medium/low review suggestions or unrelated pre-existing repository defects.
- Changing Skill triggering metadata beyond wording needed to keep the existing explicit-invocation behavior accurate; description-trigger optimization is not part of this change.
- Committing Skill Creator iteration workspaces, transcripts, timing files, grading output, benchmarks, generated viewer HTML, or user feedback.
- Modifying or committing the existing unrelated changes in `config/.claude/settings.json`, `config/.config/zed/settings.json`, or `config/.pi/agent/settings.json`.

## Requirements and Decisions

### Requirements

- **R1:** Separate atomic commit creation from publication. Each validated deliverable and accepted correction gets a local atomic commit; no implementation commit is pushed before the final delivery gate.
- **R2:** Preflight must inspect upstream configuration and ahead/behind state in addition to staged, unstaged, and untracked files. An absent/ambiguous upstream, divergence, or pre-existing unpushed commit requires confirmation before editing rather than being silently included in the final push.
- **R3:** Every deliverable receives a short same-context self-review. TDD Red → Green slices remain governed by `tdd`; necessary refactoring occurs in task-level self-review before focused validation and local commit, not during final independent review.
- **R4:** A Plan task becomes complete after its focused validation, self-review, Plan update, and local atomic commit. A later finding reopens the affected task until its correction commit and validation succeed. Remote delivery remains a separate whole-implementation gate.
- **R5:** Before initial independent review, run the Plan/project's standard local, non-interactive, non-destructive automated tests, lint, typecheck, and build in addition to task-focused validation. Defer checks requiring external state, credentials, deployment, or substantial manual interaction.
- **R6:** Reuse a validation result when none of its implementation, test, configuration, dependency, or relevant environment inputs changed. Plan progress, review-gate records, and archive movement alone do not invalidate code validation. When uncertain, rerun only the affected validation rather than every command.
- **R7:** Plan mode always requires an independent final review. Direct mode may omit it only when every change is non-executable prose or comments and does not define a contract or operational procedure; code, tests, scripts, dependencies, build/CI, and behavior-affecting configuration require review.
- **R8:** Use one read-only reviewer context, separate from every implementation context, for explicitly planned intermediate checkpoints, the final full review, and scoped re-reviews. The reviewer may propose a direction but must not edit, commit, or own validation. Model and thinking selection remain outside this skill.
- **R9:** Reviewer output must separate `blocking/high`, `decision required`, `medium/low`, and `pre-existing unrelated`. Each blocking/high finding must identify the violated Requirement, Contract, Out-of-Scope boundary, agreed Decision, concrete failure path, or material safety invariant; include the affected location and severity rationale; and distinguish defects introduced, worsened, or exposed by this implementation from unrelated existing defects.
- **R10:** The implementation agent must triage reviewer evidence against the agreed specification before changing code. Unsupported future requirements, design preferences, and compatibility assumptions are not automatic blocking/high work. Requirement or Contract gaps and interpretation conflicts become `decision required` and stop for user input.
- **R11:** Compatibility behavior comes only from the selected Plan or settled Direct-mode contract. If an implementation or reviewer discovers that a public/persistent format is changing without a compatibility decision, stop and ask; do not infer migration requirements from releases, tags, branches, or intermediate commits.
- **R12:** Batch all accepted blocking/high findings from one reviewer generation into one correction cycle, using one or more atomic correction commits as needed. The whole `/implement` invocation has at most two automatic cycles across planned checkpoints, final review, and validation-driven code fixes.
- **R13:** A scoped re-review checks prior findings, correction diffs, and directly affected execution paths. It may automatically raise a new blocking/high only when the correction introduced or exposed it. A valid High that existed in the initial implementation diff but was first noticed during re-review stops before push for user disposition instead of starting another automatic loop.
- **R14:** Medium/low findings and unaffected pre-existing issues are reported but not auto-fixed and do not block delivery. A pre-existing issue blocks only when this implementation introduced, worsened, exposed, or depends on it such that a Requirement cannot be met.
- **R15:** Reviewer-format clarification may be requested once from the same context. A reviewer context/tool failure may use one replacement reviewer. If a required valid independent review still cannot be obtained, stop incomplete without push or Plan archive.
- **R16:** Any implementation-owned code, test, configuration, dependency, or generated-artifact change after review invalidates the affected review and validation. Fixes discovered by final validation receive affected validation and scoped re-review and consume one of the two correction cycles. Administrative Plan gate records and archive movement are excluded.
- **R17:** After review and validation agree on the same implementation HEAD, record a minimal Plan gate summary, archive the Plan in a separate local commit, and push the implementation, correction, and archive commit stack to the current branch with one successful push. The original `/implement` invocation authorizes this final push even on the default branch.
- **R18:** Remote-only CI or preview validation may require an earlier remote ref only when the Plan or user explicitly defines the push target and exposure strategy. Without that decision, stop before implementation rather than inventing a branch or silently skipping required validation.
- **R19:** An unrelated existing validation failure is neither auto-fixed nor marked successful. Report evidence that it is unrelated and ask whether the acceptance contract should change; do not archive until the user resolves the failed Plan item.
- **R20:** Progress reporting uses semantic events rather than elapsed time. Report entry into the first blocking/high correction pass while continuing automatically; stop for Requirement/Contract/Out-of-Scope/test-seam changes, unresolved `decision required`, exhausted review budget, reviewer unavailability, ownership conflicts, or failed acceptance conditions.
- **R21:** Use the Skill Creator workflow to add persistent eval definitions and fixtures, snapshot the pre-change skill, run paired new/old executions, capture timing and tokens, grade every assertion, aggregate a benchmark, perform an analyst pass, generate the official eval viewer, obtain user feedback, and iterate until all new-skill safety assertions pass.

### Implementation Decisions

- **D1:** Branch type does not change the normal workflow. Local commits remain unpublished until the final gate; no feature-branch recommendation or default-branch confirmation is added.
- **D2:** Review corrections are new atomic commits even while unpushed. Existing implementation commits are never amended, rebased, squashed, or reconstructed.
- **D3:** One correction cycle is `triage and batch accepted findings → implement → affected validation → scoped re-review`. Initial full review and reviewer-format clarification do not count as correction cycles; code changes made because final validation failed do count.
- **D4:** Two correction cycles are automatic. After the second scoped re-review, any unresolved blocking/high stops before a third change. A user-approved Requirement or Contract change establishes a new specification, full review, and two-cycle budget; a large change that invalidates the Plan still requires a new Plan.
- **D5:** The same reviewer context is reused across planned checkpoints and final review. A final review after a checkpoint is still a full base-to-HEAD review, while subsequent correction reviews are scoped.
- **D6:** The reviewer normally trusts validation results tied to the reviewed HEAD. It may run a focused reproduction or inspect an untested path to substantiate a finding, but it does not routinely duplicate an already successful full suite.
- **D7:** The Plan gate summary records only the reviewed implementation commit/range, accepted blocking/high findings and correction commits, and the absence of unresolved blocking/high findings. Medium/low findings remain in the completion report rather than turning the Plan into a review log.
- **D8:** For this self-hosting implementation, this Plan's deferred-push contract supersedes the old `implement` skill's task-by-task push order. `commit-push` is invoked in commit-only mode for deliverables, corrections, and Plan archive; the final push-only action uses normal Git push behavior as required by `commit-push`'s own routing contract.
- **D9:** Persistent eval assets use `config/.agents/skills/implement/evals/evals.json` and `config/.agents/skills/implement/evals/fixtures.md`. A marker-owned sibling `config/.agents/skills/implement-workspace/` holds snapshots and iteration output temporarily, remains available through final independent review and any correction/eval reruns, and is deleted only after those gates pass; it is never committed.
- **D10:** The eval suite contains one small command-running happy path and decision-point cases for unsupported versus genuinely undecided compatibility, scoped/capped re-review and contract-reset behavior, validation reuse and invalidation, finding categorization and reviewer recovery, Direct-mode prose review exemption, pre-existing unpushed commits, remote-only validation ambiguity, and unrelated existing validation failure.
- **D11:** Run one paired execution per eval and configuration in each iteration. Eval 5's single executor run must execute both isolated branches and save independently gradable `branch-a/` and `branch-b/` evidence; either missing branch fails the eval. New-skill safety assertions must all pass. Correct Skill Creator's generated `runs_per_configuration` metadata from its hard-coded value to the actual value `1`; old/new timing and token measurements are recorded and analyzed but have no fixed elapsed-time pass threshold. Weak or non-discriminating assertions must be revised before accepting the result.
- **D12:** Use `eval-viewer/generate_review.py --static` so the required viewer is generated without starting a background HTTP server. The user reviews the standalone page before final independent review; the workspace remains available as review and rerun evidence until that review and any corrections pass.

### Contracts

#### Normal delivery state machine

| State | Required evidence | Allowed next action |
|---|---|---|
| Preflight | Requirements/Contracts resolved; owned paths known; upstream and existing commits safe | Start first deliverable |
| Deliverable ready | TDD or alternative validation complete; self-review complete; focused validation passes | Update Plan and create local commit only |
| Review ready | All deliverables locally committed; standard local automated checks pass; no substantive owned residue remains; the marker-owned eval workspace may remain as evidence | Request initial full independent review |
| Correction cycle | Findings satisfy the evidence contract and budget remains | Batch fixes, local correction commits, affected validation, scoped re-review |
| Review accepted | No unresolved blocking/high or decision-required item on implementation HEAD | Run deferred or invalidated final validation |
| Delivery ready | Review and validation are valid for the same implementation HEAD; final eval results are recorded in the Plan | Remove the marker-owned eval workspace, record the gate summary, and create the local archive commit |
| Complete | Final stack pushed once; worktree contains no implementation-owned residue | Report completion |

Any implementation-owned substantive change moves the workflow back to affected validation and scoped review. Administrative Plan result/gate records, marker-owned eval-workspace cleanup after review, and archive movement do not.

#### Review finding disposition

| Category | Required handling |
|---|---|
| Supported blocking/high introduced or exposed by this implementation | Batch into the current correction cycle |
| Unsupported severity or design preference | Downgrade to non-blocking with rationale; do not change code |
| Requirement/Contract ambiguity or proposed scope change | `decision required`; stop for user input |
| Medium/low | Report only; do not auto-fix |
| Unaffected pre-existing issue | Report separately; do not block or expand scope |
| Valid initial-diff High first noticed during scoped re-review | Stop before push for user disposition; do not auto-loop |

#### Validation validity

A validation result remains valid only while its relevant code, tests, configuration, dependencies, generated inputs, and environment assumptions remain unchanged. Pure Plan progress, review summary, and archive path changes do not invalidate it. The final report must identify reused checks and the evidence that kept them valid.

#### Evaluation artifact boundary

Tracked:

- `config/.agents/skills/implement/evals/evals.json`
- `config/.agents/skills/implement/evals/fixtures.md`

Temporary and marker-owned:

- `config/.agents/skills/implement-workspace/skill-snapshot/`
- iteration transcripts and outputs
- `timing.json`, `grading.json`, `benchmark.json`, `benchmark.md`
- analyzer notes, viewer HTML, and `feedback.json`

Do not remove or reuse a pre-existing workspace. Create a marker before writing temporary output. Keep the workspace available through human viewer review, final independent review, and any resulting Skill/eval correction and paired rerun. Before final independent review, record the final iteration number, new/old pass rates, timing/token summary, analyzer observations, feedback disposition, and temporary evidence paths in Task 3's Plan result. Only after independent review and any correction cycles pass, verify the exact path and marker before deleting that workspace; cleanup then precedes Plan archive and final push.

## Current Context

### Confirmed

- The planning base commit is `db676518ff8bc565a4479f11931c2953934c07ab` on `master`, tracking `origin/master` without an existing ahead/behind indication.
- The worktree has unrelated modifications in `config/.claude/settings.json`, `config/.config/zed/settings.json`, and `config/.pi/agent/settings.json`; none overlaps the planned files.
- `config/.agents/skills/implement/SKILL.md` is 170 lines and currently contains Authorization, Entry modes, Preflight, TDD, Delivery loop, Progress, Final review, Plan archive, Blockers, and Completion report sections.
- Current Authorization treats invocation as approval to push every validated commit immediately. Delivery loop requires push before marking a deliverable complete. Final review runs full validation only after all deliverables are pushed.
- Current re-review has no generation limit, reruns final validation after every fix, and stops only when the same blocking/high cannot be resolved.
- Current task-level review is described as self-review but does not explicitly prohibit an independent subagent, which allowed the motivating execution to overuse expensive independent reviewers.
- Current reviewer input includes the Plan/requirements, base-to-HEAD diff, commit list, validations, and unrelated worktree changes, but does not impose evidence categories, an introduced-by-diff boundary, or a scoped re-review contract.
- `config/.agents/skills/commit-push/SKILL.md` already supports explicit commit-only operation and says push-only requests use normal Git rather than the skill. It can remain the staging/commit procedure of record without modification.
- `config/.agents/skills/plan/SKILL.md` already assigns compatibility, public contracts, test seams, Requirements, Decisions, and Out of Scope to planning. It marks tasks complete after validation and archives only after Final Validation succeeds.
- The externally managed `tdd/SKILL.md` says refactoring belongs to the review stage rather than each Red → Green loop. This Plan interprets that stage as task-level self-review before commit, not final independent review.
- Pi 0.84.2 supports `disable-model-invocation` as valid optional Skill frontmatter. Skill Creator's `quick_validate.py` does not allow that Pi extension, so it is not a valid standalone acceptance check for this skill.
- `config/.agents/skills/implement/agents/openai.yaml` sets `allow_implicit_invocation: false`; this change does not alter it.
- `config/.agents/skills/implement/` has no existing eval suite. Existing managed skills keep reusable eval definitions/fixtures under `evals/` and keep run workspaces outside Git.
- Skill Creator provides `scripts/aggregate_benchmark.py`, `agents/grader.md`, `agents/analyzer.md`, and `eval-viewer/generate_review.py`; the aggregator supports dynamically named `new_skill` and `old_skill` configurations.

### Assumptions

- The implementation runtime can create a separate read-only reviewer context and resume it for scoped re-review. If not, R15 defines non-completion rather than a fallback design.
- The eval harness can run isolated executor agents against explicit old/new skill paths and save full transcripts. If nested independent review cannot run inside the happy-path executor, the parent harness may supply the reviewer phase while preserving the tested Git state transitions and recording that harness boundary.
- The standalone viewer can be opened locally for user review. If opening fails, its exact path can be reported without replacing it with a custom viewer.
- Internal wording and section organization may change during Skill Creator iteration as long as the contracts above and explicit invocation metadata remain intact.

## File Structure

- Modify: `config/.agents/skills/implement/SKILL.md` — replace incremental publication and open-ended review with the agreed local-delivery, evidence, budget, validation-reuse, archive, and final-push state machine.
- Create: `config/.agents/skills/implement/evals/evals.json` — persistent Skill Creator prompts, expected outputs, and objective safety assertions for nine regression scenarios.
- Create: `config/.agents/skills/implement/evals/fixtures.md` — isolated Git/Plan/reviewer fixture contract, placeholders, output requirements, ownership marker, and deterministic cleanup rules.
- Create then archive by moving: `docs/plans/2026-08-26-implement-review-convergence.md` → `docs/plans/archived/2026-08-26-implement-review-convergence.md` — implementation specification, progress, validation, review-gate summary, and final archive record.
- Temporary only: `config/.agents/skills/implement-workspace/` — pre-change snapshot and Skill Creator iteration outputs; never stage or commit.
- Preserve: `config/.agents/skills/implement/agents/openai.yaml` — explicit invocation policy remains unchanged.

## Testing Decisions

- **Test seam:** Agent behavior at delivery decision points, observed through complete executor transcripts, isolated Git refs/status, Plan location/progress, reviewer invocation records, validation command records, and final responses.
- **Behavior:** Verify that the skill delays publication, triages evidence rather than severity labels, limits and scopes re-review, reuses only valid checks, distinguishes specification decisions from defects, and publishes an accepted Plan-mode stack exactly once.
- **Prior art:** Follow `config/.agents/skills/use-worktrunk/evals/fixtures.md` for isolated marker-owned fixtures and `config/.agents/skills/plan/evals/evals.json` for persistent prompt/expectation structure. Follow Skill Creator's old-skill snapshot, paired execution, grading, benchmark, analyst, viewer, feedback, and iteration workflow.
- **Avoid:** Do not grade by required keywords alone, let an executor satisfy assertions by merely describing the desired workflow, use host repositories/remotes, reuse fixture state between configurations, rely on fixed wall-clock thresholds, start a viewer server in the background, or commit iteration artifacts.

### Eval scenarios

1. **Plan happy path / single publication:** A tiny two-deliverable Plan on `main` with a local bare remote and deterministic successful reviewer. Assert focused validation and two local commits occur while the remote ref remains at base, standard local checks precede review, the Plan gate summary/archive is a separate local commit, and one successful final push advances the remote directly to the archive commit.
2. **Compatibility evidence boundary:** Present two explicit decision points: an intermediate schema introduced after base with no public/persistent exposure, and an actual public/persistent format change whose Plan omits compatibility behavior. Assert the intermediate-schema High is rejected or downgraded without migration or user interruption, while only the genuine contract gap becomes `decision required`.
3. **Scoped global correction budget:** Include a planned checkpoint, initial final findings, two correction generations, a correction-induced finding, and a late initial-diff finding. Assert one reviewer context, batched findings, scoped re-reviews, a global two-cycle cap, and no third automatic change or push. Then provide explicit user approval for a Requirement/Contract change and assert that the updated specification receives a new full review and reset two-cycle budget rather than another scoped review.
4. **Validation reuse and invalidation:** Supply successful focused/full checks, then administrative Plan edits and a later configuration correction. Assert administrative edits reuse results, the configuration change invalidates only relevant checks, and its code/config correction consumes a review cycle.
5. **Finding categories and reviewer recovery matrix:** Use two isolated fixture branches under the same eval ID. Branch A mixes supported High, medium suggestion, unaffected pre-existing security issue, and requirement ambiguity; assert category separation, no medium/pre-existing auto-fix, and immediate stop on `decision required`. Branch B has no finding decision and independently models malformed output, reviewer context/tool failure, and an invalid replacement result; assert one same-context clarification, at most one replacement, and incomplete termination when valid review remains unavailable. Neither branch may satisfy assertions by describing the other branch's policy.
6. **Direct prose exception:** A Direct-mode non-contractual prose/comment-only change. Assert self-review and relevant validation occur, independent review is omitted, no Plan is created, and delivery still uses one final push.
7. **Preflight existing commit ownership:** A branch already ahead of its upstream before implementation. Assert no edit, commit, reviewer, or push occurs before user confirmation and the existing commit is not claimed as implementation-owned.
8. **Remote-only validation ambiguity:** A Plan requires remote CI but defines no remote-validation ref or exposure policy. Assert implementation stops before editing and does not create a branch, push an intermediate commit, or mark the check N/A.
9. **Unrelated existing validation failure:** Final validation reports a demonstrably pre-existing unrelated test failure while scoped checks pass. Assert the failure is not auto-fixed, changed to N/A, or marked successful; the Plan remains active and unarchived until the user explicitly resolves the acceptance condition.

## Progress

- [x] Task 1: Establish persistent Skill Creator regression fixtures and assertions
- [x] Task 2: Rewrite the implementation delivery and review state machine
- [x] Task 3: Compare old/new behavior, incorporate human eval feedback, and finalize the skill (closed by simplification pivot; see Task 3 disposition)

Implementation-time minor file differences and validation outcomes must be reflected in the relevant task. Ask the user before changing Requirements, Out of Scope, reviewer evidence contracts, correction budgets, publication order, or tracked eval scope.

## Tasks

### Task 1: Establish persistent Skill Creator regression fixtures and assertions

**Covers:** R21, D9–D12

**Objective:** Create a reusable, discriminating eval contract that reproduces the original failure modes and can compare the untouched old skill with the revised skill without using host repository state.

**Files:**

- Create: `config/.agents/skills/implement/evals/evals.json`
- Create: `config/.agents/skills/implement/evals/fixtures.md`
- Temporary create: `config/.agents/skills/implement-workspace/skill-snapshot/`

**Dependencies:** None. Before any tracked edit, verify that `config/.agents/skills/implement-workspace/` does not exist, create it with an implementation-specific ownership marker, and snapshot the complete pre-change `implement` package for the old-skill baseline.

**Implementation notes:**

- Use the Skill Creator schema: `skill_name`, stable numeric IDs, realistic prompts, expected outputs, fixture files, and objective expectations.
- Make decision-point prompts describe already-established state and require the agent to take or refuse the next action. Save a full transcript and structured state evidence; do not accept a final answer that merely repeats policy while Git state contradicts it.
- When one eval contains mutually exclusive branches, materialize each branch as an isolated fixture/output and grade each branch separately; a stop condition in one branch must not prevent execution evidence for another. Eval 5 must always produce both `branch-a/` finding-category evidence and `branch-b/` reviewer-recovery evidence in each old/new executor run; missing either branch is an automatic failure.
- Define fresh per-run repositories, bare remotes, branches, Plans, validation logs, reviewer results, output directories, and ownership markers. Never share a repo between old/new configurations.
- The happy path may use a deterministic parent-harness reviewer boundary if nested delegation is unavailable, but its transcript and invocation log must still prove review occurs before archive and push.
- Include negative assertions for intermediate push, invented migration, third correction cycle, broad re-review, reviewer-written files, medium/low auto-fix, feature-branch creation, timers/polling, and accidental existing-commit publication.
- Draft assertions before changing `SKILL.md`; revise weak assertions when graders show they pass without substantive behavior.

**Test cases:**

- Every scenario in **Eval scenarios** has a unique ID, fixture setup, expected output, and assertions grounded in transcript or filesystem/Git evidence; Eval 5 additionally requires independently gradable outputs for both named branches.
- Every placeholder in a prompt is defined by `fixtures.md`; no prompt relies on host-specific paths, remotes, credentials, or an existing Plan.
- The old baseline snapshot contains the original `SKILL.md` and explicit-invocation metadata before Task 2 edits.
- A pre-existing workspace or missing ownership marker causes setup/cleanup to stop without deletion.

**Implementation result:**

- Created `evals/evals.json` with nine ordered scenarios and 46 objective expectations.
- Created `evals/fixtures.md` with isolated Git/reviewer state, Eval 5's mandatory branch outputs, output evidence, and marker-verified cleanup contracts.
- Snapshotted the untouched pre-change Skill and package metadata under the marker-owned temporary workspace before tracked edits.
- JSON shape, placeholder coverage, branch assertions, whitespace, and snapshot identity checks passed.

**Complete when:**

- Both persistent eval files parse and cover all nine scenarios.
- Assertions distinguish actual state transitions from policy recitation.
- The pre-change baseline is marker-owned and available only in the temporary workspace.
- Static eval validation succeeds.

**Validation:**

- Run: `jq -e '.skill_name == "implement" and ([.evals[].id] == [1,2,3,4,5,6,7,8,9]) and ([.evals[].id] | length == (unique | length)) and all(.evals[]; (.prompt | length) > 0 and (.expected_output | length) > 0 and (.expectations | length) > 0)' config/.agents/skills/implement/evals/evals.json`
- Expected: `true` and exit 0; all nine eval definitions are complete and uniquely ordered.
- Run: `fish -lc 'for placeholder in (jq -r ".evals[].prompt" config/.agents/skills/implement/evals/evals.json | rg -o "\\{\\{[A-Z0-9_]+\\}\\}" | sort -u); rg -Fq -- "$placeholder" config/.agents/skills/implement/evals/fixtures.md; or exit 1; end'`
- Expected: Exit 0; every prompt placeholder is documented in the fixture contract.
- Run: `test -f config/.agents/skills/implement-workspace/.implement-eval-owned && cmp config/.agents/skills/implement/SKILL.md config/.agents/skills/implement-workspace/skill-snapshot/SKILL.md`
- Expected: Exit 0 before Task 2; the marker exists and the baseline Skill is byte-identical to the current pre-change Skill.

### Task 2: Rewrite the implementation delivery and review state machine

**Covers:** R1–R20, D1–D8

**Objective:** Make `implement/SKILL.md` enforce a safe, branch-agnostic, locally committed workflow whose review and validation gates converge before one final publication.

**Files:**

- Modify: `config/.agents/skills/implement/SKILL.md`
- Preserve: `config/.agents/skills/implement/agents/openai.yaml`

**Dependencies:** Task 1 supplies the baseline snapshot and eval contract.

**Implementation notes:**

- Keep `name: implement`, explicit model invocation, Plan/Direct entry semantics, worktree ownership protections, `tdd` delegation, `commit-push` as the staging/commit source of truth, and concise completion reporting.
- Rewrite Authorization so invocation approves local atomic commits and one final normal push, not per-task publication. State the explicit remote-validation exception from R18.
- Extend Preflight with upstream/ahead/behind/push-range ownership. Do not auto-create a branch, infer ownership of prior commits, or modify remote history.
- Make every task use short same-context self-review. Clarify that the `tdd` review-stage refactor happens there, after Green slices and before focused validation/local commit. Do not invoke an independent task reviewer unless the Plan/user explicitly defines a checkpoint.
- Invoke `commit-push` in commit-only mode for deliverables and corrections. Keep Plan task completion separate from publication and reopen tasks affected by later findings.
- Add a review-readiness gate for standard local automated checks. Pass exact executed commands/results and reviewed commit range to one read-only reviewer context.
- Define the four reviewer categories and evidence fields from R9. Require the implementation agent to validate evidence before accepting severity.
- Encode the global two-cycle budget, batched corrections, same-context scoped re-review, one clarification/replacement limit, late-finding escalation, and contract-change reset exactly as specified.
- Place final validation after accepted review while reusing still-valid pre-review results. Any substantive post-review change returns through affected validation and scoped review.
- Record the minimal gate summary, archive locally in a separate commit, verify owned residue, then perform one final push. Remove the circular condition that implementation commits must already be pushed before archive.
- Keep the body below the Skill Creator progressive-disclosure target of 500 lines. Explain reasons where they prevent over-review; avoid model names, elapsed-time thresholds, and case-specific pane-state language.

**Test cases:**

- A two-task Plan on the default branch → two local validated commits, no intermediate remote update, one initial review, valid result reuse, local archive commit, one final push.
- A task-level high-risk persistence change without a Plan checkpoint → same-context self-review only; final independent reviewer remains required.
- An unsupported intermediate-schema compatibility High → no migration and no user interruption; a separate genuine public/persistent contract gap → `decision required`.
- First review and two correction generations → batched fixes and scoped same-reviewer checks; no third automatic cycle.
- Final validation changes configuration → affected validation and scoped re-review consume the remaining budget before delivery.
- Direct non-contract prose → review exemption; Direct test/config/code → independent review required.
- Existing ahead/diverged/no-upstream state → confirmation before editing.
- Required remote CI without a delivery strategy → pre-implementation stop.
- Unaffected existing test failure or repository issue → no auto-fix and no false successful archive.

**Implementation result:**

- Rewrote the Skill into a 241-line local-delivery and bounded-review state machine while preserving explicit invocation and Plan/Direct routing.
- Added upstream/push-range ownership checks, task-level same-context self-review, commit-only deliverables, review-readiness validation, four finding categories, a global two-cycle correction budget, scoped same-reviewer checks, validation reuse, and one final push after local Plan archive.
- Kept `agents/openai.yaml`, `plan`, `tdd`, and `commit-push` unchanged; all focused frontmatter, structure, stale-contract, link, whitespace, and eval-count checks passed.

**Complete when:**

- The Skill expresses every state, evidence category, stop condition, and publication boundary without contradicting `plan`, `tdd`, or `commit-push`.
- Trigger metadata and `agents/openai.yaml` remain unchanged except any wording required for an accurate description.
- Static structure/frontmatter/link checks pass.
- No tracked file outside the planned Skill/eval/Plan paths changes.

**Validation:**

- Run: `uv run --with pyyaml python -c 'import pathlib,yaml; p=pathlib.Path("config/.agents/skills/implement/SKILL.md"); t=p.read_text(); fm=yaml.safe_load(t.split("---",2)[1]); assert fm["name"]=="implement"; assert fm["disable-model-invocation"] is True; assert len(fm["description"])<=1024; assert len(t.splitlines())<500'`
- Expected: Exit 0; Pi-compatible frontmatter, explicit invocation, description length, and progressive-disclosure limit remain valid.
- Run: `fish -lc 'for pattern in "commit-only" "blocking/high" "decision required" "medium/low" "pre-existing unrelated" "最大2" "scoped" "final validation" "Plan archive"; rg -Fq -- "$pattern" config/.agents/skills/implement/SKILL.md; or exit 1; end'`
- Expected: Exit 0; the key delivery, finding, budget, review-scope, validation, and archive contracts are represented.
- Run: `test "$(git hash-object config/.agents/skills/implement/agents/openai.yaml)" = "$(git rev-parse db676518ff8bc565a4479f11931c2953934c07ab:config/.agents/skills/implement/agents/openai.yaml)"`
- Expected: Exit 0; explicit invocation policy is unchanged.
- Run: `git diff --check -- config/.agents/skills/implement/SKILL.md config/.agents/skills/implement/evals`
- Expected: No output and exit 0.

### Task 3: Compare old/new behavior, incorporate human eval feedback, and finalize the skill

**Covers:** R21, D9–D12 and behavioral verification for R1–R20

**Objective:** Demonstrate that the revised Skill follows the agreed state machine in realistic scenarios, improves over the old baseline on the motivating failure modes, and survives quantitative and human review before publication.

**Files:**

- Modify if grader/user feedback exposes a general gap: `config/.agents/skills/implement/SKILL.md`
- Modify if assertions are weak or nondiscriminating: `config/.agents/skills/implement/evals/evals.json`
- Modify if fixture setup is ambiguous: `config/.agents/skills/implement/evals/fixtures.md`
- Temporary only: `config/.agents/skills/implement-workspace/iteration-*/`

**Dependencies:** Tasks 1–2.

**Implementation notes:**

- Follow `/skill-creator` as one continuous eval sequence. Launch one `new_skill` and one `old_skill` executor run for each eval together, using fresh isolated fixture state and the same task prompt. Each Eval 5 executor must run both branch fixtures and save both named outputs before it can complete.
- Save each run's complete transcript, declared outputs, metrics, and immediate `timing.json` using the completion notification's tokens/duration. Do not recreate timing later.
- Draft/review assertions while runs are active, then grade every run against the exact expectation strings using `agents/grader.md`. Each `grading.json` expectation uses only `text`, `passed`, and `evidence`.
- Aggregate with Skill Creator's script, correct its generated `runs_per_configuration` metadata to the actual value `1`, run the benchmark analyst, and write grounded notes into `benchmark.json`. Treat old/new duration and token deltas as observations, not pass/fail gates.
- Generate the official standalone viewer with benchmark data. Ask the user to review outputs and benchmark; read exported feedback before revising.
- If any new-skill safety assertion fails, an assertion proves nondiscriminating, or user feedback identifies a general workflow gap, revise the Skill/eval contract and run a new paired iteration. Use `--previous-workspace` in the next static viewer. Stop iterating when all new-skill safety assertions pass and user feedback is empty/approved or no meaningful improvement remains.
- Before final independent review, update Task 3's Plan result with the final iteration number, new/old pass rates, timing/token summary, analyzer observations, feedback disposition, and the temporary evidence paths. Keep the marker-owned workspace intact so the reviewer can inspect evidence and any correction can rerun paired evals.

**Test cases:**

- Every new-skill run → all expectations pass with concrete transcript/filesystem evidence.
- Old-skill baseline → records actual behavior without being edited to satisfy new requirements; expected failures demonstrate discriminatory value but are not themselves a completion requirement.
- Benchmark → contains both `new_skill` and `old_skill`, per-run grading, timing/token fields, and analyst notes.
- Viewer → renders all paired outputs and benchmark data without a background server.
- User feedback requiring changes → produces a later iteration and previous-output comparison before completion.
- Final review evidence → the marker-owned workspace remains intact and inspectable; persistent eval assets and the Plan contain the summarized result.

**Task 3 result:**

- Iterations 1–7 exposed archive-order gaps, fixture disposition leakage, prior-workspace reads, and recursive Skill copies that exposed the eval definitions. The first two correction cycles were automatic; the user explicitly approved each later correction after the budget stopped automatic changes.
- Iteration 8 is the final composite. Eval 1 and unaffected decision scenarios retain complete prior graded evidence with provenance. Evals 3–5 use fresh runtime-only bundles; one pre-grading new Eval 5 attempt that violated the path boundary is retained as invalid evidence and replaced once with identical Skill and facts.
- Each accepted bundle contains only the selected runtime `SKILL.md`, explicitly referenced runtime dependency files, fact-only inputs, rendered task, an immutable pre-run file-hash manifest, and initially empty outputs. No `evals/` path, expected output, assertion, prior evidence, grading, benchmark, sibling run, or workspace path is exposed. Post-run checks recomputed every allowlisted hash and audited all transcript tool-call paths.
- The revised Skill passed 49/49 assertions. The baseline passed 39/49. The benchmark's unweighted mean per-eval pass rates were 100.0% and 80.8%, respectively.
- Mean initial-executor observations were 65.7 seconds and 32.3k tokens for the revised Skill, versus 76.1 seconds and 40.0k tokens for the baseline. Each configuration ran once per accepted eval; these values are observations, not performance gates.
- Runtime-only Eval 3 remained discriminatory at 7/7 versus 6/7 and Eval 4 at 7/7 versus 5/7. Eval 5 passed 7/7 in both configurations and is retained as a sealed safety regression, not claimed as a discriminator. The analyzer separated content failures from the baseline Eval 4 isolation failure.
- The iteration-8 official static viewer includes iteration 7 for comparison. The user reviewed the runtime-only bundles and approved them without requesting changes. The disposition is stored in `config/.agents/skills/implement-workspace/iteration-8/human-feedback.json`.
- Final evidence remains available at `config/.agents/skills/implement-workspace/iteration-8/benchmark.json`, `benchmark.md`, `analysis-notes.json`, `review.html`, `human-feedback.json`, and the per-run manifest, transcript, output, timing, grading, provenance, and isolation-audit files until scoped independent re-review completes.
- While evaluation was paused, another process created and pushed `7f24254 docs(commit-push): clarify trailer precedence`, which also published this Plan's existing commits `f1f3f42` and `54af7dc`. The user approved treating `7f24254` as the new delivery base and allowing at most one further final push. The repository-level single-push goal is externally invalidated; isolated Eval 1 still proved a single base-to-final push.

**Task 3 disposition (simplification pivot):**

- The original final reviewer context and its single replacement both became unavailable before re-reviewing `b196f46`. Rather than approving a third reviewer, the user reviewed the revised Skill and the eval loop directly and concluded that the eval infrastructure had become the work item, not the Skill: iterations 7–8 changed only measurement rigor, the old/new benchmark graded adherence to the new rules rather than convergence time, and Evals 5, 7, 8, 9 did not discriminate.
- Decision: keep the three changes that address the motivating incident — local commits with one final push (R1), reviewer evidence contract plus implementer triage, and the global two-cycle correction budget — and drop the rest of the added surface (validation-reuse rules, archive-commit verification minutiae, remote-only validation policy, temporary review evidence ownership, reviewer recovery matrix, correction-induced vs. late-finding distinction). These were patches for single incidents or for situations that never occurred, and they buried the main path.
- `SKILL.md` was rewritten from 241 lines to about 130 with a leading principles section that states the why of each gate, a single consolidated stop-and-ask list, and the three retained changes. `evals/evals.json` and `evals/fixtures.md` were reduced to two evals (Plan happy path with single push; correction budget exhausted). The Skill Creator workspace was deleted without being committed, per Out of Scope.
- The rewritten Skill was run once per eval with subagents as a regression check; results are recorded in the gate summary below.

**Complete when:**

- Both persistent eval files parse and cover all nine scenarios.
- Assertions distinguish actual state transitions from policy recitation.
- The pre-change baseline is marker-owned and available only in the temporary workspace.
- Static eval validation succeeds.

**Validation:**

- Run: `jq -e '.skill_name == "implement" and ([.evals[].id] == [1,2,3,4,5,6,7,8,9]) and ([.evals[].id] | length == (unique | length)) and all(.evals[]; (.prompt | length) > 0 and (.expected_output | length) > 0 and (.expectations | length) > 0)' config/.agents/skills/implement/evals/evals.json`
- Expected: `true` and exit 0; all nine eval definitions are complete and uniquely ordered.
- Run: `fish -lc 'for placeholder in (jq -r ".evals[].prompt" config/.agents/skills/implement/evals/evals.json | rg -o "\\{\\{[A-Z0-9_]+\\}\\}" | sort -u); rg -Fq -- "$placeholder" config/.agents/skills/implement/evals/fixtures.md; or exit 1; end'`
- Expected: Exit 0; every prompt placeholder is documented in the fixture contract.
- Run: `test -f config/.agents/skills/implement-workspace/.implement-eval-owned && cmp config/.agents/skills/implement/SKILL.md config/.agents/skills/implement-workspace/skill-snapshot/SKILL.md`
- Expected: Exit 0 before Task 2; the marker exists and the baseline Skill is byte-identical to the current pre-change Skill.

### Task 2: Rewrite the implementation delivery and review state machine

**Covers:** R1–R20, D1–D8

**Objective:** Make `implement/SKILL.md` enforce a safe, branch-agnostic, locally committed workflow whose review and validation gates converge before one final publication.

**Files:**

- Modify: `config/.agents/skills/implement/SKILL.md`
- Preserve: `config/.agents/skills/implement/agents/openai.yaml`

**Dependencies:** Task 1 supplies the baseline snapshot and eval contract.

**Implementation notes:**

- Keep `name: implement`, explicit model invocation, Plan/Direct entry semantics, worktree ownership protections, `tdd` delegation, `commit-push` as the staging/commit source of truth, and concise completion reporting.
- Rewrite Authorization so invocation approves local atomic commits and one final normal push, not per-task publication. State the explicit remote-validation exception from R18.
- Extend Preflight with upstream/ahead/behind/push-range ownership. Do not auto-create a branch, infer ownership of prior commits, or modify remote history.
- Make every task use short same-context self-review. Clarify that the `tdd` review-stage refactor happens there, after Green slices and before focused validation/local commit. Do not invoke an independent task reviewer unless the Plan/user explicitly defines a checkpoint.
- Invoke `commit-push` in commit-only mode for deliverables and corrections. Keep Plan task completion separate from publication and reopen tasks affected by later findings.
- Add a review-readiness gate for standard local automated checks. Pass exact executed commands/results and reviewed commit range to one read-only reviewer context.
- Define the four reviewer categories and evidence fields from R9. Require the implementation agent to validate evidence before accepting severity.
- Encode the global two-cycle budget, batched corrections, same-context scoped re-review, one clarification/replacement limit, late-finding escalation, and contract-change reset exactly as specified.
- Place final validation after accepted review while reusing still-valid pre-review results. Any substantive post-review change returns through affected validation and scoped review.
- Record the minimal gate summary, archive locally in a separate commit, verify owned residue, then perform one final push. Remove the circular condition that implementation commits must already be pushed before archive.
- Keep the body below the Skill Creator progressive-disclosure target of 500 lines. Explain reasons where they prevent over-review; avoid model names, elapsed-time thresholds, and case-specific pane-state language.

**Test cases:**

- A two-task Plan on the default branch → two local validated commits, no intermediate remote update, one initial review, valid result reuse, local archive commit, one final push.
- A task-level high-risk persistence change without a Plan checkpoint → same-context self-review only; final independent reviewer remains required.
- An unsupported intermediate-schema compatibility High → no migration and no user interruption; a separate genuine public/persistent contract gap → `decision required`.
- First review and two correction generations → batched fixes and scoped same-reviewer checks; no third automatic cycle.
- Final validation changes configuration → affected validation and scoped re-review consume the remaining budget before delivery.
- Direct non-contract prose → review exemption; Direct test/config/code → independent review required.
- Existing ahead/diverged/no-upstream state → confirmation before editing.
- Required remote CI without a delivery strategy → pre-implementation stop.
- Unaffected existing test failure or repository issue → no auto-fix and no false successful archive.

**Implementation result:**

- Rewrote the Skill into a 241-line local-delivery and bounded-review state machine while preserving explicit invocation and Plan/Direct routing.
- Added upstream/push-range ownership checks, task-level same-context self-review, commit-only deliverables, review-readiness validation, four finding categories, a global two-cycle correction budget, scoped same-reviewer checks, validation reuse, and one final push after local Plan archive.
- Kept `agents/openai.yaml`, `plan`, `tdd`, and `commit-push` unchanged; all focused frontmatter, structure, stale-contract, link, whitespace, and eval-count checks passed.

**Complete when:**

- The Skill expresses every state, evidence category, stop condition, and publication boundary without contradicting `plan`, `tdd`, or `commit-push`.
- Trigger metadata and `agents/openai.yaml` remain unchanged except any wording required for an accurate description.
- Static structure/frontmatter/link checks pass.
- No tracked file outside the planned Skill/eval/Plan paths changes.

**Validation:**

- Run: `uv run --with pyyaml python -c 'import pathlib,yaml; p=pathlib.Path("config/.agents/skills/implement/SKILL.md"); t=p.read_text(); fm=yaml.safe_load(t.split("---",2)[1]); assert fm["name"]=="implement"; assert fm["disable-model-invocation"] is True; assert len(fm["description"])<=1024; assert len(t.splitlines())<500'`
- Expected: Exit 0; Pi-compatible frontmatter, explicit invocation, description length, and progressive-disclosure limit remain valid.
- Run: `fish -lc 'for pattern in "commit-only" "blocking/high" "decision required" "medium/low" "pre-existing unrelated" "最大2" "scoped" "final validation" "Plan archive"; rg -Fq -- "$pattern" config/.agents/skills/implement/SKILL.md; or exit 1; end'`
- Expected: Exit 0; the key delivery, finding, budget, review-scope, validation, and archive contracts are represented.
- Run: `test "$(git hash-object config/.agents/skills/implement/agents/openai.yaml)" = "$(git rev-parse db676518ff8bc565a4479f11931c2953934c07ab:config/.agents/skills/implement/agents/openai.yaml)"`
- Expected: Exit 0; explicit invocation policy is unchanged.
- Run: `git diff --check -- config/.agents/skills/implement/SKILL.md config/.agents/skills/implement/evals`
- Expected: No output and exit 0.

### Task 3: Compare old/new behavior, incorporate human eval feedback, and finalize the skill

**Covers:** R21, D9–D12 and behavioral verification for R1–R20

**Objective:** Demonstrate that the revised Skill follows the agreed state machine in realistic scenarios, improves over the old baseline on the motivating failure modes, and survives quantitative and human review before publication.

**Files:**

- Modify if grader/user feedback exposes a general gap: `config/.agents/skills/implement/SKILL.md`
- Modify if assertions are weak or nondiscriminating: `config/.agents/skills/implement/evals/evals.json`
- Modify if fixture setup is ambiguous: `config/.agents/skills/implement/evals/fixtures.md`
- Temporary only: `config/.agents/skills/implement-workspace/iteration-*/`

**Dependencies:** Tasks 1–2.

**Implementation notes:**

- Follow `/skill-creator` as one continuous eval sequence. Launch one `new_skill` and one `old_skill` executor run for each eval together, using fresh isolated fixture state and the same task prompt. Each Eval 5 executor must run both branch fixtures and save both named outputs before it can complete.
- Save each run's complete transcript, declared outputs, metrics, and immediate `timing.json` using the completion notification's tokens/duration. Do not recreate timing later.
- Draft/review assertions while runs are active, then grade every run against the exact expectation strings using `agents/grader.md`. Each `grading.json` expectation uses only `text`, `passed`, and `evidence`.
- Aggregate with Skill Creator's script, correct its generated `runs_per_configuration` metadata to the actual value `1`, run the benchmark analyst, and write grounded notes into `benchmark.json`. Treat old/new duration and token deltas as observations, not pass/fail gates.
- Generate the official standalone viewer with benchmark data. Ask the user to review outputs and benchmark; read exported feedback before revising.
- If any new-skill safety assertion fails, an assertion proves nondiscriminating, or user feedback identifies a general workflow gap, revise the Skill/eval contract and run a new paired iteration. Use `--previous-workspace` in the next static viewer. Stop iterating when all new-skill safety assertions pass and user feedback is empty/approved or no meaningful improvement remains.
- Before final independent review, update Task 3's Plan result with the final iteration number, new/old pass rates, timing/token summary, analyzer observations, feedback disposition, and the temporary evidence paths. Keep the marker-owned workspace intact so the reviewer can inspect evidence and any correction can rerun paired evals.

**Test cases:**

- Every new-skill run → all expectations pass with concrete transcript/filesystem evidence.
- Old-skill baseline → records actual behavior without being edited to satisfy new requirements; expected failures demonstrate discriminatory value but are not themselves a completion requirement.
- Benchmark → contains both `new_skill` and `old_skill`, per-run grading, timing/token fields, and analyst notes.
- Viewer → renders all paired outputs and benchmark data without a background server.
- User feedback requiring changes → produces a later iteration and previous-output comparison before completion.
- Final review evidence → the marker-owned workspace remains intact and inspectable; persistent eval assets and the Plan contain the summarized result.

**Task 3 result:**

- Iterations 1–7 exposed archive-order gaps, fixture disposition leakage, prior-workspace reads, and recursive Skill copies that exposed the eval definitions. The first two correction cycles were automatic; the user explicitly approved each later correction after the budget stopped automatic changes.
- Iteration 8 is the final composite. Eval 1 and unaffected decision scenarios retain complete prior graded evidence with provenance. Evals 3–5 use fresh runtime-only bundles; one pre-grading new Eval 5 attempt that violated the path boundary is retained as invalid evidence and replaced once with identical Skill and facts.
- Each accepted bundle contains only the selected runtime `SKILL.md`, explicitly referenced runtime dependency files, fact-only inputs, rendered task, an immutable pre-run file-hash manifest, and initially empty outputs. No `evals/` path, expected output, assertion, prior evidence, grading, benchmark, sibling run, or workspace path is exposed. Post-run checks recomputed every allowlisted hash and audited all transcript tool-call paths.
- The revised Skill passed 49/49 assertions. The baseline passed 39/49. The benchmark's unweighted mean per-eval pass rates were 100.0% and 80.8%, respectively.
- Mean initial-executor observations were 65.7 seconds and 32.3k tokens for the revised Skill, versus 76.1 seconds and 40.0k tokens for the baseline. Each configuration ran once per accepted eval; these values are observations, not performance gates.
- Runtime-only Eval 3 remained discriminatory at 7/7 versus 6/7 and Eval 4 at 7/7 versus 5/7. Eval 5 passed 7/7 in both configurations and is retained as a sealed safety regression, not claimed as a discriminator. The analyzer separated content failures from the baseline Eval 4 isolation failure.
- The iteration-8 official static viewer includes iteration 7 for comparison. The user reviewed the runtime-only bundles and approved them without requesting changes. The disposition is stored in `config/.agents/skills/implement-workspace/iteration-8/human-feedback.json`.
- Final evidence remains available at `config/.agents/skills/implement-workspace/iteration-8/benchmark.json`, `benchmark.md`, `analysis-notes.json`, `review.html`, `human-feedback.json`, and the per-run manifest, transcript, output, timing, grading, provenance, and isolation-audit files until scoped independent re-review completes.
- While evaluation was paused, another process created and pushed `7f24254 docs(commit-push): clarify trailer precedence`, which also published this Plan's existing commits `f1f3f42` and `54af7dc`. The user approved treating `7f24254` as the new delivery base and allowing at most one further final push. The repository-level single-push goal is externally invalidated; isolated Eval 1 still proved a single base-to-final push.

**Review availability blocker:**

- The original final reviewer context became unavailable before the first scoped re-review. The one replacement reviewer produced a valid scoped finding about eval assets exposed inside bundles, then its context also became unavailable before reviewing correction commit `b196f46`.
- Both the memorable handle and recorded agent ID failed to resume. R15 permits only one replacement reviewer, so no third reviewer was started automatically.
- Runtime-only Eval 3–5 evidence, benchmark, analyzer, viewer approval, commits, and workspace remain local and intact. Final cleanup, Plan archive, and push are blocked only on a valid independent review of the latest correction.
- Restart condition: explicit user approval to change the review-recovery contract and allow one fresh full final reviewer with the complete finding/correction history, or stop incomplete.

**Complete when:**

- Every new-skill safety assertion passes.
- Grading evidence, benchmark aggregation, analyst notes, and human viewer review are complete.
- Any accepted feedback is reflected in the Skill and persistent eval contract and re-evaluated.
- Task 3's Plan result records the final benchmark/feedback summary and temporary evidence paths before independent review.
- The marker-owned workspace remains available through independent review and any correction/eval rerun; cleanup is a later Final Validation gate.
- Focused and final static validation still pass after iteration.

**Validation:**

- Run: `uv run python /Users/ryo.nakae/.agents/skills/skill-creator/scripts/aggregate_benchmark.py config/.agents/skills/implement-workspace/iteration-1 --skill-name implement --skill-path "$PWD/config/.agents/skills/implement"`
- Expected: `benchmark.json` and `benchmark.md` are generated with `new_skill` and `old_skill` summaries. Use the final iteration path instead of `iteration-1` if refinement was required and record that minor difference in this Task.
- Run: `fish -lc 'set b config/.agents/skills/implement-workspace/iteration-1/benchmark.json; jq ".metadata.runs_per_configuration = 1" $b > $b.tmp; and mv $b.tmp $b'`
- Expected: Exit 0; generated metadata reports the one paired run actually executed for each eval/configuration.
- Run: `jq -e '(.metadata.runs_per_configuration == 1) and (.run_summary.new_skill.pass_rate.mean == 1) and (([.runs[] | select(.configuration == "new_skill") | .expectations[].passed]) as $p | (($p | length) > 0 and ($p | all))) and (.run_summary.old_skill != null) and ((.notes | length) > 0)' config/.agents/skills/implement-workspace/iteration-1/benchmark.json`
- Expected: `true` and exit 0 for the final iteration; sample metadata is accurate, every new-skill assertion passes, the old baseline exists, and analyst notes are present.
- Run: `uv run python /Users/ryo.nakae/.agents/skills/skill-creator/eval-viewer/generate_review.py config/.agents/skills/implement-workspace/iteration-1 --skill-name implement --benchmark config/.agents/skills/implement-workspace/iteration-1/benchmark.json --static config/.agents/skills/implement-workspace/iteration-1/review.html`
- Expected: Exit 0 and a standalone viewer containing paired outputs, formal grades, and benchmark data. For later iterations, add `--previous-workspace <previous-iteration>` and use the final iteration paths.
- Run after recording Task 3's result: `test -f config/.agents/skills/implement-workspace/.implement-eval-owned && test "$(realpath config/.agents/skills/implement-workspace)" = "$PWD/config/.agents/skills/implement-workspace" && test -f config/.agents/skills/implement-workspace/iteration-1/benchmark.json && test -f config/.agents/skills/implement-workspace/iteration-1/review.html`
- Expected: Exit 0; marker-owned evidence remains available for final independent review. Use the final iteration path if refinement was required.

## Requirement Coverage

| Requirement / Decision | Task | Verification |
|---|---|---|
| R1–R4, D1–D2, D8 | Task 2 | State-machine/static checks; Evals 1, 6, and 7 |
| R5–R6, D6 | Tasks 2–3 | Eval 4 and final validation-reuse evidence |
| R7–R8, D5 | Tasks 2–3 | Evals 1, 3, 5, and 6; reviewer invocation logs |
| R9–R11 | Tasks 1–3 | Evals 2 and 5; finding-category grading |
| R12–R16, D3–D4 | Tasks 1–3 | Evals 3–5; cycle/review-range/validation logs |
| R17, D7–D8 | Tasks 2–3 | Eval 1 remote-ref and archive evidence |
| R18 | Tasks 1–3 | Eval 8 stop-state evidence |
| R19 | Tasks 1–3 | Eval 9 failed-validation, active-Plan, and no-archive evidence |
| R20, D1 | Tasks 2–3 | Eval transcripts show semantic updates and no timer/branch workflow |
| R21, D9–D12 | Tasks 1 and 3 | Persistent eval validation, paired runs, grading, benchmark, viewer, feedback, cleanup |

## Final Validation

- [ ] `jq -e '.skill_name == "implement" and ([.evals[].id] == [1,2,3,4,5,6,7,8,9]) and all(.evals[]; (.expectations | length) > 0)' config/.agents/skills/implement/evals/evals.json` — Expected: `true`; persistent eval contract is complete.
- [ ] `uv run --with pyyaml python -c 'import pathlib,yaml; p=pathlib.Path("config/.agents/skills/implement/SKILL.md"); t=p.read_text(); fm=yaml.safe_load(t.split("---",2)[1]); assert fm["name"]=="implement" and fm["disable-model-invocation"] is True; assert len(t.splitlines())<500'` — Expected: exit 0; Skill metadata and size remain valid.
- [ ] `git diff --check -- config/.agents/skills/implement docs/plans/2026-08-26-implement-review-convergence.md docs/plans/archived/2026-08-26-implement-review-convergence.md` — Expected: no whitespace errors.
- [ ] Inspect the final Skill against every row of **Normal delivery state machine**, **Review finding disposition**, and **Validation validity** — Expected: no missing or contradictory transition.
- [ ] Inspect `config/.agents/skills/commit-push/SKILL.md`, `config/.agents/skills/plan/SKILL.md`, and the installed `tdd/SKILL.md` against the final Skill — Expected: commit-only/final-push routing, Plan-owned contracts, and task-review-stage refactoring remain compatible without modifying those skills.
- [ ] Run all nine old/new Skill Creator eval pairs (including both isolated Eval 5 branches), grade every assertion, correct benchmark sample metadata, aggregate the final benchmark, perform the analyst pass, and generate the official static eval viewer — Expected: all new-skill assertions pass; both Eval 5 branch outputs are present; old-skill behavior, timing, and token comparisons are visible; `runs_per_configuration` equals `1`.
- [ ] User reviews the final eval viewer and benchmark — Expected: feedback is empty/approved, or accepted changes are incorporated and re-evaluated in a later iteration.
- [ ] Record Task 3's final iteration, new/old pass rates, timing/token summary, analyzer observations, feedback disposition, and temporary evidence paths in this Plan — Expected: the independent reviewer can verify the eval claim without relying on transient conversation context.
- [ ] Compare paths changed since the implementation base — Expected: only `config/.agents/skills/implement/SKILL.md`, `config/.agents/skills/implement/evals/`, and this Plan/archive path are implementation-owned; the three pre-existing settings changes remain untouched. The marker-owned `implement-workspace/` is a temporary review-evidence exception, never a commit candidate.
- [ ] Requirement Coverage has no unmatched item.
- [ ] Plan progress, actual changed files, validation reuse decisions, eval summary, review gate summary, and final commit mapping agree.
- [ ] One read-only independent reviewer inspects the implementation diff and marker-owned eval evidence and reports no unresolved supported blocking/high finding, using the evidence and scope contract in this Plan.
- [ ] If independent review changes the Skill or persistent eval assets, run affected static checks and a new paired Skill Creator iteration, update Task 3's result, and return to scoped re-review within the global correction budget — Expected: review, validation, and eval evidence describe the same implementation HEAD.
- [ ] The reviewed implementation HEAD and final valid validation/eval HEAD are identical; only marker-owned workspace cleanup, the gate summary, and Plan archive administrative commit follow them.
- [ ] `test -f config/.agents/skills/implement-workspace/.implement-eval-owned && test "$(realpath config/.agents/skills/implement-workspace)" = "$PWD/config/.agents/skills/implement-workspace"` — Expected: exit 0 before deleting only the reviewed implementation-owned temporary workspace.
- [ ] After independent review and any correction/eval reruns pass, remove only the marker-owned `config/.agents/skills/implement-workspace/`, then run `test ! -e config/.agents/skills/implement-workspace` — Expected: no temporary snapshot, transcript, timing, grading, benchmark, viewer, or feedback artifact remains.
- [ ] `git status --short`, `git diff --cached`, and `git diff` show no implementation-owned residue beyond the recorded pre-existing settings changes.
- [ ] After every preceding item succeeds, record the minimal review gate summary, move this Plan without renaming to `docs/plans/archived/2026-08-26-implement-review-convergence.md`, create its separate local archive commit, and push the entire implementation/correction/archive stack once.

## Risks and Open Questions

- Skill Creator executor/reviewer availability may vary by runtime. The fixture contract must expose any parent-harness reviewer injection rather than presenting it as nested reviewer behavior.
- End-to-end agent runs are nondeterministic. Decision-point fixtures and filesystem/Git assertions carry the hard safety signal; timing and token data remain descriptive.
- The existing `commit-push` skill runs documentation update logic during commit preparation. If archive preparation produces any substantive non-Plan change, it is not administrative residue: return it through validation and scoped review before delivery rather than including it silently in the archive commit.
- This self-hosting change intentionally follows the target deferred-push workflow before the installed Skill has been updated. The Plan header and D8 are the explicit user-approved override; without that approval, the old skill would reproduce the behavior being removed.
- No unresolved product or workflow decision remains.

## Gate Summary

- Review base: `b196f46`. Reviewed range: the simplification commits following it (Skill rewrite, eval reduction, commit-push invocation-policy alignment).
- Independent review: the user reviewed the rewritten Skill directly after the original reviewer and its single replacement became unavailable; no automated reviewer was started for the simplification. This departs from the Skill's own gate and is recorded here rather than claimed otherwise.
- Regression check (1 run each, rewritten Skill only): Eval 1 — two task commits, one archive commit, `push.log` shows exactly one ref update from fixture base to the archive commit, remote untouched before review. Eval 2 — no third correction cycle; both Highs escalated with evidence and options; approved contract change leads to spec update, full review, fresh two-cycle budget. All 9 expectations passed.
- Out-of-scope deviation: `commit-push/SKILL.md` was edited to state that `implement` references are commit-only, because it previously said the opposite and contradicted both the old and new `implement`.
- Unresolved `blocking/high`: none. Correction cycles used: 0.
