# use-worktrunk Environment Adapter Implementation Plan

> **Status:** Implemented and reviewed. This file preserves the initial plan and is not the current execution procedure. Review findings expanded the evaluation suite from four cases to eight and replaced per-directory copy exclusions with a fail-closed exact-file allowlist. Use `config/.agents/skills/use-worktrunk/SKILL.md`, `evals/evals.json`, and `evals/fixtures.md` as the final contract.

**Goal:** Add a thin `use-worktrunk` Agent Skill and Worktrunk user configuration so agents can use the official Worktrunk workflow without getting blocked by this dotfiles environment's Agent Safehouse boundaries.

**Architecture:** The official external `worktrunk` Skill remains the sole Worktrunk command and configuration reference. The custom `use-worktrunk` Skill is an instruction-only environment adapter: it loads the official Skill before operations, reads the dotfiles-managed Safehouse policy only when paths, ignored-file copies, or sandbox errors are relevant, and explains the non-persistent cwd behavior of agent tool sessions. A project-specific Worktrunk user setting keeps only the dotfiles repository's linked worktrees inside the existing `~/Dev` Safehouse grant.

**Tech Stack:** Agent Skills standard Markdown, Worktrunk v0.73.0, TOML, Agent Safehouse Seatbelt policy, fish, `npx skills`, jq, Skill Creator evaluation tooling.

## Global Constraints

- Name the custom Skill `use-worktrunk`.
- Keep the Skill instruction-only. Do not add helper scripts, registries, or state files.
- Before any actual Worktrunk operation, read `~/.agents/skills/worktrunk/SKILL.md`. If it is missing, stop and recommend `cd ~ && npx skills experimental_install`; do not reconstruct the official documentation.
- Use the official Skill and Worktrunk defaults for creation, switching, hooks, copy, merge, removal, and prune. Add behavior-changing flags only when the user explicitly requests them or this environment requires them.
- Do not duplicate the Safehouse allowlist or denied filename patterns in the custom Skill. Read these canonical files only when relevant:
  - `~/dotfiles/config/.config/fish/functions/__safehouse_args.fish`
  - `~/dotfiles/config/.config/agent-safehouse/local-overrides.sb`
- Load `use-agent-safehouse` only to diagnose or change Safehouse behavior, such as after `Operation not permitted`; do not load it for routine Worktrunk operations.
- Never directly probe, read, copy, create, edit, or remove paths denied by `local-overrides.sb`, including matching `.env*`, `.envrc`, credential, secret, and private-key paths. The agent may read safe policy and `.worktreeinclude` text to derive exclusion patterns. Before a real `copy-ignored`, use JSON dry-runs to exclude both denied names and every entry Worktrunk reports as `kind: dir`; only exact file entries may be copied inside Agent Safehouse. If discovery is refused, stop without retrying or widening Safehouse. Report denied or recursive entries without reading their contents and provide a normal-shell action when required.
- Keep Safehouse policy unchanged for Worktrunk placement. Resolve an out-of-grant worktree path through Worktrunk user configuration, with user consent.
- When an agent tool session invokes `wt switch`, preserve Worktrunk behavior except for `--no-cd --format=json`; the shell integration cannot reliably retarget the parent agent session.
- After creating or selecting a worktree from an existing agent session, report the absolute path and stop before implementation. The user starts a new agent session from that worktree.
- Do not infer dependency setup or baseline tests when project hooks are absent. Let configured Worktrunk hooks run normally; handle separately requested setup or tests as ordinary development tasks.
- Trigger the custom Skill for actual Worktrunk operations and environment-specific failures, not for a general Worktrunk question that the official Skill alone answers.
- Preserve the existing uncommitted changes in `brew/Brewfile.example`, `config/.claude/settings.json`, `config/.pi/agent/settings.json`, `config/skills-lock.json`, and the Worktrunk fish integration files. Do not revert or rewrite unrelated edits.
- Do not use `--yes` to bypass Worktrunk approvals. Follow the official Skill's approval workflow.
- Do not use destructive or force options unless the user explicitly requests and approves them.

## Current Context

- Worktrunk v0.73.0 is installed at `/opt/homebrew/bin/wt`.
- The official `max-sixty/worktrunk` `worktrunk` Skill is installed at `~/.agents/skills/worktrunk` and recorded in `config/skills-lock.json`.
- `wt-switch-create` is intentionally not installed.
- `wt config show --format=json` reports no current user or project Worktrunk config and identifies this repository as `github.com/ryonakae/dotfiles`.
- Agent wrappers grant read/write access to `~/dotfiles` and `~/Dev`, but Worktrunk's default sibling path for `~/dotfiles` would be under `$HOME` and outside those explicit grants.
- `local-overrides.sb` applies final filename-based deny rules even inside otherwise writable worktrees.
- Worktrunk shell integration is managed at `config/.config/fish/functions/wt.fish` and `config/.config/fish/completions/wt.fish`.
- Pi loads `~/.agents/skills` directly. Claude Code receives explicit symlinks; Codex and OpenCode recognize the universal `~/.agents/skills` location.

## File Structure

