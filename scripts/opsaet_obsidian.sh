#!/bin/bash
# Gør fag/ til en Obsidian-vault: skabelon til emne-noter, pensum-PDF'er udelukket fra søgning.
# Brug: scripts/opsaet_obsidian.sh   – åbn derefter mappen "fag" som vault i Obsidian.
set -euo pipefail
ROD="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"
VAULT="$ROD/fag"
mkdir -p "$VAULT/.obsidian" "$VAULT/_skabeloner"
cp "$ROD/portable/obsidian/Emne.md" "$VAULT/_skabeloner/Emne.md"
[ -f "$VAULT/.obsidian/app.json" ] || cat > "$VAULT/.obsidian/app.json" <<'JSON'
{
  "userIgnoreFilters": ["kilder/"],
  "newFileLocation": "current",
  "alwaysUpdateLinks": true,
  "showFrontmatter": false
}
JSON
[ -f "$VAULT/.obsidian/templates.json" ] || echo '{ "folder": "_skabeloner", "dateFormat": "YYYY-MM-DD" }' > "$VAULT/.obsidian/templates.json"
echo "✓ Vault klar: $VAULT"
echo "  Obsidian → 'Åbn mappe som vault' → vælg $VAULT"
echo "  Slå kerne-plugin'et 'Skabeloner' til (Indstillinger → Kerne-plugins), hvis du vil indsætte skabelonen selv."
