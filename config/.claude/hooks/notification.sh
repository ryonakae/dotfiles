#!/bin/sh

AGENT_NOTIFICATION_SOURCE="claude" \
  exec "$HOME/.agents/hooks/notification.sh" "$@"
