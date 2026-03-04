# Workflow: Design and Code Synchronization

## Goal

Support both Design->Code and Code->Design operations.

Run one direction per request by default. Execute both directions only when the user explicitly requests a multi-step flow.

## Mode Policy

1. Select `Design->Code` or `Code->Design` first.
2. Do not chain both directions automatically.
3. If multi-direction execution is requested, state the order explicitly before running.

## Design->Code Sequence

1. Extract frame hierarchy and reusable components with `batch_get`.
2. Extract tokens and theme axes with `get_variables`.
3. Read instance-expanded structure (`resolveInstances=true`) only for unclear component internals.
4. Split the design into implementation units (pages, sections, components).
5. Map layout semantics (frame/layout/gap/padding) to CSS or framework layout primitives.
6. Map design variables to semantic styling tokens in code.
7. Apply responsive mapping rules from `responsive-breakpoints.md`.
8. Emit code plus a mapping summary for traceability.

## Code->Design Sequence

1. Identify source files and target `.pen` regions.
2. Recreate or update structure as reusable components where possible.
3. Align imported styles with existing Pencil variables.
4. Validate updated regions with screenshot and layout checks.

## Mapping Reference

| Pencil concept | Code concept |
| --- | --- |
| `frame` + `layout` | `flex`/layout containers |
| `reusable: true` | reusable UI component definition |
| `ref` | component instance with overrides |
| `variables` | design tokens / CSS variables / theme tokens |
| `themes` | theme variants / mode variants |
| slot path (`instance/slot`) | component composition slots |

## Output Requirements

1. Selected direction (`Design->Code` or `Code->Design`).
2. Explicit token mapping decisions.
3. Responsive behavior mapping by breakpoint when Design->Code is used.
4. Assumptions where design intent is ambiguous.
5. Visual or structural mismatch risks.
