#!/bin/sh

# Claude Code / Codex 共通通知フック
# - Claude Code: stdin で JSON を受け取る
# - Codex: argv[1] で JSON を受け取り、agent-turn-complete のみ通知する
# - Gemini CLI: stdin で JSON を受け取る（Notification フック）

find_app_from_pid() {
  pid="$1"
  while [ "$pid" -gt 1 ] 2>/dev/null; do
    exe=$(ps -ww -o command= -p "$pid" 2>/dev/null | sed 's/^[[:space:]]*//')
    case "$exe" in
      */Contents/MacOS/*)
        app_bundle="${exe%/Contents/MacOS/*}"
        bundle_id=$(defaults read "${app_bundle}/Contents/Info" CFBundleIdentifier 2>/dev/null)
        if [ -n "$bundle_id" ]; then
          echo "$bundle_id"
          return 0
        fi
        ;;
    esac
    pid=$(ps -o ppid= -p "$pid" 2>/dev/null | tr -d ' ')
  done
  return 1
}

detect_terminal_app() {
  find_app_from_pid "$$" && return 0

  if [ -n "${TERM_PROGRAM:-}" ]; then
    bundle_id=$(osascript -e "id of app \"$TERM_PROGRAM\"" 2>/dev/null)
    if [ -n "$bundle_id" ]; then
      echo "$bundle_id"
      return 0
    fi
  fi

  return 1
}

run_terminal_notifier() {
  perl -e 'system { $ARGV[0] } @ARGV; exit 0;' "$@" >/dev/null 2>&1 || true
}

notify() {
  title="$1"
  message="$2"
  group="$3"
  activate_app=$(detect_terminal_app || true)

  if ! launchctl print "gui/$(id -u)" >/dev/null 2>&1; then
    return 0
  fi

  if [ -n "$group" ] && [ -n "$activate_app" ]; then
    run_terminal_notifier terminal-notifier -title "$title" -message "$message" -sound default -group "$group" -activate "$activate_app"
    return 0
  fi

  if [ -n "$group" ]; then
    run_terminal_notifier terminal-notifier -title "$title" -message "$message" -sound default -group "$group"
    return 0
  fi

  if [ -n "$activate_app" ]; then
    run_terminal_notifier terminal-notifier -title "$title" -message "$message" -sound default -activate "$activate_app"
    return 0
  fi

  run_terminal_notifier terminal-notifier -title "$title" -message "$message" -sound default
}

if ! command -v jq >/dev/null 2>&1; then
  exit 0
fi

if ! command -v terminal-notifier >/dev/null 2>&1; then
  exit 0
fi

source="${AGENT_NOTIFICATION_SOURCE:-}"
input=""
title=""
message=""
group=""

case "$source" in
  claude)
    input=$(cat)
    title=$(echo "$input" | jq -r '.title // "Claude Code"' 2>/dev/null)
    message=$(echo "$input" | jq -r '.message // "Claude Code"' 2>/dev/null)
    ;;
  codex)
    input="${1:-}"
    if [ -z "$input" ]; then
      exit 0
    fi

    event_type=$(echo "$input" | jq -r '.type // ""' 2>/dev/null)
    if [ "$event_type" != "agent-turn-complete" ]; then
      exit 0
    fi

    last_message=$(echo "$input" | jq -r '.["last-assistant-message"] // .last_assistant_message // ""' 2>/dev/null)
    if [ -n "$last_message" ]; then
      title="Codex: $last_message"
    else
      title="Codex"
    fi

    message=$(echo "$input" | jq -r '(.["input-messages"] // .input_messages // []) | map(tostring) | join(" ")' 2>/dev/null)
    if [ -z "$message" ]; then
      message="Turn complete"
    fi

    thread_id=$(echo "$input" | jq -r '.["thread-id"] // .thread_id // ""' 2>/dev/null)
    if [ -n "$thread_id" ]; then
      group="codex-$thread_id"
    fi
    ;;
  gemini)
    input=$(cat)
    notification_type=$(echo "$input" | jq -r '.notification_type // ""' 2>/dev/null)
    if [ -n "$notification_type" ]; then
      title="Gemini CLI: $notification_type"
    else
      title="Gemini CLI"
    fi

    message=$(echo "$input" | jq -r '.message // "Gemini CLI notification"' 2>/dev/null)
    ;;
  *)
    exit 0
    ;;
esac

notify "$title" "$message" "$group"