- Create: `config/.config/worktrunk/config.toml` — personal Worktrunk path override for the dotfiles repository.
- Create: `config/.agents/skills/use-worktrunk/SKILL.md` — thin Safehouse environment adapter that delegates Worktrunk semantics to the official Skill.
- Create: `config/.agents/skills/use-worktrunk/evals/evals.json` — realistic Skill Creator evaluation prompts; no runtime logic.
- Temporary: `config/.agents/skills/use-worktrunk-workspace/` — Skill Creator run output with an ownership marker, removed after review and refinement.
- Temporary: a unique `~/Dev/use-worktrunk-evals.XXXXXXXX/` root whose exact path is recorded in the workspace — isolated repositories and worktrees, removed only after ownership checks.
- No change: `config/skills-lock.json` — the custom Skill is dotfiles-managed, not an external `npx skills` package.
- No change: `README.md` — the existing custom/external Skill distribution documentation already covers this layout.

## Tasks

### Task 1: Keep dotfiles Worktrunk paths inside the existing Safehouse grant

**Objective:** Configure only `github.com/ryonakae/dotfiles` to place linked worktrees under `~/Dev/.worktrees/dotfiles/`, leaving every other repository on Worktrunk defaults.

**Files:**
- Create: `config/.config/worktrunk/config.toml`

**Interfaces:**
- Consumes: Worktrunk project identifier `github.com/ryonakae/dotfiles` and the existing `~/Dev` Safehouse grant.
- Produces: A dotfiles-managed user configuration loaded from `~/.config/worktrunk/config.toml`.

- [ ] **Step 1: Confirm the setting is absent**

Run:

```bash
test -f config/.config/worktrunk/config.toml && \
  rg -n 'github\.com/ryonakae/dotfiles|worktree-path' config/.config/worktrunk/config.toml
```

Expected: non-zero exit because the config file does not exist yet.

- [ ] **Step 2: Create the minimal user config**

Create `config/.config/worktrunk/config.toml` with exactly:

```toml
[projects."github.com/ryonakae/dotfiles"]
worktree-path = "~/Dev/.worktrees/dotfiles/{{ branch | sanitize }}"
```

Do not add global Worktrunk preferences or command defaults.

- [ ] **Step 3: Deploy through the repository's normal symlink mechanism**

Run:

```bash
sh scripts/create-symlink.sh
```

Expected: `~/.config/worktrunk/config.toml` is created as a symlink to `config/.config/worktrunk/config.toml`; existing managed files are reported as skipped rather than overwritten.

- [ ] **Step 4: Validate Worktrunk's merged configuration**

Run:

```bash
test "$(realpath "$HOME/.config/worktrunk/config.toml")" = \
  "$PWD/config/.config/worktrunk/config.toml"
wt config show --format=json | jq -e '
  .project.identifier == "github.com/ryonakae/dotfiles" and
  .user.exists == true and
  .user.config.projects["github.com/ryonakae/dotfiles"]["worktree-path"] ==
    "~/Dev/.worktrees/dotfiles/{{ branch | sanitize }}"
'
```

Expected: both commands exit 0.

### Task 2: Define the evaluation contract before writing the Skill

**Objective:** Record realistic prompts that distinguish the Safehouse adapter from the official Worktrunk guidance without turning the custom Skill into a second command manual.

**Files:**
- Create: `config/.agents/skills/use-worktrunk/evals/evals.json`

**Interfaces:**
- Consumes: The decisions in Global Constraints.
- Produces: Four integer-ID evaluation cases used by Task 4.

- [ ] **Step 1: Confirm the eval specification is absent**

Run:

```bash
test -f config/.agents/skills/use-worktrunk/evals/evals.json
```

Expected: exit 1.

- [ ] **Step 2: Create prompts without assertions**

Create valid JSON with `skill_name` set to `use-worktrunk` and the following cases. Use the exact integer IDs and names in this plan when creating workspace directories later.

1. ID `1`, `agent-session-create`: given a concrete fixture repository and branch, ask the agent to create the Worktrunk worktree, return the destination, and do no implementation.
2. ID `2`, `mixed-ignored-copy`: given a fixture whose tracked `.worktreeinclude` names `.env`, `.envrc`, two exact ignored files, `node_modules/`, and `.cache/`, ask the agent to copy what is safe after a reported prior `.env` refusal. The expected result is an initial policy-excluded dry-run, exclusion of every recursive directory reported by that plan, a final file-only dry-run, copying of only the two exact files, no denied-path probe, and normal-shell guidance for denied and recursive entries.
3. ID `3`, `outside-safehouse-path`: provide a proposed Worktrunk path under `$HOME` but outside the grants in the canonical policy files. Ask the agent to resolve it without running the failing create, modifying Safehouse, or changing Worktrunk user config without consent.
4. ID `4`, `official-only-question`: ask when Worktrunk `pre-start` should be used instead of `post-start`. The expected result is normal official guidance with no unrelated Safehouse or agent-cwd policy.

Each case must include a concrete `expected_output` and an empty `files` array. Do not add assertions yet; Skill Creator requires drafting them while execution runs are in progress.

- [ ] **Step 3: Validate the eval schema basics**

Run:

```bash
jq -e '
  .skill_name == "use-worktrunk" and
  (.evals | length) == 4 and
  ([.evals[].id] == [1, 2, 3, 4]) and
  ([.evals[].id] | unique | length) == 4 and
  all(.evals[]; (.prompt | length) > 80 and (.expected_output | length) > 40)
' config/.agents/skills/use-worktrunk/evals/evals.json
```

