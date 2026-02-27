#!/bin/sh

AGENT_NOTIFICATION_SOURCE="codex" \
  exec "$HOME/.agents/hooks/notification.sh" "$@"
