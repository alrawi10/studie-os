#!/bin/bash
# Absalon → fag/<fag>/kilder/ → NotebookLM. Brug: scripts/sync_all.sh [--fag KOF]
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/.local/bin:/opt/homebrew/bin:$PATH"

echo "### 1/2 Absalon-synk"
uv run -q --python 3.12 --with requests --with python-dotenv scripts/absalon_sync.py "$@"

echo
echo "### 2/2 NotebookLM-upload"
if ! nlm login --check >/dev/null 2>&1; then
  echo "NotebookLM-login er udløbet – kør 'nlm login' og derefter scripts/sync_all.sh igen." >&2
  exit 1
fi
uv run -q --python 3.12 --with python-pptx --with python-docx scripts/notebook_sync.py "$@"