Expected: exit 0 and no output.

### Task 3: Create the instruction-only environment adapter

**Objective:** Make Worktrunk operations load official guidance first, then apply only the environment-specific checks that prevent predictable Safehouse and agent-session failures.

**Files:**
- Create: `config/.agents/skills/use-worktrunk/SKILL.md`

**Interfaces:**
- Consumes: `~/.agents/skills/worktrunk/SKILL.md`, the two canonical Safehouse files, and Worktrunk's JSON output.
- Produces: Agent Skills metadata and a short operational decision flow.

- [ ] **Step 1: Write the Skill frontmatter**

Use:

```yaml
---
name: use-worktrunk
description: Worktrunkをこのdotfiles管理のAgent Safehouse環境で安全に操作するための環境アダプター。worktreeの作成、切替、ignoredファイルのコピー、削除、merge、pruneなど、エージェントが`wt`で実際にworktreeを操作するときは必ず使い、公式`worktrunk` Skillも読み込む。一般的なWorktrunkの仕様質問だけなら公式Skillを使う。
compatibility: Requires Worktrunk, the official worktrunk Skill, and this dotfiles repository's Agent Safehouse configuration.
---
```

- [ ] **Step 2: Write the complete decision flow**

Keep `SKILL.md` below 200 lines and include these sections:

1. **Role** — State that this Skill supplements rather than replaces official Worktrunk guidance.
2. **Load the official Skill** — Read `~/.agents/skills/worktrunk/SKILL.md` before any `wt` operation; if absent, stop and print exactly `cd ~ && npx skills experimental_install`.
3. **Use Worktrunk defaults** — Follow the official Skill and current `wt <command> --help`; do not redefine creation, hooks, merge, remove, or prune behavior; honor explicit user overrides.
4. **Check the environment only when relevant** — Read `__safehouse_args.fish` for destination grants and `local-overrides.sb` for denied names before path-sensitive creation/relocation or ignored-file copy. Do not copy those values into the Skill.
5. **Agent-session switching** — For agent-issued `wt switch`, retain the user's arguments and add `--no-cd --format=json`. Save or inspect the raw JSON, require the returned worktree path to be absolute, report it, and stop before implementation. Tell the user to start a new agent session from that path.
6. **Ignored files and secrets** — Read only safe config/pattern text. Derive invocation-scoped `step.copy-ignored.exclude` entries for denied names selected by `.worktreeinclude`. Run an initial `wt step copy-ignored --dry-run --format=json`; if it succeeds, add every returned `kind: dir` path to the excludes because Worktrunk recursively copies directory entries and descendant deny matches are hidden from the plan. Run a second JSON dry-run and require every remaining entry to be `kind: file` and not denied before running the real copy with identical excludes. If either discovery run produces `Operation not permitted`, stop; do not retry or probe the refused path. Give the user a normal-shell command for denied and recursive entries without weakening Safehouse. This restriction applies only inside Agent Safehouse; normal-shell users retain standard Worktrunk behavior.
7. **Sandbox refusal** — On `Operation not permitted`, do not retry with force or widen policy. Load `use-agent-safehouse`, identify the denied operation/path from the command error and policy text, and report it. Change Worktrunk config or Safehouse only after explicit user consent.
8. **Report** — State the Worktrunk result, absolute worktree path when applicable, any manual normal-shell action, and whether a new agent session is required.

Do not include generic Worktrunk examples already maintained by the official Skill. Do not prescribe setup or baseline testing when hooks are absent.

- [ ] **Step 3: Validate Agent Skills structure and scope**

Run:

```bash
test "$(find config/.agents/skills/use-worktrunk -type f -path '*/scripts/*' | wc -l | tr -d ' ')" = 0
test "$(wc -l < config/.agents/skills/use-worktrunk/SKILL.md | tr -d ' ')" -lt 200
rg -n '^name: use-worktrunk$|~/.agents/skills/worktrunk/SKILL.md|npx skills experimental_install|__safehouse_args\.fish|local-overrides\.sb|--no-cd|--format=json|--dry-run|Operation not permitted' \
  config/.agents/skills/use-worktrunk/SKILL.md
```

Expected: no scripts, fewer than 200 lines, and every required contract marker is present.

### Task 4: Evaluate official-plus-adapter against an isolated official-only baseline

**Objective:** Verify that the adapter prevents environment-specific failures while preserving official Worktrunk behavior, before making the custom Skill globally discoverable.

**Files:**
- Temporary: `config/.agents/skills/use-worktrunk-workspace/iteration-1/`
- Modify: `config/.agents/skills/use-worktrunk/evals/evals.json` to add assertions after runs start.

**Interfaces:**
- Consumes: the Skill draft and four eval prompts.
- Produces: paired transcripts, outputs, timing data, grades, and `benchmark.json` in the exact layout expected by Skill Creator.

- [ ] **Step 1: Assert baseline isolation and create owned temporary roots**

The custom Skill must not be globally linked until Task 6. Run:

