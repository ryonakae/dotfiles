# Workflow: Design and Code Synchronization

## Goal

Support both Design->Code and Code->Design operations.

Run one direction per request by default. Execute both directions only when the user explicitly requests a multi-step flow.

## Mode Policy

1. Select `Design->Code` or `Code->Design` first.
2. Do not chain both directions automatically.
3. If multi-direction execution is requested, state the order explicitly before running.

Runtime context handling and fallback policy are defined in `references/mcp-tool-rules.md`.

## Design->Code Sequence

1. Resolve runtime context and initial evidence using `references/mcp-tool-rules.md`.
2. Ensure frame hierarchy and reusable component context is available (host context or `batch_get`).
3. Ensure token/theme context is available (`get_variables`) when missing from host context.
4. Read instance-expanded structure (`resolveInstances=true`) only for unclear component internals.
5. Split the design into implementation units (pages, sections, components).
6. Map layout semantics (frame/layout/gap/padding) to CSS or framework layout primitives.
7. Map design variables to semantic styling tokens in code.
8. Apply responsive mapping rules from `responsive-breakpoints.md`.
9. Emit code plus a mapping summary for traceability.

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
