#!/bin/sh

AGENT_NOTIFICATION_SOURCE="pi" \
  exec "$HOME/.agents/hooks/notification.sh" "$@"
