#!/bin/bash
# Registrerer studiesystemets MCP-servere i Claude Desktop, så Chat og Cowork kan bruge dem:
#   studie      – sync, deadlines, kalenderplanlægning, opgaver, Siri-indbakke, figurer fra PDF'er
#   anki        – Anki (add-on'et AnkiMCP, via mcp-remote)
#   canvas-api  – kun hvis "lms" er canvas og Canvas MCP er installeret
#   NotebookLM  – via "nlm setup add claude-desktop"
# Brug (i Terminal.app, med Claude-appen HELT lukket – ⌘Q):  ~/Odontologi/scripts/desktop_mcp.sh
# Fjern igen:                                                 ~/Odontologi/scripts/desktop_mcp.sh --fjern
set -euo pipefail
ROD="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"
KONFIG="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"

if pgrep -xq Claude; then
  echo "❌ Claude-appen kører. Luk den helt (⌘Q) – ellers kan den overskrive konfigurationen – og kør igen." >&2
  exit 1
fi
mkdir -p "$(dirname "$KONFIG")"
[ -f "$KONFIG" ] || echo '{}' > "$KONFIG"
cp "$KONFIG" "$KONFIG.backup-$(date +%Y%m%d-%H%M%S)"

UV="$(command -v uv)"; NPX="$(command -v npx || true)"
python3 - "$KONFIG" "$ROD" "$UV" "$NPX" "${1:-}" <<'PY'
import json, os, sys
konfig, rod, uv, npx, flag = sys.argv[1:6]
d = json.load(open(konfig))
servere = d.setdefault("mcpServers", {})
vores = ["studie", "anki", "canvas-api"]
if flag == "--fjern":
    for n in vores:
        servere.pop(n, None)
    print("Fjernet:", ", ".join(vores))
else:
    deps = ["mcp>=2.2,<3", "requests", "python-dotenv", "icalendar", "python-pptx", "python-docx",
            "pymupdf", "pillow", "python-dateutil"]
    servere["studie"] = {"command": uv, "args": ["run", "-q", "--python", "3.12"]
                         + sum([["--with", x] for x in deps], []) + [f"{rod}/scripts/studie_mcp.py"]}
    if npx:  # GUI-apps har en kort PATH – giv node-mappen med, så npx kan finde node
        servere["anki"] = {"command": npx, "args": ["-y", "mcp-remote", "http://127.0.0.1:3141/"],
                           "env": {"PATH": f"{os.path.dirname(npx)}:/usr/bin:/bin"}}
    else:
        print("⚠️  npx ikke fundet – installér Node (brew install node) for at få Anki i Desktop.")
    cfg = json.load(open(f"{rod}/config/fag.json")) if os.path.exists(f"{rod}/config/fag.json") else {}
    canvas_bin = os.path.expanduser("~/.local/share/canvas-mcp/.venv/bin/canvas-mcp-server")
    if cfg.get("lms", "canvas") == "canvas" and os.path.exists(canvas_bin):
        servere["canvas-api"] = {"command": f"{rod}/scripts/canvas_mcp.sh"}
    print("Registreret:", ", ".join(n for n in vores if n in servere))
json.dump(d, open(konfig, "w"), indent=2, ensure_ascii=False)
PY

if [ "${1:-}" = "--fjern" ]; then
  nlm setup remove claude-desktop --profile regular || true
else
  nlm setup add claude-desktop --profile regular || echo "⚠️  NotebookLM kunne ikke registreres – kør 'nlm setup add claude-desktop' senere."
fi
echo "✅ Færdig. Åbn Claude igen. I en ny chat: klik på værktøjs-ikonet for at se 'studie', 'anki' og NotebookLM."
