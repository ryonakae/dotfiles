---
name: pencil-design-and-develop
description: "Design, inspect, and troubleshoot Pencil .pen files with MCP tools. Use this skill when an AI coding agent needs one selected mode per request: (1) Design-only editing in Pencil, (2) Design to Code implementation from Pencil files, (3) Code to Design synchronization into Pencil, or (4) Pencil MCP troubleshooting."
---

# Pencil Design and Develop

## Purpose

Use this skill for Pencil work with explicit mode selection.

1. Design or edit `.pen` files in Pencil.
2. Implement code from existing Pencil designs.
3. Synchronize code changes into Pencil designs.
4. Troubleshoot Pencil MCP and runtime issues.

## Mode Gating

Select one mode per request.

1. `Design-only`: Create or edit design content in Pencil.
2. `Design->Code`: Read `.pen` files and generate implementation code.
3. `Code->Design`: Reflect code-side structure and styles into Pencil.
4. `Troubleshooting`: Diagnose MCP, auth, document, and runtime failures.

Run multiple modes only when the user explicitly asks for a multi-step flow.

## Start Sequence

1. Call `get_editor_state(include_schema=false)` first.
2. If no editor is open, call `open_document`.
3. Call `batch_get` to understand current structure before any mutation.
4. Confirm the selected mode before detailed execution.
5. If tool behavior or API details are unclear, resolve docs with Context7 first; then consult `references/docs-map.md`.

## Workflow Selection

1. For design creation or design edits in Pencil, use Workflow A.
2. For implementation from Pencil designs, use Workflow B.
3. For syncing code into Pencil, use Workflow C.
4. For MCP/auth/export/runtime issues, use Workflow D.

## Workflow A: Design-only in Pencil

1. Read `references/workflow-design.md`.
2. Apply safety rules in `references/mcp-tool-rules.md` under the design mutation loop.
3. Enforce mode-eligible gates in `references/quality-gates.md`.
4. Run visual checks from `references/visual-verification.md` after each section.
5. Run `snapshot_layout(problemsOnly=true)` after each mutation batch.

## Workflow B: Design to Code

1. Read `references/workflow-design-to-code.md` and execute only the Design->Code section.
2. Read `.pen` structure hints in `references/pen-format-cheatsheet.md` when needed.
3. Apply responsive extraction rules from `references/responsive-breakpoints.md`.
4. Preserve reusable component boundaries and token semantics in generated code.
5. Report mapping decisions and unresolved ambiguities explicitly.

## Workflow C: Code to Design

1. Read `references/workflow-design-to-code.md` and execute only the Code->Design section.
2. Use `references/pen-format-cheatsheet.md` for reusable and slot-safe updates.
3. Apply mode-eligible gates in `references/quality-gates.md`.
4. Validate affected regions with screenshot and layout checks.

## Workflow D: Troubleshooting

1. Read `references/troubleshooting-playbook.md`.
2. Verify editor state, document state, and MCP tool availability in this order.
3. Isolate auth/session issues before changing prompts or operations.
4. Retry mutations only after connectivity and permissions are stable.

## Hard Rules

1. Do not mutate a document before reading structure with `batch_get`.
2. Keep each `batch_design` call to 25 operations or fewer.
3. Always use bindings for `I`, `C`, and `R` operations.
4. Do not update `children` with `U`; use `R` for node replacement.
5. Do not update copied descendants by original IDs; use `descendants` in `C`.
6. Use `G()` for image fills instead of hardcoded image URLs.
7. Reuse existing reusable components before creating new primitives.
8. Validate each completed mutation section with screenshot and layout checks.

## Reference Loading Rules

1. For tool portability and operation constraints, read `references/mcp-tool-rules.md`.
2. For mode-based pass/fail criteria, read `references/quality-gates.md`.
3. For responsive extraction in Design->Code, read `references/responsive-breakpoints.md`.
4. For screenshot QA, read `references/visual-verification.md`.
5. For official docs navigation, read `references/docs-map.md`.

## Output Contract

Every user-facing report must include:

1. Selected mode.
2. What was changed.
3. Which files or node IDs were affected.
4. What validations were run (visual and layout).
5. Any unresolved risks, assumptions, or constraints.
6. Which modes were intentionally not executed.
