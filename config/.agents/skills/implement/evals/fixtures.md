# implement evaluation fixture contract

This file is test-only input. It does not add runtime behavior to `implement`.

## Harness contract

Run each eval in a fresh directory outside the dotfiles repository. Give the executor only the runtime `SKILL.md` (plus `commit-push` and `tdd` if referenced), the rendered task, and the fixture inputs below. Do not expose this file, `evals.json`, prior outputs, or grading. Replace every `{{PLACEHOLDER}}` before execution. Save the full transcript alongside `{{OUTPUT_DIR}}`.

Reviewers are read-only and separate from the implementation executor. If nested delegation is unavailable, the harness may pause at the review-ready state, run one read-only reviewer with the Plan, base-to-HEAD diff, commit list, and validation results, then resume the executor with that result. Record the boundary; do not claim a nested reviewer was launched.

## Eval 1: Plan happy path and single publication

`{{FIXTURE_REPO}}` is a fresh Git repository on `main` with a local test identity. `{{ACTIVE_PLAN}}` is `docs/plans/2026-08-26-fixture-change.md`. `{{OUTPUT_DIR}}` is outside the repository.

Create a bare remote configured as `origin`, with a `post-receive` hook appending `old-sha new-sha ref` to a harness-owned `push.log` on every ref update. Push only the initial base before starting the executor, then truncate `push.log`.

Initial tracked files:

- `values.txt` containing `base=1`;
- `tests/check-values.sh`, executable, requiring exactly one `alpha=1` line and one `beta=2` line in `values.txt`, exiting nonzero otherwise;
- `scripts/full-check.sh`, executable, running `tests/check-values.sh` plus `git diff --check`;
- the active Plan.

The Plan defines two tasks: (1) append `alpha=1`, verify with a focused shell command, self-review, commit; (2) append `beta=2`, run `tests/check-values.sh`, self-review, commit. Final Validation runs `scripts/full-check.sh`, requires one read-only independent review, and archives the Plan without renaming. The Plan says nothing about publication timing; the Skill alone decides whether commits are pushed before or after review.

Harness captures into `{{OUTPUT_DIR}}`: `base-head.txt`, `pre-review-remote-head.txt` (taken before review is supplied), `final-remote-head.txt`, `commit-list.txt`, `push.log`. The executor saves `validation.json`, `review.json`, and `final-report.md`.

## Eval 2: correction budget exhausted

`{{REVIEW_HISTORY}}` is an inert JSON fixture describing:

- one read-only reviewer context reused for the final review and both scoped re-reviews;
- correction cycle 1 and scoped re-review complete;
- correction cycle 2 and scoped re-review complete;
- one still-unresolved High tied to a prior accepted finding;
- one valid High present in the initial diff but first noticed during the latest scoped review.

A separate state records explicit user approval to change a Requirement/Contract after the history above. The fixture records no action or review-scope decision for either state. Decision files contain at least `status`, `actions`, `forbidden_actions`, `reason`.

## Cleanup

Delete only the harness-created fixture directories. Never run cleanup against the dotfiles repository.