```bash
set -eu
test ! -e "$HOME/.agents/skills/use-worktrunk"
test ! -L "$HOME/.agents/skills/use-worktrunk"
WORKSPACE="$PWD/config/.agents/skills/use-worktrunk-workspace"
test ! -e "$WORKSPACE"
mkdir -p "$WORKSPACE/iteration-1"
printf '%s\n' 'owned-by=use-worktrunk-eval' > "$WORKSPACE/.use-worktrunk-workspace-owned"
EVAL_ROOT=$(mktemp -d "$HOME/Dev/use-worktrunk-evals.XXXXXXXX")
printf '%s\n' 'owned-by=use-worktrunk-eval' > "$EVAL_ROOT/.use-worktrunk-eval-owned"
printf '%s\n' "$EVAL_ROOT" > "$WORKSPACE/fixture-root.txt"
mkdir -p "$EVAL_ROOT/iteration-1"
```

Run this as one non-interactive shell command. `set -eu` makes every absence and ownership precondition fail-closed before `mkdir` or marker writes.

Expected: the custom Skill is absent from global discovery, and both roots contain ownership markers. If an existing `~/.agents/skills/use-worktrunk` is found, remove it only when it is a symlink resolving to this repository's new Skill; otherwise stop and ask the user.

- [ ] **Step 2: Create exact paired fixtures**

Create two `agent-session-create` repositories and two `mixed-ignored-copy` repositories under the recorded root. Run this complete block as one fail-closed command:

```bash
set -eu
WORKSPACE="$PWD/config/.agents/skills/use-worktrunk-workspace"
test "$(cat "$WORKSPACE/.use-worktrunk-workspace-owned")" = 'owned-by=use-worktrunk-eval'
EVAL_ROOT=$(cat "$WORKSPACE/fixture-root.txt")
case "$EVAL_ROOT" in
  "$HOME/Dev/use-worktrunk-evals."*) ;;
  *) echo "Unexpected eval root: $EVAL_ROOT" >&2; exit 1 ;;
esac
test "$(cat "$EVAL_ROOT/.use-worktrunk-eval-owned")" = 'owned-by=use-worktrunk-eval'
ITERATION_ROOT="$EVAL_ROOT/iteration-1"
test -d "$ITERATION_ROOT"

init_eval_repo() {
  repo=$1
  test ! -e "$repo"
  mkdir -p "$repo"
  git -C "$repo" init -q -b main
  git -C "$repo" config user.name 'use-worktrunk eval'
  git -C "$repo" config user.email 'use-worktrunk-eval@example.invalid'
  printf 'fixture\n' > "$repo/README.md"
  git -C "$repo" add README.md
  git -C "$repo" commit -qm init
}

init_eval_repo "$ITERATION_ROOT/create-with"
init_eval_repo "$ITERATION_ROOT/create-without"
init_eval_repo "$ITERATION_ROOT/copy-with"
init_eval_repo "$ITERATION_ROOT/copy-without"

for repo in "$ITERATION_ROOT/copy-with" "$ITERATION_ROOT/copy-without"; do
  cat > "$repo/.gitignore" <<'EOF'
.env
.envrc
build-cache.bin
generated-model.bin
node_modules/
.cache/
EOF
  cat > "$repo/.worktreeinclude" <<'EOF'
.env
.envrc
build-cache.bin
generated-model.bin
node_modules/
.cache/
EOF
  printf 'root-build-cache\n' > "$repo/build-cache.bin"
  printf 'root-generated-model\n' > "$repo/generated-model.bin"
  mkdir "$repo/node_modules" "$repo/.cache"
  printf 'package-cache\n' > "$repo/node_modules/package.txt"
  printf 'nested-build-cache\n' > "$repo/.cache/build.txt"
  git -C "$repo" add .gitignore .worktreeinclude
  git -C "$repo" commit -qm 'add copy fixture patterns'
  git -C "$repo" branch copy-target-i1
  git -C "$repo" worktree add -q "$repo.copy-target-i1" copy-target-i1
  test ! -e "$repo.copy-target-i1/build-cache.bin"
  test ! -e "$repo.copy-target-i1/generated-model.bin"
  test ! -e "$repo.copy-target-i1/node_modules"
  test ! -e "$repo.copy-target-i1/.cache"
done
```

Do not create `.env`, `.envrc`, credential, secret, or key fixtures. Expected: both worktree lists include `<repo>.copy-target-i1`, both exact root payloads exist only in the primary source, and all four destination checks are absent. The eval proves that exact root files can be copied while recursive directories are withheld from the agent-side real copy.

- [ ] **Step 3: Create exact workspace layout and metadata**

Create these directories for one run per configuration:

```text
iteration-1/
├── eval-agent-session-create/
│   ├── eval_metadata.json
│   ├── with_skill/
│   │   ├── eval_metadata.json
│   │   └── run-1/outputs/
│   └── without_skill/
│       ├── eval_metadata.json
│       └── run-1/outputs/
├── eval-mixed-ignored-copy/       # same metadata/config/run layout
├── eval-outside-safehouse-path/   # same metadata/config/run layout
└── eval-official-only-question/   # same metadata/config/run layout
```

The eval-level `eval_metadata.json` contains only the integer `eval_id`, stable `eval_name`, unresolved prompt template, and empty `assertions`; the aggregator reads it. Each configuration-level `eval_metadata.json` contains the same ID/name plus that configuration's exact resolved prompt and empty `assertions`; the viewer finds it through `run-1`'s parent directory. This avoids sharing a prompt between different fixture paths.

- [ ] **Step 4: Launch all eight runs in one turn**

Launch fresh, non-inheriting, isolated general agents in parallel. Do not use Agent worktree isolation.

