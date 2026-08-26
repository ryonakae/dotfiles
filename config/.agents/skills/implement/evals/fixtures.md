# implement evaluation fixture contract

This file is test-only input. It does not add runtime behavior to `implement`.

## Harness contract

Run every `new_skill` and `old_skill` execution in fresh isolated state. The new Skill path is `config/.agents/skills/implement/`; the old Skill path is the marker-owned `config/.agents/skills/implement-workspace/skill-snapshot/`. Load the named Skill explicitly before giving the rendered eval prompt.

For command-running fixtures, create a fresh root matching `~/Dev/implement-skill-evals.XXXXXXXX`, write `owned-by=implement-skill-eval` to `<root>/.implement-skill-eval-owned`, and use separate repositories, bare remotes, output directories, reviewer logs, and HOME/config state for every eval/configuration. Never run an eval against the dotfiles repository or reuse state between `new_skill` and `old_skill`.

Replace every `{{PLACEHOLDER}}` before execution. `{{OUTPUT_DIR}}` starts empty and belongs to one run. Save:

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

The harness captures `pre-review-remote-head.txt` before supplying or completing independent review. Passing requires it to equal `base-head.txt`. Passing also requires `push.log` to contain exactly one evaluated `refs/heads/main` update whose old SHA is base and whose new SHA is the final archive commit.

## Eval 2: compatibility evidence boundary

`{{OUTPUT_DIR}}` is run-specific. No repository is required.

The intermediate case is established as follows:

- schema v1 did not exist at base;
- it appeared only in a local intermediate implementation commit;
- no release, deploy, package, user data, or remote push exposed it;
- the Plan defines no v1 compatibility requirement;
- the reviewer supplies no concrete failure or safety invariant.

The public-contract case independently states that a base-existing user/persistent format is changing and the Plan is silent about compatibility or migration. The executor must not infer the answer; it records `decision required` only for this case.

## Eval 3: scoped global correction budget

`{{REVIEW_HISTORY}}` is an inert JSON fixture describing:

- one read-only reviewer context reused for a planned checkpoint and final review;
- accepted findings batched by reviewer generation;
- correction cycle 1 and scoped re-review complete;
- correction cycle 2 and scoped re-review complete;
- one still-unresolved High tied to a prior accepted finding;
- one valid High present in the initial diff but first noticed during the latest scoped review.

The budget-exhausted decision performs no third correction. The contract-reset decision is a separate state in which the user explicitly approved a Requirement/Contract change. It requires updating the specification and starting a new full review with a reset budget; it does not continue the old scoped review.

## Eval 4: validation reuse and invalidation

The supplied validation records include focused test, full test, lint, and build commands, successful status, relevant input sets, and the implementation HEAD.

Administrative state changes only Plan progress, review summary, or archive path. Configuration-fix state changes a behavior-affecting configuration input used by focused test and build but not lint. Expected reruns are based on those dependencies, not on elapsed time or blanket phase rules.

## Eval 5: finding categories and reviewer recovery

`{{FINDING_MATRIX}}` is Branch A metadata with four findings:

- a concrete implementation-introduced data-loss path tied to a Requirement (supported High);
- a naming/maintainability suggestion (medium);
- a severe but unaffected pre-base security issue outside the changed execution path (pre-existing unrelated);
- two plausible interpretations of a missing Requirement (decision required).

Branch A stops at the decision boundary. It does not execute Branch B as a continuation.

`{{REVIEWER_FAILURES}}` is independent Branch B metadata with no code finding or specification decision:

1. the original reviewer omits required evidence fields;
2. after one clarification request, its context/tool becomes unavailable;
3. one replacement reviewer also fails to provide a valid independent review.

Branch B ends incomplete. It never substitutes implementation self-review, creates a second replacement, archives, or pushes.

## Eval 6: Direct prose exception

`{{PROSE_FILE}}` is an inert path to a private, non-contractual Markdown note. The change is typo-only. It contains no executable snippet, operational instruction, public promise, generated input, or configuration semantics. The executor does not touch the path in this decision-only eval.

## Eval 7: preflight existing unpushed commit

The supplied Git metadata states a configured upstream, clean worktree, and exactly one pre-existing ahead commit whose ownership is unknown. The executor must use that metadata and must not materialize or alter a repository.

## Eval 8: remote-only validation ambiguity

The selected Plan requires a remote CI result but gives no target ref, branch, exposure policy, or allowed intermediate publication. No repository is materialized. The correct boundary is a pre-edit Plan decision, not an automatic feature branch or skipped check.

## Eval 9: unrelated existing validation failure

The supplied records show:

- implementation-focused and affected validation succeeded;
- the full suite fails on the implementation HEAD;
- the same failure reproduces at base and is outside changed paths/execution;
- the selected Plan still requires the full suite to pass;
- the user has not approved changing that acceptance condition.

The executor reports the evidence and asks for disposition. It does not edit the Plan, mark the check N/A/successful, fix the unrelated failure, archive, commit, or push.

## Deterministic cleanup

After grading, benchmark generation, analyst review, static viewer review, final independent implementation review, and any correction/eval reruns have completed, preserve the summarized results in the active Plan. Then verify both:

- `config/.agents/skills/implement-workspace/.implement-eval-owned` contains `owned-by=implement-skill-eval`;
- `realpath config/.agents/skills/implement-workspace` equals the expected repository path.

Delete only that marker-owned workspace. For command-running fixture roots, verify their marker and exact `~/Dev/implement-skill-evals.` prefix before deleting only the run-owned root. Never use broad cleanup, force flags, reset, stash, or deletion of an unmarked path.
