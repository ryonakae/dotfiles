#!/bin/sh

input=$(cat)
printf '%s' "$input" | AGENT_NOTIFICATION_SOURCE="gemini" "$HOME/.agents/hooks/notification.sh"

# Gemini CLI hooks は stdout を JSON として扱うため、空オブジェクトを返す
printf '{}\n'
