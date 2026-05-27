#!/usr/bin/env bash
# =============================================================================
#  Ge-mini — Instalador Linux
#  Ejecutar con:  sh install.sh
#  Requiere: conexión a internet. Puede pedir sudo para instalar Ollama.
# =============================================================================

set -euo pipefail

# ── Colores ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; DIM='\033[2m'; NC='\033[0m'

ok()   { echo -e "${GREEN}[OK]${NC} $1"; }
step() { echo -e "${CYAN}[··]${NC} $1"; }
warn() { echo -e "${YELLOW}[!!]${NC} $1"; }
err()  { echo -e "${RED}[ERROR]${NC} $1"; }
sep()  { echo -e "${DIM}────────────────────────────────────────────────────${NC}"; }

# ── Modelos ───────────────────────────────────────────────────────────────────
MODELS=(
  "qwen2.5-coder:1.5b|Qwen 2.5 Coder 1.5B|Código, ligero|~1.5 GB|qwen2.5-coder:1.5b"
  "qwen2.5-coder:3b|Qwen 2.5 Coder 3B|Código, equilibrado|~2.5 GB|qwen2.5-coder:3b"
  "phi3.5:latest|Phi 3.5 Mini|Razonamiento|~3.0 GB|phi3.5"
  "mistral:7b-instruct-q4_K_M|Mistral 7B Instruct|General, maduro|~4.8 GB|mistral:7b-instruct"
  "qwen2.5-coder:7b|Qwen 2.5 Coder 7B|Código, potente|~5.2 GB|qwen2.5-coder:7b"
)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
cd "$PROJECT_ROOT"

clear
echo -e "${CYAN}${BOLD}"
echo "  ╔═══════════════════════════════════════════════════╗"
echo "  ║           💠  Ge-mini  —  Instalador             ║"
echo "  ╚═══════════════════════════════════════════════════╝"
echo -e "${NC}"
echo -e "  ${DIM}Sistema: Linux  |  Ruta: $PROJECT_ROOT${NC}"
echo

# =============================================================================
sep
echo -e "${BOLD}  PASO 1/5 — Entorno Python (uv)${NC}"
sep

if command -v uv &>/dev/null; then
  ok "uv ya instalado ($(uv --version))"
else
  step "Instalando uv..."
  if command -v curl &>/dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
  else
    err "curl no encontrado. Instálalo con tu gestor de paquetes y vuelve a ejecutar."
    exit 1
  fi
  export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
  if ! command -v uv &>/dev/null; then
    warn "uv instalado pero no en PATH. Añade ~/.local/bin a tu PATH y vuelve a ejecutar."
    exit 1
  fi
  ok "uv instalado"
fi

if [ -d ".venv" ]; then
  ok ".venv ya existe"
else
  step "Instalando Python 3.12 y creando entorno virtual..."
  uv python install 3.12
  uv venv .venv --python 3.12
  ok "Entorno virtual creado"
fi

step "Sincronizando dependencias..."
uv pip install -r requirements.txt --quiet
ok "Dependencias instaladas"

# =============================================================================
sep
echo -e "${BOLD}  PASO 2/5 — Ollama${NC}"
sep

if command -v ollama &>/dev/null; then
  ok "Ollama ya instalado"
else
  step "Instalando Ollama (puede pedir contraseña sudo)..."
  curl -fsSL https://ollama.com/install.sh | sh
  ok "Ollama instalado"
fi

step "Verificando servicio Ollama..."
OLLAMA_RUNNING=false
if curl -sf http://localhost:11434/api/tags &>/dev/null; then
  OLLAMA_RUNNING=true
  ok "Ollama ya está activo"
else
  step "Arrancando Ollama en segundo plano..."
  ollama serve &>/dev/null &
  OLLAMA_PID=$!
  sleep 4
  if curl -sf http://localhost:11434/api/tags &>/dev/null; then
    OLLAMA_RUNNING=true
    ok "Ollama arrancado (PID $OLLAMA_PID)"
  else
    warn "Ollama no responde. Los modelos locales no estarán disponibles en esta sesión."
  fi
