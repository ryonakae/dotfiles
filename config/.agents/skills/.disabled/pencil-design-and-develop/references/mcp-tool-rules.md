# Pencil MCP Tool Rules

## Portability: Canonical Name to Provider-Specific Name

Use canonical operation names in reasoning, then map to runtime tool names.

| Canonical operation | Common tool names |
| --- | --- |
| `get_editor_state` | `mcp__pencil__get_editor_state`, `pencil_get_editor_state` |
| `open_document` | `mcp__pencil__open_document`, `pencil_open_document` |
| `batch_get` | `mcp__pencil__batch_get`, `pencil_batch_get` |
| `batch_design` | `mcp__pencil__batch_design`, `pencil_batch_design` |
| `get_screenshot` | `mcp__pencil__get_screenshot`, `pencil_get_screenshot` |
| `snapshot_layout` | `mcp__pencil__snapshot_layout`, `pencil_snapshot_layout` |
| `get_variables` | `mcp__pencil__get_variables`, `pencil_get_variables` |
| `set_variables` | `mcp__pencil__set_variables`, `pencil_set_variables` |
| `get_guidelines` | `mcp__pencil__get_guidelines`, `pencil_get_guidelines` |
| `find_empty_space_on_canvas` | `mcp__pencil__find_empty_space_on_canvas`, `pencil_find_empty_space_on_canvas` |

## Runtime Context Resolution (Single Source of Truth)

1. Resolve runtime context in this order:
   1. Explicit runtime metadata from host/session (if present).
   2. Host-injected context markers (state summaries, prewired tool constraints).
   3. Best-effort heuristic hints from prompt/session shape.
2. If runtime cannot be resolved, default to `embedded-safe`.
3. `embedded-safe` means:
   1. Treat tool order guidance as advisory, not mandatory.
   2. Reuse host-provided context first.
   3. Add read calls only for missing evidence.
   4. Do not override host-level tool filters, permission gates, or runtime policy decisions.
4. `external` means:
   1. Follow full read-before-mutate sequencing.
   2. Keep the same mutation safety and quality checks.

## Embedded Host Compatibility

1. For `embedded` behavior, apply the `embedded-safe` policy defined in `Runtime Context Resolution`.
2. Do not redefine embedded runtime rules in this section; keep this section as a pointer to the single source of truth.

## Read-only Implementation Loop (Design->Code)

1. Ensure state context is available via host-provided summary or `get_editor_state`.
2. Ensure structure context is available with `batch_get` when host context is insufficient.
3. Ensure token context is available with `get_variables` when required for mapping.
4. Use `resolveInstances=true` only when instance internals are unclear.
5. Generate mapping and implementation output without mutating `.pen` nodes.

## Design Mutation Loop (Design-only / Code->Design)

1. Confirm current structure from host context or fresh reads (`get_editor_state`, `batch_get`) as needed.
2. Apply small mutation batches (`batch_design`).
3. Verify visually (`get_screenshot`) and structurally (`snapshot_layout`).
4. Repeat until required quality gates pass.
5. Apply runtime branching from `Runtime Context Resolution`; add extra read calls only when missing evidence blocks safe progress.

## `batch_get` Rules

1. Start shallow (`readDepth` 1 or 2) and widen only when needed.
2. Query reusable components in one call (`patterns: [{ reusable: true }]`).
3. Combine related pattern and node ID reads in fewer calls.
4. Use `resolveInstances=true` only when you need concrete descendant shape.
5. Avoid deep reads that flood context.

## `batch_design` Rules

1. Keep each operation list to 25 operations or fewer.
2. Always bind outputs of `I`, `C`, and `R`.
3. Do not use `U` to mutate `children`; use `R` to replace subtree nodes.
4. Do not update copied descendants by old IDs after `C`; pass `descendants` inside `C`.
5. Use `G(node, "ai"|"stock", prompt)` for image fills.
6. Split large edits into structure pass, content pass, polish pass.

## Common Failure Patterns

1. Running mutation operations during read-only Design->Code tasks.
2. Building new primitives when reusable components already exist.
3. Skipping screenshot/layout checks after mutation sections.
4. Applying hardcoded visual values when variables exist.
5. Over-reading the file graph and losing focus.
6. Mixing troubleshooting operations with active mutation loops.
7. Forcing duplicated host-preprocessed reads without evidence they are missing.