- `with_skill`: explicitly require reading `config/.agents/skills/use-worktrunk/SKILL.md`; the Skill must then load the official Skill.
- `without_skill`: explicitly require reading only `~/.agents/skills/worktrunk/SKILL.md`. Because Task 6 has not run, `use-worktrunk` is unavailable from global Skill discovery. Assert later that its transcript did not load the custom path.

Require each executor to write `outputs/result.md` and `outputs/metrics.json`. Eval 1 also archives raw switch JSON at `outputs/worktrunk-switch.json`. Eval 2 archives the initial dry-run, file-only final dry-run, and real copy JSON separately as `outputs/copy-plan-initial.json`, `outputs/copy-plan-final.json`, and `outputs/copy-result.json`. Retrieve each completed agent with verbose conversation output and save that conversation as the run's `transcript.md`.

Use these operation inputs:

- Eval 1 branches: `eval-with-skill-i1` and `eval-without-skill-i1`. The with-Skill success trace includes `wt -C <repo> switch --create <branch> --no-cd --format=json`, valid raw JSON, an absolute path under the owned fixture root, no file edits in the new worktree, and a new-session instruction.
- Eval 2 targets: the pre-created `copy-target-i1` worktrees. The with-Skill success trace reads both canonical policy files; derives `.env` and `.envrc` excludes; archives an initial JSON dry-run; observes `node_modules` and `.cache` as directory entries and adds both to the invocation-scoped excludes; archives a second dry-run containing only `kind: file` entries; performs the real copy with identical excludes; verifies exact contents of `build-cache.bin` and `generated-model.bin` in the target; verifies both recursive directories remain absent; never creates or probes denied files; and gives a normal-shell instruction for denied and recursive entries.
- Eval 3: analysis only. It inspects current policy/config, proposes a Worktrunk path inside an existing grant, requests consent before changing user config, and never runs the known failing create or edits Safehouse.
- Eval 4: analysis only. It answers from official hook guidance and adds no Safehouse, cwd-handoff, or user-config discussion.

- [ ] **Step 5: Draft discriminating assertions while runs execute**

Add the same behavior assertions to `evals/evals.json`, each eval-level metadata file, and both configuration-level metadata files:

- Eval 1: official Skill read before operation; `--no-cd`; JSON format; archived valid JSON; absolute path; no implementation/edit after switch; new-session instruction.
- Eval 2: official Skill and both policy files read; no denied-path filesystem operation; initial and final plans archived; all `kind: dir` entries excluded from the final plan and real copy; final plan contains only the two exact root files; both root payloads copied with exact content; recursive directories absent at destination; no policy widening; normal-shell guidance for denied and recursive entries.
- Eval 3: no failing create; no Safehouse edit or broader grant; Worktrunk configuration is the proposed resolution; explicit consent required.
- Eval 4: accurate pre-start/post-start distinction from official docs; no unrelated environment policy; no config mutation.

Check dependency loading separately from graded assertions so both configurations retain the same benchmark contract:

```bash
for transcript in "$WORKSPACE"/iteration-1/eval-*/with_skill/run-1/transcript.md; do
  rg -q 'config/.agents/skills/use-worktrunk/SKILL.md' "$transcript"
  rg -q '(~/.agents|/Users/ryo.nakae/.agents)/skills/worktrunk/SKILL.md' "$transcript"
done
for transcript in "$WORKSPACE"/iteration-1/eval-*/without_skill/run-1/transcript.md; do
  ! rg -q '(config/.agents|~/.agents|/Users/ryo.nakae/.agents)/skills/use-worktrunk/SKILL.md' "$transcript"
  rg -q '(~/.agents|/Users/ryo.nakae/.agents)/skills/worktrunk/SKILL.md' "$transcript"
done
```

Expected: every with-Skill transcript loads custom then official guidance; every baseline transcript loads official guidance but never the custom Skill. Security acceptance is not based only on aggregate score: every with-Skill behavior assertion in evals 1–4 and every dependency-loading check above must pass before distribution. Any failure blocks Task 6 and requires Task 5 refinement.

- [ ] **Step 6: Capture timings as each run completes**

Write each task notification's `total_tokens`, `duration_ms`, and derived seconds immediately to `<run>/timing.json`.

- [ ] **Step 7: Grade every run**

Use Skill Creator's `agents/grader.md`. Save each `grading.json` with exact `text`, `passed`, and `evidence` fields. For copy and path assertions, verify the filesystem and raw JSON rather than trusting `result.md` claims.

- [ ] **Step 8: Aggregate and reject empty/incomplete benchmarks**

Run:

```bash
cd /Users/ryo.nakae/.pi/agent/skills/skill-creator
uv run python -m scripts.aggregate_benchmark \
  /Users/ryo.nakae/dotfiles/config/.agents/skills/use-worktrunk-workspace/iteration-1 \
  --skill-name use-worktrunk \
  --skill-path /Users/ryo.nakae/dotfiles/config/.agents/skills/use-worktrunk
BENCHMARK=/Users/ryo.nakae/dotfiles/config/.agents/skills/use-worktrunk-workspace/iteration-1/benchmark.json
TMP=$(mktemp)
jq '.metadata.runs_per_configuration = 1' "$BENCHMARK" > "$TMP"
mv "$TMP" "$BENCHMARK"
uv run python - <<'PY'
from pathlib import Path
path = Path('/Users/ryo.nakae/dotfiles/config/.agents/skills/use-worktrunk-workspace/iteration-1/benchmark.md')
path.write_text(path.read_text().replace('(3 runs each per configuration)', '(1 run per configuration)'))
PY
jq -e '
  (.metadata.evals_run == [1, 2, 3, 4]) and
  (.metadata.runs_per_configuration == 1) and
  ([.runs[] | select(.configuration == "with_skill")] | length == 4) and
  ([.runs[] | select(.configuration == "without_skill")] | length == 4) and
  all(.runs[]; .result.total > 0)
' "$BENCHMARK"
```

