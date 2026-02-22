#!/bin/bash

PROJECT_DIR="${1:-$(pwd)}"
PROJECT_DIR=$(cd "$PROJECT_DIR" && pwd)
SESSION=$(basename "$PROJECT_DIR")

if zellij list-sessions --short 2>/dev/null | grep -qFx "$SESSION"; then
    cd "$PROJECT_DIR" && zellij attach "$SESSION"
else
    cd "$PROJECT_DIR" && zellij --session "$SESSION" --layout dev
fi
