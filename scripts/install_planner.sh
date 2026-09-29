#!/bin/bash
# Installerer (eller fjerner med --fjern) den automatiske planlægning som launchd-agent (macOS).
# Bemærk: projektmappen må ikke ligge i ~/Desktop, ~/Documents eller ~/Downloads – macOS
# blokerer baggrundsjob dér.
set -euo pipefail
ROD="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"
LABEL="dk.full-uni-package.studieplan"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
INTERVAL="${INTERVAL:-1800}"

launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
if [[ "${1:-}" == "--fjern" ]]; then rm -f "$PLIST"; echo "Fjernet."; exit 0; fi

case "$ROD" in "$HOME/Desktop"*|"$HOME/Documents"*|"$HOME/Downloads"*)
  echo "Flyt projektet ud af $ROD først (fx til ~/$(basename "$ROD"))." >&2; exit 1;;
esac

mkdir -p "$ROD/planlaegning" "$(dirname "$PLIST")"
cat > "$PLIST" <<PL
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key><array><string>$ROD/scripts/planlaeg_auto.sh</string></array>
  <key>StartInterval</key><integer>$INTERVAL</integer>
  <key>RunAtLoad</key><true/>
  <key>StandardErrorPath</key><string>$ROD/planlaegning/launchd.err</string>
</dict>
</plist>
PL
launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo "Installeret: planlægger hvert $((INTERVAL / 60)). minut. Log: $ROD/planlaegning/auto.log"
