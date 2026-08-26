# implement evaluation fixture contract

This file is test-only input. It does not add runtime behavior to `implement`.

## Harness contract

Run every `new_skill` and `old_skill` execution in a fresh sealed bundle under a root matching `~/Dev/implement-skill-evals.XXXXXXXX`. Write `owned-by=implement-skill-eval` to `<root>/.implement-skill-eval-owned`. Each run bundle contains only the selected runtime `SKILL.md`, runtime files needed by its explicit references, rendered task, fact-only fixture input, a pre-run file-hash manifest, and an empty output directory. Copy runtime files from an allowlist; never copy a Skill directory recursively. Do not include any `evals/` path, eval definition, expected output, assertion, grading file, benchmark, previous output, sibling run, or dotfiles-workspace path.

Before execution, enumerate every bundle file into `bundle-manifest.json` and reject the run if a path or non-task input contains evaluation assets or oracle keys. The executor may read and write only paths inside its named run bundle. Any read, search, listing, or command that inspects a sibling bundle, the dotfiles repository, Skill Creator workspace, previous output, grading, benchmark, or assertion fails the isolation expectation even if the decision is otherwise correct. Capture the complete transcript, verify the immutable pre-run manifest, and audit path access before grading.

For command-running fixtures, use separate repositories, bare remotes, output directories, reviewer logs, and HOME/config state for every eval/configuration. Never run an eval against the dotfiles repository or reuse state between `new_skill` and `old_skill`.

Replace every `{{PLACEHOLDER}}` before execution. `{{RUN_BUNDLE}}` identifies the allowed root, and `{{OUTPUT_DIR}}` starts empty inside it. Save:

- `transcript.md` — complete executor messages and tool calls;
- `outputs/` — every requested decision/state file;
- `outputs/metrics.json` — tool-call and output metrics when available;
- sibling `timing.json` — tokens and duration from the completion notification.

Decision-point evals do not edit source repositories, create commits, invoke reviewers, or push. They receive established fixture facts and save the next-action decision as JSON. A decision file contains at least `status`, `category`, `actions`, `forbidden_actions`, `reason`, and `evidence`. Assertions grade the decision and any observed tool calls, not keyword presence alone.

For Eval 5, one executor run must evaluate two isolated in-memory/fixture branches and create both:

- `{{OUTPUT_DIR}}/branch-a/decision.json`
- `{{OUTPUT_DIR}}/branch-b/decision.json`

The harness and grader fail the eval if either file is absent or if one branch merely quotes the expected policy without addressing its supplied state.

## Reviewer boundary

Reviewers are read-only and separate from implementation executors. When an executor runtime supports nested reviewer delegation, record the reviewer handle/context and full reviewer result in the transcript. If nested delegation is unavailable for Eval 1, the parent harness may pause at the review-ready state, run one read-only reviewer with the selected Plan, base-to-HEAD diff, commit list, and validation results, then resume the same executor with that exact result. Record this parent boundary explicitly; do not claim the executor launched a nested reviewer.

Decision-point reviewer histories are inert supplied metadata. Do not actually launch reviewers in Evals 2–9.

## Eval 1: Plan happy path and single publication

`{{FIXTURE_REPO}}` is a fresh Git repository on `main`. Configure a local test identity. `{{ACTIVE_PLAN}}` is `docs/plans/2026-08-26-fixture-change.md`. `{{OUTPUT_DIR}}` is outside the repository but inside the owned fixture root.

Create a bare remote and configure it as `origin`. Enable a bare-repository `post-receive` hook that appends one line containing old SHA, new SHA, and ref to a fixture-owned `push.log` for every successful ref update. Push only the initial base before starting the executor, then truncate `push.log` so it records evaluated publication only.

Initial tracked files:

- `values.txt` containing `base=1`;
- `tests/check-values.sh`, executable, requiring exactly one `alpha=1` line and one `beta=2` line and exiting nonzero otherwise;
- `scripts/full-check.sh`, executable, running `tests/check-values.sh` plus `git diff --check`;
- the active Plan below.

The Plan defines two reviewable tasks:

1. append `alpha=1`, test the alpha behavior with a focused shell command, self-review, and commit;
2. append `beta=2`, run `tests/check-values.sh`, self-review, and commit.

Final Validation runs `scripts/full-check.sh`, verifies Requirement Coverage, requires one read-only independent review, and archives the Plan without renaming. The fixture Plan does not define publication timing; the loaded Skill alone determines whether deliverable commits are pushed before or after review. The fixture contains no remote-only validation and no unrelated worktree changes.