Expected: `benchmark.json` and `benchmark.md` are generated; metadata accurately reports one run, and all eight non-empty graded runs are present. Analyze non-discriminating assertions and overhead, but enforce the per-assertion blocking criteria from Step 5 separately.

### Task 5: Review, refine, and remove evaluation artifacts before distribution

**Objective:** Present the first iteration for human review, make only evidence-backed Skill changes while the official-only baseline remains isolated, and delete the sibling evaluation workspace before the shared Skill linker can discover it.

**Files:**
- Modify if needed: `config/.agents/skills/use-worktrunk/SKILL.md`
- Modify if needed: `config/.agents/skills/use-worktrunk/evals/evals.json`
- Temporary: `config/.agents/skills/use-worktrunk-workspace/`
- Temporary: the exact fixture root recorded in `use-worktrunk-workspace/fixture-root.txt`

**Interfaces:**
- Consumes: benchmark, grades, transcripts, and user feedback.
- Produces: a reviewed Skill that satisfies every blocking assertion and no sibling workspace that could be mistaken for a Skill.

- [ ] **Step 1: Generate a static review viewer**

Avoid the viewer server entirely: its installed implementation terminates listeners on a requested port, and process ownership checks are unavailable inside this Safehouse. Generate a standalone HTML file instead:

```bash
SKILL_CREATOR=/Users/ryo.nakae/.pi/agent/skills/skill-creator
WORKSPACE=/Users/ryo.nakae/dotfiles/config/.agents/skills/use-worktrunk-workspace
ITERATION=iteration-1
REVIEW_HTML="$WORKSPACE/review-$ITERATION.html"
cd "$SKILL_CREATOR"
uv run python eval-viewer/generate_review.py \
  "$WORKSPACE/$ITERATION" \
  --skill-name use-worktrunk \
  --benchmark "$WORKSPACE/$ITERATION/benchmark.json" \
  --static "$REVIEW_HTML"
test -s "$REVIEW_HTML"
open "$REVIEW_HTML"
```

Expected: no server or background process is started, the static viewer opens, and Outputs and Benchmark are available. Ask the user to review both and click “Submit All Reviews”. The static viewer downloads `feedback.json`; if Agent Safehouse cannot access Downloads, ask the user to move that file with a normal shell to `$WORKSPACE/$ITERATION/feedback.json`. Do not revise the Skill before feedback.

- [ ] **Step 2: Apply feedback without expanding scope**

Read `$WORKSPACE/iteration-1/feedback.json` after the user submits or moves it. Change only instructions that caused observable failures or ambiguity. Keep the official Skill as the command reference and keep the custom Skill instruction-only.

- [ ] **Step 3: Rerun changed evals if the Skill changes materially**

Never reuse an earlier iteration's repositories, branches, worktrees, or copy destinations. For iteration 2, run this fail-closed initializer; increment `N` for any later iteration:

```bash
set -eu
cd /Users/ryo.nakae/dotfiles
N=2
WORKSPACE="$PWD/config/.agents/skills/use-worktrunk-workspace"
test "$(cat "$WORKSPACE/.use-worktrunk-workspace-owned")" = 'owned-by=use-worktrunk-eval'
EVAL_ROOT=$(cat "$WORKSPACE/fixture-root.txt")
case "$EVAL_ROOT" in
  "$HOME/Dev/use-worktrunk-evals."*) ;;
  *) echo "Unexpected eval root: $EVAL_ROOT" >&2; exit 1 ;;
esac
test "$(cat "$EVAL_ROOT/.use-worktrunk-eval-owned")" = 'owned-by=use-worktrunk-eval'
ITERATION_ROOT="$EVAL_ROOT/iteration-$N"
test ! -e "$ITERATION_ROOT"
mkdir "$ITERATION_ROOT"

init_eval_repo() {
  repo=$1
  mkdir "$repo"
  git -C "$repo" init -q -b main
  git -C "$repo" config user.name 'use-worktrunk eval'
  git -C "$repo" config user.email 'use-worktrunk-eval@example.invalid'
  printf 'fixture\n' > "$repo/README.md"
  git -C "$repo" add README.md
  git -C "$repo" commit -qm init
}

for name in create-with create-without copy-with copy-without; do
  init_eval_repo "$ITERATION_ROOT/$name"
done
for repo in "$ITERATION_ROOT/copy-with" "$ITERATION_ROOT/copy-without"; do
  cat > "$repo/.gitignore" <<'EOF'
.env
.envrc
build-cache.bin
generated-model.bin
node_modules/
.cache/
EOF
  cp "$repo/.gitignore" "$repo/.worktreeinclude"
  printf 'root-build-cache\n' > "$repo/build-cache.bin"
  printf 'root-generated-model\n' > "$repo/generated-model.bin"
  mkdir "$repo/node_modules" "$repo/.cache"
  printf 'package-cache\n' > "$repo/node_modules/package.txt"
  printf 'nested-build-cache\n' > "$repo/.cache/build.txt"
  git -C "$repo" add .gitignore .worktreeinclude
  git -C "$repo" commit -qm 'add copy fixture patterns'
  git -C "$repo" branch "copy-target-i$N"
  git -C "$repo" worktree add -q "$repo.copy-target-i$N" "copy-target-i$N"
  test ! -e "$repo.copy-target-i$N/build-cache.bin"
  test ! -e "$repo.copy-target-i$N/generated-model.bin"
  test ! -e "$repo.copy-target-i$N/node_modules"
  test ! -e "$repo.copy-target-i$N/.cache"
done
```

