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

## Mode Selection

Select one mode per request.

1. `Design-only`: Create or edit design content in Pencil.
2. `Design->Code`: Read `.pen` files and generate implementation code.
3. `Code->Design`: Reflect code-side structure and styles into Pencil.
4. `Troubleshooting`: Diagnose MCP, auth, document, and runtime failures.

Run multiple modes only when the user explicitly asks for a multi-step flow.

If runtime context cannot be resolved, use `embedded-safe` behavior from `references/mcp-tool-rules.md`.

## Start Sequence

1. Read `references/mcp-tool-rules.md` first.
2. Resolve runtime context and tool naming via that file.
3. Confirm the selected mode.
4. Load only the mode-specific references below.
5. If tool behavior or API details are unclear, resolve docs with Context7 first; then consult `references/docs-map.md`.

## Mode Routing

### Design-only

1. Read `references/workflow-design.md`.
2. Apply mutation/tool safety from `references/mcp-tool-rules.md`.
3. Enforce mode gates from `references/quality-gates.md`.
4. Run checks from `references/visual-verification.md`.

### Design->Code

1. Read `references/workflow-design-to-code.md` and execute only the Design->Code section.
2. Apply responsive mapping from `references/responsive-breakpoints.md`.
3. Use `references/pen-format-cheatsheet.md` when `.pen` structure details are needed.

### Code->Design

1. Read `references/workflow-design-to-code.md` and execute only the Code->Design section.
2. Use `references/pen-format-cheatsheet.md` for reusable and slot-safe updates.
3. Enforce mode gates from `references/quality-gates.md`.
4. Run checks from `references/visual-verification.md`.

### Troubleshooting

1. Read `references/troubleshooting-playbook.md`.
2. Reuse runtime and failure handling rules from `references/mcp-tool-rules.md`.
3. Use `references/docs-map.md` for official documentation navigation.

## Non-negotiable Safety Rules

1. Do not mutate a document before structure is confirmed via host context or `batch_get`.
2. Keep each `batch_design` call to 25 operations or fewer.
3. Always use bindings for `I`, `C`, and `R` operations.
4. Do not update `children` with `U`; use `R` for node replacement.
5. Do not update copied descendants by original IDs; use `descendants` in `C`.
6. Validate each completed mutation section with screenshot and layout checks.

## Output Contract

Every user-facing report must include:

1. Selected mode.
2. Resolved runtime context (`embedded` or `external`) and whether fallback was used.
3. What was changed.
4. Which files or node IDs were affected.
5. What validations were run (visual and layout).
6. Any unresolved risks, assumptions, or constraints.
7. Which modes were intentionally not executed.

For runbooks and detailed guardrails, rely on:

1. `references/mcp-tool-rules.md`
2. `references/workflow-design.md`
3. `references/workflow-design-to-code.md`
4. `references/quality-gates.md`
5. `references/visual-verification.md`
6. `references/troubleshooting-playbook.md`
7. `references/docs-map.md`
