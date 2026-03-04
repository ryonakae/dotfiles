# Pencil Design and Develop Skill

This skill helps AI coding agents work with Pencil `.pen` files using a selected execution mode.

## Primary use cases

1. Design and edit screens/components in Pencil.
2. Read Pencil design files and implement frontend code.

## Additional supported modes

1. Synchronize code-side updates back into Pencil designs.
2. Troubleshoot Pencil MCP connectivity and runtime issues.

## How this skill executes

1. Default behavior is one mode per request.
2. Multi-mode execution is allowed only when the user explicitly requests it.
3. `Design ↔ Code` means bidirectional capability, not mandatory sequential execution.

## Highlights

1. Quality-gated workflow (component reuse, token usage, overflow checks, visual checks).
2. Progressive disclosure references for design, implementation mapping, troubleshooting, and responsive behavior.
3. Tool-name portability guidance across different MCP provider naming schemes.
4. Explicit output contract with selected mode and skipped modes.

## Folder structure

- `SKILL.md`: Trigger description and mode-based workflow instructions.
- `references/`: Detailed procedures and checklists.
- `README.md`: English summary and usage overview.
- `README.ja.md`: Japanese summary.

## Invocation examples

- `Use $pencil-design-and-develop to design a new dashboard in Pencil.`
- `Use $pencil-design-and-develop to read this .pen file and implement it in React.`
