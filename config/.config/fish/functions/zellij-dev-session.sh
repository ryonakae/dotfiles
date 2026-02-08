#!/bin/bash

PROJECT_DIR="${1:-$(pwd)}"
PROJECT_DIR=$(cd "$PROJECT_DIR" && pwd)
SESSION=$(basename "$PROJECT_DIR")

cd "$PROJECT_DIR" && zellij attach -c "$SESSION"
