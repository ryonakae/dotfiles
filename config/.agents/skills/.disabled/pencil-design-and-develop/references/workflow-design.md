# Workflow: Design in Pencil

## Scope

This workflow is the primary procedure for `Design-only` mode.

## Goal

Create or update `.pen` designs safely while preserving consistency with existing design systems.

Runtime context handling and fallback policy are defined in `references/mcp-tool-rules.md`.

## Standard Sequence

1. Resolve runtime context and initial evidence using `references/mcp-tool-rules.md`.
2. Ensure editor state is available (host-provided context or `get_editor_state(include_schema=false)`).
3. Ensure top-level and target-region structure is available (host context or `batch_get`).
4. Discover reusable components with `batch_get(patterns: [{ reusable: true }])` when not already known.
5. Read variables with `get_variables` when token context is missing.
6. Build section by section using `batch_design` in small batches.
7. After each section, run `get_screenshot` and `snapshot_layout(problemsOnly=true)`.
8. Apply fixes immediately when overflow, clipping, or alignment issues appear.

## Existing Screen Edits

1. Capture a before screenshot for the target frame.
2. Reuse existing components first; add new components only when no equivalent exists.
3. Match established variables, spacing rhythm, and typography scale.
4. Capture an after screenshot at the same scope.
5. Confirm no new layout problems in `snapshot_layout`.

## New Screen Creation

1. Define target screen size and placement before inserting content.
2. Build layout skeleton first (major containers and navigation).
3. Populate sections with reusable components.
4. Add textual content and media after hierarchy is stable.
5. Run final full-screen screenshot and layout validation.

## Style Direction

1. When no design system exists, optionally use `get_guidelines` and `get_style_guide`.
2. When a design system exists, prioritize consistency over stylistic reinvention.

## Exit Criteria

1. All required quality gates for `Design-only` pass (`references/quality-gates.md`).
2. No `snapshot_layout(problemsOnly=true)` issues remain.
3. Visual checks pass for each section and final screen.