fi

# =============================================================================
sep
echo -e "${BOLD}  PASO 3/5 — Modelos de IA local${NC}"
sep

echo -e "  ${DIM}Selecciona los modelos que quieres descargar.${NC}"
echo -e "  ${DIM}Modelos no descargados aparecerán deshabilitados en la interfaz.${NC}"
echo

INSTALLED_JSON=""
if $OLLAMA_RUNNING; then
  INSTALLED_JSON=$(curl -sf http://localhost:11434/api/tags 2>/dev/null || echo '{"models":[]}')
fi

is_installed() {
  local check="$1"
  echo "$INSTALLED_JSON" | grep -q "\"name\":\"[^\"]*${check}" && return 0 || return 1
}

printf "  %-4s %-28s %-22s %-10s %s\n" "Nº" "Modelo" "Descripción" "Tamaño" "Estado"
printf "  %-4s %-28s %-22s %-10s %s\n" "──" "───────────────────────────" "─────────────────────" "────────" "──────"

for i in "${!MODELS[@]}"; do
  IFS='|' read -r tag name desc size check <<< "${MODELS[$i]}"
  num=$((i + 1))
  if is_installed "$check"; then
    status="${GREEN}[OK]${NC}"
  else
    status="${DIM}[ ]${NC}"
  fi
  printf "  ${BOLD}[%-1s]${NC} %-28s %-22s %-10s %b\n" "$num" "$name" "$desc" "$size" "$status"
done

echo
echo -e "  ${DIM}Introduce números separados por comas (ej: 1,3)${NC}"
echo -e "  ${DIM}  t = todos   |   n = ninguno${NC}"
echo
printf "  Tu selección: "
read -r SELECTION

TO_DOWNLOAD=()
if [[ "$SELECTION" == "t" || "$SELECTION" == "T" ]]; then
  for i in "${!MODELS[@]}"; do TO_DOWNLOAD+=("$i"); done
elif [[ "$SELECTION" == "n" || "$SELECTION" == "N" || -z "$SELECTION" ]]; then
  echo -e "  ${DIM}Sin descargas. Puedes hacerlo más tarde volviendo a ejecutar install.sh${NC}"
else
  IFS=',' read -ra NUMS <<< "$SELECTION"
  for n in "${NUMS[@]}"; do
    n="${n// /}"
    if [[ "$n" =~ ^[0-9]+$ ]] && [ "$n" -ge 1 ] && [ "$n" -le "${#MODELS[@]}" ]; then
      TO_DOWNLOAD+=("$((n - 1))")
    else
      warn "Número ignorado (fuera de rango): $n"
    fi
  done
fi

echo
DOWNLOADED_TAGS=()

for i in "${!MODELS[@]}"; do
  IFS='|' read -r tag name desc size check <<< "${MODELS[$i]}"
  if is_installed "$check"; then DOWNLOADED_TAGS+=("$tag"); fi
done

for idx in "${TO_DOWNLOAD[@]}"; do
  IFS='|' read -r tag name desc size check <<< "${MODELS[$idx]}"
  if is_installed "$check"; then
    ok "$name ya está descargado"
  else
    if ! $OLLAMA_RUNNING; then
      warn "Ollama no activo — no se puede descargar $name"
      continue
    fi
    step "Descargando $name ($size)..."
    if ollama pull "$tag"; then
      ok "$name descargado"
      DOWNLOADED_TAGS+=("$tag")
    else
      err "Fallo al descargar $name"
    fi
  fi
done

mkdir -p data
ALL_TAGS=$(printf '"%s",' "${MODELS[@]%%|*}"); ALL_TAGS="[${ALL_TAGS%,}]"
INST_TAGS="["
for t in "${DOWNLOADED_TAGS[@]}"; do INST_TAGS+="\"$t\","; done
INST_TAGS="${INST_TAGS%,}]"
printf '{\n  "installed": %s,\n  "available": %s\n}\n' "$INST_TAGS" "$ALL_TAGS" > data/installed_models.json
ok "Estado guardado en data/installed_models.json"

# =============================================================================
sep
echo -e "${BOLD}  PASO 4/5 — Claves API${NC}"
sep

validate_key() {
  local key="$1" pattern="$2"
  [[ "$key" =~ $pattern ]]
}

if [ -f ".env" ]; then
  ok ".env ya existe — se mantiene sin cambios"
else
  echo -e "  ${DIM}Puedes dejar en blanco cualquier clave para omitir ese proveedor.${NC}"
  echo

  ENV_CONTENT="OLLAMA_BASE_URL=http://localhost:11434"$'\n'

  echo -e "  ${BOLD}[1/2] GEMINI_API_KEY${NC}"
  echo -e "        Proveedor  : Google Gemini"
  echo -e "        Formato    : empieza con ${BOLD}AIzaSy${NC} (39 caracteres)"
  echo -e "        Obtener en : https://aistudio.google.com/app/apikey"
  echo

  GEMINI_KEY=""
  while true; do
    printf "  > "; read -r input
    if [ -z "$input" ]; then
      warn "GEMINI_API_KEY omitida."
      break
    elif validate_key "$input" '^AIzaSy[0-9A-Za-z_-]{33}$'; then
      GEMINI_KEY="$input"; ok "Clave Gemini válida"; break
    else
      warn "Formato incorrecto. Esperado: AIzaSy + 33 caracteres."
      echo -e "  ${DIM}Enter para omitir o vuelve a intentarlo.${NC}"
    fi
  done
  [ -n "$GEMINI_KEY" ] && ENV_CONTENT+="GEMINI_API_KEY=$GEMINI_KEY"$'\n'

  echo
  echo -e "  ${BOLD}[2/2] GROQ_API_KEY${NC}"
  echo -e "        Proveedor  : Groq (modelos Llama cloud)"
  echo -e "        Formato    : empieza con ${BOLD}gsk_${NC} (aprox. 56 caracteres)"
  echo -e "        Obtener en : https://console.groq.com/keys"
  echo

  GROQ_KEY=""
  while true; do
    printf "  > "; read -r input
    if [ -z "$input" ]; then
      warn "GROQ_API_KEY omitida."
      break
    elif validate_key "$input" '^gsk_[0-9A-Za-z]{52,}$'; then
      GROQ_KEY="$input"; ok "Clave Groq válida"; break
    else
      warn "Formato incorrecto. Esperado: gsk_ + mínimo 52 caracteres."
      echo -e "  ${DIM}Enter para omitir o vuelve a intentarlo.${NC}"
    fi
  done
  [ -n "$GROQ_KEY" ] && ENV_CONTENT+="GROQ_API_KEY=$GROQ_KEY"$'\n'

  printf '%s' "$ENV_CONTENT" > .env
  ok ".env creado"
fi

# =============================================================================
sep
echo -e "${BOLD}  PASO 5/5 — Base de datos y arranque${NC}"
sep

step "Ejecutando migraciones..."
.venv/bin/python -m alembic upgrade head
ok "Base de datos actualizada"

echo
echo -e "${GREEN}${BOLD}"
echo "  ╔═══════════════════════════════════════════════════╗"
echo "  ║       ✅  Instalación completada                  ║"
echo "  ║   Accede en: http://127.0.0.1:8000/static/index.html  ║"
echo "  ║   Futuros arranques:  sh start.sh                 ║"
echo "  ╚═══════════════════════════════════════════════════╝"
echo -e "${NC}"

command -v xdg-open &>/dev/null && (sleep 2 && xdg-open http://127.0.0.1:8000/static/index.html &)
.venv/bin/python -m uvicorn app.main:app --port 8000
