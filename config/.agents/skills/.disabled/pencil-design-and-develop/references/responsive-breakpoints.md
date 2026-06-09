# Responsive Breakpoints

## Scope

Primary scope: `Design->Code` mode.

Use in `Code->Design` only when responsive parity is explicitly required.

## Goal

Derive reliable responsive implementation behavior from one or more Pencil artboards.

## Breakpoint Extraction Procedure

1. Collect artboard/frame widths representing each target viewport.
2. Group widths into practical breakpoint tiers.
3. Name tiers consistently (for example: `mobile`, `tablet`, `desktop`, `wide`).
4. Record layout differences per tier (stacking, spacing, visibility, typography scale).

## Default Tier Mapping

Use project-specific values when defined. If no values are defined, use this fallback:

- `mobile`: under 640px
- `tablet`: 640px to 1023px
- `desktop`: 1024px to 1279px
- `wide`: 1280px and above

## Implementation Mapping Guidance

1. Keep component structure stable across breakpoints when possible.
2. Move only layout/spacing/size behavior across breakpoints.
3. Avoid introducing new visual tokens only for one breakpoint without justification.
4. Preserve content order and accessibility semantics when layouts reflow.

## Validation

1. Verify each breakpoint tier against corresponding Pencil artboard.
2. Confirm no new overflow/clipping appears at intermediate widths.
3. Document breakpoint-specific assumptions when artboards are missing.

## Output Contract

When generating code from design, always include:

1. Which artboard widths were used.
2. Which breakpoint tiers were produced.
3. Which layout behaviors change at each tier.
