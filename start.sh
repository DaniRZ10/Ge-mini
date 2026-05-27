#!/usr/bin/env bash
# Ge-mini — Arranque rápido (Linux)
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"
GREEN='\033[0;32m'; CYAN='\033[0;36m'; YELLOW='\033[1;33m'; NC='\033[0m'
echo -e "${CYAN}💠 Ge-mini — Arrancando...${NC}"
if [ ! -f ".venv/bin/python" ]; then
    echo -e "${YELLOW}[!!] Entorno no encontrado. Ejecuta primero: sh install.sh${NC}"; exit 1
fi
if command -v ollama &>/dev/null; then
    if ! curl -sf http://localhost:11434/api/tags &>/dev/null; then
        echo -e "${CYAN}[··] Arrancando Ollama...${NC}"
        ollama serve &>/dev/null &
        sleep 3
    fi
fi
echo -e "${GREEN}[OK] Servidor en http://127.0.0.1:8000/static/index.html${NC}"
command -v xdg-open &>/dev/null && (sleep 1 && xdg-open http://127.0.0.1:8000/static/index.html &)
.venv/bin/python -m uvicorn app.main:app --port 8000
