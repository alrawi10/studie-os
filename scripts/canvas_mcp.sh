#!/bin/bash
# Starter Canvas MCP-serveren med token/URL fra projektets .env (hemmeligheder forbliver i .env).
# Registrér i Claude Code:  claude mcp add --scope user canvas-api -- <sti>/scripts/canvas_mcp.sh
ROD="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"
set -a
source "$ROD/.env"
set +a
exec "${CANVAS_MCP_BIN:-$HOME/.local/share/canvas-mcp/.venv/bin/canvas-mcp-server}" "$@"
