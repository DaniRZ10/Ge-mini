#!/usr/bin/env bash
# =============================================================================
#  Ge-mini — Instalador Linux (smart-model-selection)
# =============================================================================
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; DIM='\033[2m'; NC='\033[0m'

ok()   { echo -e "${GREEN}[OK]${NC} $1"; }
step() { echo -e "${CYAN}[··]${NC} $1"; }
warn() { echo -e "${YELLOW}[!!]${NC} $1"; }
err()  { echo -e "${RED}[ERROR]${NC} $1"; }
sep()  { echo -e "${DIM}────────────────────────────────────────────────────${NC}"; }

# ── Catálogo de 11 modelos: "TAG|NOMBRE|CATEGORIA|RAM_GB|CHECK" ──────────────
CATALOG=(
  "qwen2.5-coder:0.5b|Qwen Coder 0.5B|Código ultra ligero|2|qwen2.5-coder:0.5b"
  "llama3.2:1b|Llama 3.2 1B|Chat ligero|2|llama3.2:1b"
  "qwen2.5-coder:1.5b|Qwen Coder 1.5B|Código ligero|3|qwen2.5-coder:1.5b"
  "llama3.2:3b|Llama 3.2 3B|Chat general|5|llama3.2:3b"
  "qwen2.5-coder:3b|Qwen Coder 3B|Código equilibrado|5|qwen2.5-coder:3b"
  "phi3.5:latest|Phi 3.5 Mini|Razonamiento|6|phi3.5"
  "mistral:7b-instruct-q4_K_M|Mistral 7B|General maduro|8|mistral:7b-instruct"
  "qwen2.5-coder:7b|Qwen Coder 7B|Código capaz|8|qwen2.5-coder:7b"
  "llama3.1:8b|Llama 3.1 8B|Multipropósito|8|llama3.1:8b"
  "qwen2.5:14b|Qwen 2.5 14B|Razonamiento avanzado|12|qwen2.5:14b"
  "mixtral:8x7b|Mixtral 8x7B|Top tier MoE|28|mixtral:8x7b"
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

# ── Bienvenida ────────────────────────────────────────────────────────────────
cat << 'WELCOME'
  Ge-mini se va a instalar en este equipo. El proceso es automático:

    1. Prepara Python y el entorno aislado del proyecto.
    2. Instala Ollama (motor de IA local).
    3. Detecta tu hardware y recomienda modelos adaptados.
    4. Al final te pregunta si quieres usar también modelos cloud.
    5. Arranca la aplicación y abre tu navegador.

  Puedes parar con Ctrl+C en cualquier momento.

WELCOME

# ── Detección de RAM ──────────────────────────────────────────────────────────
detect_ram_gb() {
  awk '/MemTotal/ { printf "%d\n", $2 / 1024 / 1024 }' /proc/meminfo
}
RAM_GB=$(detect_ram_gb)
echo -e "  ${DIM}RAM detectada: ${BOLD}${RAM_GB} GB${NC}"
echo

# =============================================================================
sep; echo -e "${BOLD}  PASO 1/5 — Entorno Python (uv)${NC}"; sep

if command -v uv &>/dev/null; then
  ok "uv ya instalado ($(uv --version))"
else
  step "Instalando uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
  command -v uv &>/dev/null || { err "uv no en PATH. Añade ~/.local/bin"; exit 1; }
  ok "uv instalado"
fi

if [ -d ".venv" ]; then
  ok ".venv ya existe"
else
  step "Instalando Python 3.12..."
  uv python install 3.12
  uv venv .venv --python 3.12
  ok "Entorno virtual creado"
fi

step "Sincronizando dependencias..."
uv pip install -r requirements.txt --quiet
ok "Dependencias instaladas"

# =============================================================================
sep; echo -e "${BOLD}  PASO 2/5 — Ollama${NC}"; sep

if command -v ollama &>/dev/null; then
  ok "Ollama ya instalado"
else
  step "Instalando Ollama..."
  curl -fsSL https://ollama.com/install.sh | sh
  ok "Ollama instalado"
fi

OLLAMA_RUNNING=false
if curl -sf http://localhost:11434/api/tags &>/dev/null; then
  OLLAMA_RUNNING=true; ok "Ollama activo"
else
  step "Arrancando Ollama..."
  ollama serve &>/dev/null &
  sleep 4
  if curl -sf http://localhost:11434/api/tags &>/dev/null; then
    OLLAMA_RUNNING=true; ok "Ollama arrancado"
  else
    warn "Ollama no responde."
  fi
fi

# =============================================================================
sep; echo -e "${BOLD}  PASO 3/5 — Modelos locales${NC}"; sep
echo -e "  ${DIM}RAM disponible para modelos: ${BOLD}$((RAM_GB - 2)) GB${NC} (margen de 2 GB para el SO)"
echo

INSTALLED_JSON=""
if $OLLAMA_RUNNING; then
  INSTALLED_JSON=$(curl -sf http://localhost:11434/api/tags 2>/dev/null || echo '{"models":[]}')
fi

is_installed() { echo "$INSTALLED_JSON" | grep -q "\"name\":\"[^\"]*${1}" && return 0 || return 1; }

# ── Calcular recomendados ────────────────────────────────────────────────────
RAM_USABLE=$((RAM_GB - 2))
ELIGIBLE_IDX=()
for i in "${!CATALOG[@]}"; do
  IFS='|' read -r tag name cat ram check <<< "${CATALOG[$i]}"
  if [ "$ram" -le "$RAM_USABLE" ]; then ELIGIBLE_IDX+=("$i"); fi
done

RECOMMENDED=()
if [ ${#ELIGIBLE_IDX[@]} -eq 0 ]; then
  RECOMMENDED=("0")
elif [ ${#ELIGIBLE_IDX[@]} -le 3 ]; then
  RECOMMENDED=("${ELIGIBLE_IDX[@]}")
else
  RECOMMENDED=(
    "${ELIGIBLE_IDX[0]}"
    "${ELIGIBLE_IDX[$((${#ELIGIBLE_IDX[@]} / 2))]}"
    "${ELIGIBLE_IDX[-1]}"
  )
fi

is_recommended() {
  local idx="$1"
  for r in "${RECOMMENDED[@]}"; do [ "$r" == "$idx" ] && return 0; done
  return 1
}

# ── Mostrar tabla ────────────────────────────────────────────────────────────
echo -e "  ${DIM}[OK]=instalado [*]=recomendado [!]=excede tu RAM${NC}"
echo
printf "  %-4s %-22s %-22s %-7s %s\n" "Nº" "Modelo" "Uso" "RAM" "Estado"
printf "  %-4s %-22s %-22s %-7s %s\n" "──" "──────────────────────" "──────────────────────" "───────" "──────"

for i in "${!CATALOG[@]}"; do
  IFS='|' read -r tag name cat ram check <<< "${CATALOG[$i]}"
  num=$((i + 1))
  status=""
  if is_installed "$check"; then status="${GREEN}[OK]${NC}"
  elif [ "$ram" -gt "$RAM_USABLE" ]; then status="${YELLOW}[!]${NC}"
  elif is_recommended "$i"; then status="${CYAN}[*]${NC}"
  else status="${DIM}[ ]${NC}"
  fi
  printf "  ${BOLD}[%-2s]${NC} %-22s %-22s %-7s %b\n" "$num" "$name" "$cat" "${ram} GB" "$status"
done

echo
echo -e "  ${DIM}Introduce números (ej: 1,3,5)  |  r=recomendados  |  t=todos  |  n=ninguno${NC}"
printf "  Tu selección: "
read -r SELECTION

TO_DOWNLOAD=()
case "$SELECTION" in
  ""|"r"|"R") TO_DOWNLOAD=("${RECOMMENDED[@]}") ;;
  "n"|"N") ;;
  "t"|"T") for i in "${!CATALOG[@]}"; do TO_DOWNLOAD+=("$i"); done ;;
  *)
    IFS=',' read -ra NUMS <<< "$SELECTION"
    for n in "${NUMS[@]}"; do
      n="${n// /}"
      if [[ "$n" =~ ^[0-9]+$ ]] && [ "$n" -ge 1 ] && [ "$n" -le "${#CATALOG[@]}" ]; then
        TO_DOWNLOAD+=("$((n - 1))")
      else warn "Ignorado: $n"; fi
    done ;;
esac

echo
DOWNLOADED_TAGS=()
for i in "${!CATALOG[@]}"; do
  IFS='|' read -r tag name cat ram check <<< "${CATALOG[$i]}"
  is_installed "$check" && DOWNLOADED_TAGS+=("$tag")
done

for idx in "${TO_DOWNLOAD[@]}"; do
  IFS='|' read -r tag name cat ram check <<< "${CATALOG[$idx]}"
  if is_installed "$check"; then ok "$name ya descargado"
  elif ! $OLLAMA_RUNNING; then warn "Ollama no activo — saltando $name"
  else
    step "Descargando $name..."
    if ollama pull "$tag"; then ok "$name descargado"; DOWNLOADED_TAGS+=("$tag")
    else err "Fallo: $name"; fi
  fi
done

# ── Tags personalizados ──────────────────────────────────────────────────────
echo
echo -e "  ${BOLD}Tags personalizados${NC} ${DIM}(opcional)${NC}"
echo -e "  ${DIM}Cualquier tag de Ollama (ej: codellama:13b). Enter para terminar.${NC}"
CUSTOM_TAGS=()
while true; do
  printf "  Tag: "; read -r CTAG
  [ -z "$CTAG" ] && break
  if $OLLAMA_RUNNING; then
    step "Descargando $CTAG..."
    if ollama pull "$CTAG"; then ok "$CTAG descargado"; CUSTOM_TAGS+=("$CTAG")
    else err "Fallo: $CTAG"; fi
  fi
done

# ── Estado a disco ───────────────────────────────────────────────────────────
mkdir -p data
ALL_TAGS=$(printf '"%s",' "${CATALOG[@]%%|*}"); ALL_TAGS="[${ALL_TAGS%,}]"
INST_TAGS="["; for t in "${DOWNLOADED_TAGS[@]}"; do INST_TAGS+="\"$t\","; done; INST_TAGS="${INST_TAGS%,}]"
CUST_TAGS="["; for t in "${CUSTOM_TAGS[@]}"; do CUST_TAGS+="\"$t\","; done; CUST_TAGS="${CUST_TAGS%,}]"
printf '{\n  "installed": %s,\n  "available": %s,\n  "custom": %s\n}\n' "$INST_TAGS" "$ALL_TAGS" "$CUST_TAGS" > data/installed_models.json
ok "Estado guardado en data/installed_models.json"

# =============================================================================
sep; echo -e "${BOLD}  PASO 4/5 — Modelos cloud (opcional)${NC}"; sep

# ── Leer .env existente si lo hay ─────────────────────────────────────────────
EXISTING_GEMINI=""; EXISTING_GROQ=""; EXISTING_ANTHROPIC=""
if [ -f ".env" ]; then
  EXISTING_GEMINI=$(grep -E "^GEMINI_API_KEY=" .env | cut -d= -f2- || echo "")
  EXISTING_GROQ=$(grep -E "^GROQ_API_KEY=" .env | cut -d= -f2- || echo "")
  EXISTING_ANTHROPIC=$(grep -E "^ANTHROPIC_API_KEY=" .env | cut -d= -f2- || echo "")
fi

echo -e "  ¿Quieres configurar modelos en la nube? ${DIM}(s/N)${NC}"
printf "  > "; read -r CLOUD_YES

if [[ "$CLOUD_YES" == "s" || "$CLOUD_YES" == "S" ]]; then
  echo
  echo -e "  ${BOLD}Proveedores cloud disponibles:${NC}"
  echo -e "    [1] Google Gemini   $([ -n "$EXISTING_GEMINI" ] && echo -e "${GREEN}[ya configurado]${NC}")"
  echo -e "    [2] Groq (Llama)    $([ -n "$EXISTING_GROQ" ] && echo -e "${GREEN}[ya configurado]${NC}")"
  echo -e "    [3] Anthropic (Claude)  $([ -n "$EXISTING_ANTHROPIC" ] && echo -e "${GREEN}[ya configurado]${NC}")"
  echo
  printf "  Selecciona (ej: 1,3): "
  read -r PROVS

  NEW_GEMINI="$EXISTING_GEMINI"
  NEW_GROQ="$EXISTING_GROQ"
  NEW_ANTHROPIC="$EXISTING_ANTHROPIC"

  ask_key() {
    local label="$1" provider="$2" format="$3" url="$4" regex="$5" ping_cmd="$6"
    local key=""
    echo
    echo -e "  ${BOLD}$label${NC}"
    echo -e "        Proveedor : $provider"
    echo -e "        Formato   : $format"
    echo -e "        Obtener en: $url"
    while true; do
      printf "  > "; read -r key
      [ -z "$key" ] && { warn "Omitida."; echo ""; return; }
      if ! [[ "$key" =~ $regex ]]; then
        warn "Formato incorrecto."
        echo -e "  ${DIM}Enter para omitir o vuelve a intentarlo.${NC}"
        continue
      fi
      step "Validando clave..."
      if eval "$ping_cmd \"$key\""; then
        ok "Clave válida"
        echo "$key"
        return
      else
        warn "La clave parece inválida según el proveedor."
        echo -e "  ${DIM}Enter para guardarla igual, o vuelve a intentarlo.${NC}"
        printf "  > "; read -r FORCE
        [ -z "$FORCE" ] && { echo "$key"; return; }
      fi
    done
  }

  ping_gemini() { curl -sf -o /dev/null -w "%{http_code}" "https://generativelanguage.googleapis.com/v1beta/models?key=$1" --max-time 5 | grep -q "200"; }
  ping_groq() { curl -sf -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $1" "https://api.groq.com/openai/v1/models" --max-time 5 | grep -q "200"; }
  ping_anthropic() { curl -sf -o /dev/null -w "%{http_code}" -H "x-api-key: $1" -H "anthropic-version: 2023-06-01" "https://api.anthropic.com/v1/models" --max-time 5 | grep -q "200"; }

  IFS=',' read -ra PROVNUMS <<< "$PROVS"
  for p in "${PROVNUMS[@]}"; do
    p="${p// /}"
    case "$p" in
      1)
        [ -n "$EXISTING_GEMINI" ] && { ok "GEMINI ya configurado, omitido"; continue; }
        NEW_GEMINI=$(ask_key "GEMINI_API_KEY" "Google Gemini" "AIzaSy + 33 chars" \
          "https://aistudio.google.com/app/apikey" '^AIzaSy[0-9A-Za-z_-]{33}$' "ping_gemini")
        ;;
      2)
        [ -n "$EXISTING_GROQ" ] && { ok "GROQ ya configurado, omitido"; continue; }
        NEW_GROQ=$(ask_key "GROQ_API_KEY" "Groq (Llama cloud)" "gsk_ + 52+ chars" \
          "https://console.groq.com/keys" '^gsk_[0-9A-Za-z]{52,}$' "ping_groq")
        ;;
      3)
        [ -n "$EXISTING_ANTHROPIC" ] && { ok "ANTHROPIC ya configurado, omitido"; continue; }
        echo
        echo -e "  ${YELLOW}⚠ Claude Opus 4.7 tiene coste alto por token (~\$15/M output).${NC}"
        echo -e "  ${DIM}  Revisa tu consola de Anthropic si planeas usarlo intensivamente.${NC}"
        NEW_ANTHROPIC=$(ask_key "ANTHROPIC_API_KEY" "Anthropic (Claude)" "sk-ant- + 80+ chars" \
          "https://console.anthropic.com/" '^sk-ant-[A-Za-z0-9_\-]{80,}$' "ping_anthropic")
        ;;
    esac
  done

  # ── Regenerar .env ──────────────────────────────────────────────────────────
  {
    echo "OLLAMA_BASE_URL=http://localhost:11434"
    [ -n "$NEW_GEMINI" ] && echo "GEMINI_API_KEY=$NEW_GEMINI"
    [ -n "$NEW_GROQ" ] && echo "GROQ_API_KEY=$NEW_GROQ"
    [ -n "$NEW_ANTHROPIC" ] && echo "ANTHROPIC_API_KEY=$NEW_ANTHROPIC"
  } > .env
  ok ".env actualizado"
else
  if [ ! -f ".env" ]; then
    echo "OLLAMA_BASE_URL=http://localhost:11434" > .env
    ok ".env creado solo con Ollama"
  else
    ok ".env existente respetado"
  fi
fi

# =============================================================================
sep; echo -e "${BOLD}  PASO 5/5 — Migraciones y arranque${NC}"; sep
step "Migraciones..."
.venv/bin/python -m alembic upgrade head
ok "Base de datos actualizada"

echo
echo -e "${GREEN}${BOLD}"
echo "  ╔═══════════════════════════════════════════════════╗"
echo "  ║       ✅  Instalación completada                  ║"
echo "  ║   http://127.0.0.1:8000/static/index.html         ║"
echo "  ║   Futuros arranques:  sh start.sh                 ║"
echo "  ╚═══════════════════════════════════════════════════╝"
echo -e "${NC}"

command -v xdg-open &>/dev/null && (sleep 2 && xdg-open http://127.0.0.1:8000/static/index.html &)
.venv/bin/python -m uvicorn app.main:app --port 8000