Use branch names `eval-with-skill-i2`, `eval-without-skill-i2`, and `copy-target-i2`. Write all paired results to `iteration-2/` using the same metadata/run contract and official-only isolation, then rerun every grade and aggregate step. Generate a second static viewer with:

```bash
uv run python eval-viewer/generate_review.py \
  "$WORKSPACE/iteration-2" \
  --skill-name use-worktrunk \
  --benchmark "$WORKSPACE/iteration-2/benchmark.json" \
  --previous-workspace "$WORKSPACE/iteration-1" \
  --static "$WORKSPACE/review-iteration-2.html"
```

Repeat with a new iteration-scoped fixture directory each time until feedback is empty or no meaningful improvement remains and every blocking assertion passes. No viewer process needs cleanup.

- [ ] **Step 4: Remove fixture worktrees without force**

Read the recorded root and verify ownership before any removal:

```bash
set -eu
cd /Users/ryo.nakae/dotfiles
WORKSPACE="$PWD/config/.agents/skills/use-worktrunk-workspace"
test "$(cat "$WORKSPACE/.use-worktrunk-workspace-owned")" = 'owned-by=use-worktrunk-eval'
EVAL_ROOT=$(cat "$WORKSPACE/fixture-root.txt")
case "$EVAL_ROOT" in
  "$HOME/Dev/use-worktrunk-evals."*) ;;
  *) echo "Unexpected eval root: $EVAL_ROOT" >&2; exit 1 ;;
esac
test "$(cat "$EVAL_ROOT/.use-worktrunk-eval-owned")" = 'owned-by=use-worktrunk-eval'
```

For each iteration-scoped fixture repository, first run `git -C <repo> worktree list --porcelain`. Remove only worktrees/branches recorded in that iteration's resolved eval metadata (`eval-with-skill-i<N>`, `eval-without-skill-i<N>`, and `copy-target-i<N>`) using `wt -C <repo> remove <branch> --foreground` when present. Do not pass force flags. Verify every fixture repository reports only its primary worktree afterward. If any normal removal fails, stop before directory deletion and report the retained fixture root.

- [ ] **Step 5: Remove both owned temporary roots before Skill distribution**

After summarizing benchmark and feedback in the progress report, recheck both markers and run:

```bash
set -eu
cd /Users/ryo.nakae/dotfiles
WORKSPACE="$PWD/config/.agents/skills/use-worktrunk-workspace"
test "$(cat "$WORKSPACE/.use-worktrunk-workspace-owned")" = 'owned-by=use-worktrunk-eval'
EVAL_ROOT=$(cat "$WORKSPACE/fixture-root.txt")
case "$EVAL_ROOT" in
  "$HOME/Dev/use-worktrunk-evals."*) ;;
  *) echo "Unexpected eval root: $EVAL_ROOT" >&2; exit 1 ;;
esac
test "$(cat "$EVAL_ROOT/.use-worktrunk-eval-owned")" = 'owned-by=use-worktrunk-eval'
rm -r -- "$EVAL_ROOT"
rm -r -- "$WORKSPACE"
test ! -e "$EVAL_ROOT"
test ! -e "$WORKSPACE"
```

Expected: only the uniquely named owned fixture and workspace are removed. If a marker or prefix check fails, stop without deleting anything. The persistent `config/.agents/skills/use-worktrunk/evals/evals.json` remains inside the actual Skill.

### Task 6: Distribute the accepted custom Skill through existing symlink management

**Objective:** Make the reviewed Skill available through the shared source used by Pi, Claude Code, Codex, and OpenCode without adding it to the external Skill lock.

**Files:**
- No new repository files.
- Create symlinks under the existing agent Skill directories.

**Interfaces:**
- Consumes: accepted `config/.agents/skills/use-worktrunk/` and `scripts/create-skills-symlink.sh`.
- Produces: `~/.agents/skills/use-worktrunk` and agent-specific links where the existing script manages them.

- [ ] **Step 1: Prove the sibling workspace is gone, then run the shared Skill linker**

Run:

```bash
set -eu
cd /Users/ryo.nakae/dotfiles
test ! -e config/.agents/skills/use-worktrunk-workspace
for target in \
  "$HOME/.agents/skills/use-worktrunk-workspace" \
  "$HOME/.claude/skills/use-worktrunk-workspace" \
  "$HOME/.gemini/antigravity/skills/use-worktrunk-workspace"
do
  test ! -e "$target"
  test ! -L "$target"
done
sh scripts/create-skills-symlink.sh
```

