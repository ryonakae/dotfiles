# Visual Verification Protocol

## Goal

Catch visual regressions early by validating each section instead of validating only at the end.

## Section-Level Verification Loop

For every logical section (for example header, hero, form block, card grid, sidebar):

1. Capture screenshot after finishing the section.
2. Inspect alignment and spacing consistency.
3. Inspect text clipping, wrapping, and hierarchy.
4. Inspect icon/image rendering and aspect behavior.
5. Run `snapshot_layout(problemsOnly=true)` and fix all reported issues.

## Full-Screen Verification

1. Capture a final full-screen screenshot after all sections pass.
2. Re-run layout snapshot for the full frame tree.
3. Confirm no section broke after global adjustments.

## Comparison Heuristics

1. Verify major anchors line up (headers, grid edges, container bounds).
2. Verify spacing rhythm is consistent within and across sections.
3. Verify visual emphasis hierarchy matches design intent.
4. Verify no accidental style drift from existing design systems.

## Reporting Requirements

Include in output:

1. Which sections were verified.
2. Which issues were found.
3. Which fixes were applied.
4. Which residual risks remain, if any.
