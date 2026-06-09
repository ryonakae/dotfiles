# .pen Format Cheatsheet

## Document Shape

A `.pen` file is JSON-like structured design data with these common fields:

- `version`
- `children` (required)
- `variables` (optional)
- `themes` (optional)

## Common Node Types

- Layout containers: `frame`, `group`
- Shapes: `rectangle`, `ellipse`, `line`, `polygon`, `path`
- Content: `text`, `icon_font`, `note`, `prompt`, `context`
- Reusable instance: `ref`

## Reusable Components

1. Set `reusable: true` on the component definition.
2. Insert instances via `type: "ref"` and `ref: "<component-id>"`.
3. Override descendant properties with `U("instanceId/childId", { ... })`.
4. For copied trees, pass descendant overrides in `C(..., { descendants: { ... }})`.

## Slots

Use slot paths like `instanceId/slotId` to replace or insert slot content.

## Variables and Themes

1. Prefer variable references over hardcoded values.
2. Theme resolution follows the last matching condition rule.
3. Keep variable naming stable when synchronizing with code.

## Layout Behavior

1. Parent auto-layout controls child positioning; child `x`/`y` may be ignored.
2. Use fill constraints intentionally (`fill_container`) in layout contexts.
3. Validate clipping/overflow after each mutation batch.
