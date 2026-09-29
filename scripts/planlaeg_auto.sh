#!/bin/bash
# Køres af launchd hver 30. min (installeres med scripts/install_planner.sh).
ROD="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"
cd "$ROD" || exit 1
export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/.local/bin:/usr/bin:/bin"
mkdir -p planlaegning
uv run -q --python 3.12 --with python-dateutil scripts/kalender.py planlaeg --skriv --stille >> planlaegning/auto.log 2>&1
tail -n 500 planlaegning/auto.log > planlaegning/auto.log.tmp && mv planlaegning/auto.log.tmp planlaegning/auto.log