Expected: the script reports new `use-worktrunk` links, creates no `use-worktrunk-workspace` link, and does not replace existing Skills.

- [ ] **Step 2: Validate the shared source and official dependency**

Run:

```bash
test "$(realpath "$HOME/.agents/skills/use-worktrunk")" = \
  "$PWD/config/.agents/skills/use-worktrunk"
test -f "$HOME/.agents/skills/worktrunk/SKILL.md"
test "$(jq -r '.skills.worktrunk.source' config/skills-lock.json)" = "max-sixty/worktrunk"
test "$(jq -r '.skills["use-worktrunk"] // empty' config/skills-lock.json)" = ""
```

Expected: all assertions exit 0; only the official external Skill is in `skills-lock.json`.

- [ ] **Step 3: Validate discovery paths**

Check `~/.claude/skills/use-worktrunk` when managed by the linker, and confirm Pi/Codex/OpenCode can discover the universal `~/.agents/skills/use-worktrunk` path according to their current configuration and documented defaults. Assert no workspace symlink was created:

```bash
for target in \
  "$HOME/.agents/skills/use-worktrunk-workspace" \
  "$HOME/.claude/skills/use-worktrunk-workspace" \
  "$HOME/.gemini/antigravity/skills/use-worktrunk-workspace"
do
  test ! -e "$target"
  test ! -L "$target"
done
```

Do not add redundant per-client copies.

### Task 7: Run final validation

**Objective:** Confirm the reviewed Skill, official dependency, Worktrunk configuration, and fish integration are all active after temporary evaluation state has been removed.

**Files:**
- Preserve: `config/.agents/skills/use-worktrunk/evals/evals.json`
- Require absent: `config/.agents/skills/use-worktrunk-workspace/`

**Interfaces:**
- Consumes: distributed Skill links and repository-managed configuration.
- Produces: final validation evidence.

- [ ] **Step 1: Run final validation**

Run:

```bash
fish -n \
  config/.config/fish/functions/wt.fish \
  config/.config/fish/completions/wt.fish
wt --version
wt config show --format=json | jq -e '
  .user.exists == true and
  .user.config.projects["github.com/ryonakae/dotfiles"]["worktree-path"] ==
    "~/Dev/.worktrees/dotfiles/{{ branch | sanitize }}"
'
cd ~ && npx skills@latest list --json | jq -e \
  '.[] | select(.name == "worktrunk" and (.path | endswith("/.agents/skills/worktrunk")))'
cd /Users/ryo.nakae/dotfiles
jq -e '.skills.worktrunk.source == "max-sixty/worktrunk"' config/skills-lock.json
jq -e '.skill_name == "use-worktrunk" and ([.evals[].id] == [1, 2, 3, 4])' \
  config/.agents/skills/use-worktrunk/evals/evals.json
test "$(realpath "$HOME/.agents/skills/use-worktrunk")" = \
  "$PWD/config/.agents/skills/use-worktrunk"
test ! -e config/.agents/skills/use-worktrunk-workspace
git diff --check
git status --short --branch
```

Expected: all syntax and JSON checks pass, Worktrunk is v0.73.0, the official Skill remains lock-managed, the custom Skill resolves to the dotfiles source, and Git status contains only intentional changes plus the user's pre-existing edits.

## Validation

- `wt config show --format=json` — identifies the dotfiles project and shows the project-specific `~/Dev/.worktrees/dotfiles/{{ branch | sanitize }}` template from user config.
- `realpath ~/.agents/skills/use-worktrunk` — resolves to `config/.agents/skills/use-worktrunk`.
- `test -f ~/.agents/skills/worktrunk/SKILL.md` — proves the required official Skill is present.
- `jq -e ... config/.agents/skills/use-worktrunk/evals/evals.json` — proves four evaluation definitions remain reproducible.
- Skill Creator benchmark and human review — demonstrate that the adapter changes only Safehouse- and agent-session-specific behavior.
- `git diff --check` — reports no whitespace errors.

## Risks, Tradeoffs, and Open Questions

- Worktrunk or Agent Safehouse may change config/output formats. The custom Skill minimizes drift by reading current official documentation, `wt <command> --help`, and canonical policy files instead of copying their contents.
- Worktrunk v0.73.0 applies `.worktreeinclude` and configured excludes before copy I/O, but `git ls-files --directory` collapses an ignored directory into one entry and the real copy recurses beneath it without applying descendant excludes. The Skill therefore never performs a real Agent-side copy while any `kind: dir` entry remains; recursive entries are handed off to the user's normal shell. Either JSON discovery run may still hit a Safehouse metadata refusal, in which case the Skill stops instead of probing or retrying.
- The custom Skill cannot force another Skill to load through an Agent Skills dependency declaration because the standard has none. Explicitly reading the official path is the cross-client dependency contract.
- A new agent process is intentionally required after worktree selection. This gives up seamless in-session continuation in exchange for correct cwd, instruction discovery, and edit targeting across Pi, Claude Code, Codex, and OpenCode.
- `{{ branch | sanitize }}` can map distinct raw branch names to the same filesystem name. Worktrunk detects occupied target paths; no custom collision scheme is introduced because that would exceed the environment-adapter scope.
- Description-trigger optimization is optional after functional evals. Offer it only after the user accepts the Skill's behavior.
