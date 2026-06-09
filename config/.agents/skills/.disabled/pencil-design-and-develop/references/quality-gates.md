# Quality Gates

Apply only the gates required by the selected mode. Do not mark the task complete until all required gates pass.

## Gate 1: Reuse Existing Components First

Applies to: `Design-only`, `Design->Code`, `Code->Design`

Pass criteria:

1. Evidence exists that reusable components were discovered before creating new primitives (host-provided listing or tool query).
2. Existing reusable components are instantiated via `ref` where applicable.
3. New component creation is justified only when no equivalent exists.

## Gate 2: Use Variables and Tokens

Applies to: `Design-only`, `Design->Code`, `Code->Design`

Pass criteria:

1. Evidence exists that variable/token context was inspected before final styling decisions (host context or `get_variables`).
2. Colors, spacing, typography, and radius use variables when available.
3. Generated code uses semantic tokens/classes instead of arbitrary one-off values.

## Gate 3: Prevent Overflow and Clipping

Applies to: `Design-only`, `Code->Design`

Pass criteria:

1. Evidence exists that overflow/clipping checks were performed after each logical section (`snapshot_layout` or equivalent host-provided diagnostics).
2. Reported clipping/overlap/overflow issues are fixed immediately.
3. Text and container constraints are adjusted for target viewport widths.

## Gate 4: Visual Verification Per Section

Applies to: `Design-only`, `Code->Design`

Pass criteria:

1. Evidence exists that each completed section was visually verified (captured screenshot or equivalent host-provided visual check).
2. Alignment, spacing, content integrity, and hierarchy are reviewed.
3. A final full-screen screenshot is captured after all fixes.

## Gate 5: Responsive Consistency

Applies to: `Design->Code` (and `Code->Design` when responsive parity is explicitly in scope)

Pass criteria:

1. Artboard widths are mapped to explicit breakpoints.
2. Layout behavior differences across breakpoints are documented.
3. Generated code reflects those breakpoint behaviors.

## Gate 6: Safe Mutation Discipline

Applies to: `Design-only`, `Code->Design`

Pass criteria:

1. Each `batch_design` operation list has 25 operations or fewer.
2. Binding and replacement rules are followed for `I/C/R/U` usage.
3. Risky large changes are split into small validated passes.

## Completion Checklist

1. Required gates for the selected mode are explicitly satisfied.
2. Remaining assumptions or risks are documented.
3. Output includes changed nodes/files and validation evidence.
4. Output states which gates were not applicable in the selected mode.
