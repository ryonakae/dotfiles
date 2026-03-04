# Troubleshooting Playbook

## Isolation Order

1. Confirm Pencil editor is running and an expected `.pen` file is open.
2. Confirm MCP server/tool visibility in the current agent runtime.
3. Confirm authentication/session state.
4. Confirm workspace path and permission access.
5. Retry a minimal read operation (`get_editor_state`, then `batch_get`).
6. Retry mutation only after read operations are stable.

## Symptom to Action Map

| Symptom | Likely cause | First action |
| --- | --- | --- |
| Pencil tools not visible | MCP registration/runtime issue | Recheck MCP server list and reload session |
| Auth-related errors | Expired or conflicting auth context | Re-authenticate and clear conflicting auth env vars |
| Read operations fail | Document not open or path issue | Open document and retry `get_editor_state` |
| Mutation operations fail | Invalid IDs or operation misuse | Re-read IDs with `batch_get` and retry smaller batches |
| Export/import failures | Permission or unsupported payload | Verify file access and retry with minimal content |
| Random partial behavior | Session corruption or stale editor state | Restart editor/runtime and re-open `.pen` |

## Fast Recovery Sequence

1. Restart the agent runtime session.
2. Restart Pencil.
3. Open target `.pen` explicitly.
4. Verify MCP tool list and run `get_editor_state`.
5. Run a minimal `batch_get`.
6. Resume normal workflow.

## Preventive Practices

1. Keep mutation batches small and validated.
2. Save checkpoints frequently and use version control.
3. Avoid mixing auth changes with active design mutations.