The executor saves or the harness derives into `{{OUTPUT_DIR}}/outputs/`:

- `base-head.txt`, `pre-review-local-head.txt`, `pre-review-remote-head.txt`, and `final-remote-head.txt`;
- `commit-list.txt`;
- `push.log` copied from the bare remote;
- `validation.json` with command, status, HEAD, and reuse decisions;
- `review.json` with reviewer identity/context, scope, findings, and read-only evidence;
- `final-status.txt` and `final-report.md`.

The harness captures `pre-review-remote-head.txt` before supplying or completing independent review. The executor fixture contains the Git facts and output paths only; publication assertions remain harness-side.

## Eval 2: compatibility evidence boundary

`{{OUTPUT_DIR}}` is run-specific. No repository is required.

The intermediate case is established as follows:

- schema v1 did not exist at base;
- it appeared only in a local intermediate implementation commit;
- no release, deploy, package, user data, or remote push exposed it;
- the Plan defines no v1 compatibility requirement;
- the reviewer supplies no concrete failure or safety invariant.

The public-contract case independently states that a base-existing user/persistent format is changing and the Plan is silent about compatibility or migration.

## Eval 3: scoped global correction budget

`{{REVIEW_HISTORY}}` is an inert JSON fixture describing:

- one read-only reviewer context reused for a planned checkpoint and final review;
- accepted findings batched by reviewer generation;
- correction cycle 1 and scoped re-review complete;
- correction cycle 2 and scoped re-review complete;
- one still-unresolved High tied to a prior accepted finding;
- one valid High present in the initial diff but first noticed during the latest scoped review.

A separate contract-change state records explicit user approval to change a Requirement/Contract after the history above. The fixture records no action or review-scope decision for either state.

## Eval 4: validation reuse and invalidation

The supplied validation records include focused test, full test, lint, and build commands, successful status, relevant input sets, and the implementation HEAD.

Administrative state changes only Plan progress, review summary, or archive path. Configuration-fix state changes a behavior-affecting configuration input used by focused test and build but not lint. The fixture records command inputs and state changes without prescribing reruns, review scope, commit handling, or cycle accounting.

## Eval 5: finding categories and reviewer recovery

`{{FINDING_MATRIX}}` is Branch A metadata with four records:

- the implementation writes an empty replacement before copying the old value, causing data loss on an error path covered by Requirement R4;
- a reviewer prefers a shorter local variable name but identifies no behavior or contract impact;
- a credential exposure predates base, lies outside changed paths and execution, and is neither worsened nor depended on by the implementation;
- the Plan omits whether an ambiguous input should be rejected or normalized, and either interpretation would change observable behavior.

`{{REVIEWER_FAILURES}}` is independent Branch B metadata with no code finding or specification decision. It records an original review missing required evidence fields, failure of that reviewer context/tool after one follow-up exchange, and an invalid result from one separate replacement reviewer. The fixture does not prescribe the next action for either branch.

## Eval 6: Direct prose exception

`{{PROSE_FILE}}` is an inert path to a private, non-contractual Markdown note. The change is typo-only. It contains no executable snippet, operational instruction, public promise, generated input, or configuration semantics. The executor does not touch the path in this decision-only eval.

## Eval 7: preflight existing unpushed commit

The supplied Git metadata states a configured upstream, clean worktree, and exactly one pre-existing ahead commit whose ownership is unknown. The executor must use that metadata and must not materialize or alter a repository.

## Eval 8: remote-only validation ambiguity

The selected Plan requires a remote CI result but gives no target ref, branch, exposure policy, or allowed intermediate publication. No repository is materialized.

## Eval 9: unrelated existing validation failure

The supplied records show:

- implementation-focused and affected validation succeeded;
- the full suite fails on the implementation HEAD;
- the same failure reproduces at base and is outside changed paths/execution;
- the selected Plan still requires the full suite to pass;
- the user has not approved changing that acceptance condition.

The fixture supplies no disposition for the failed acceptance item.

## Deterministic cleanup

After grading, benchmark generation, analyst review, static viewer review, final independent implementation review, and any correction/eval reruns have completed, preserve the summarized results in the active Plan. Then verify both:

- `config/.agents/skills/implement-workspace/.implement-eval-owned` contains `owned-by=implement-skill-eval`;
- `realpath config/.agents/skills/implement-workspace` equals the expected repository path.

Delete only that marker-owned workspace. For command-running fixture roots, verify their marker and exact `~/Dev/implement-skill-evals.` prefix before deleting only the run-owned root. Never use broad cleanup, force flags, reset, stash, or deletion of an unmarked path.
