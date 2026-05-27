# =============================================================================
#  Ge-mini — Instalador Windows (PowerShell)
#  Ejecutado por install.bat — no llamar directamente.
# =============================================================================
param (
    [string]$ProjectRoot = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
)

Set-Location $ProjectRoot
$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "Ge-mini — Instalador"

function Write-Ok   { param($m) Write-Host "[OK] $m" -ForegroundColor Green }
function Write-Step { param($m) Write-Host "[··] $m" -ForegroundColor Cyan }
function Write-Warn { param($m) Write-Host "[!!] $m" -ForegroundColor Yellow }
function Write-Err  { param($m) Write-Host "[ERROR] $m" -ForegroundColor Red }
function Write-Sep  { Write-Host ("─" * 54) -ForegroundColor DarkGray }

$MODELS = @(
    @{ Tag="qwen2.5-coder:1.5b";          Name="Qwen 2.5 Coder 1.5B"; Desc="Código, ligero";      Size="~1.5 GB"; Check="qwen2.5-coder:1.5b" },
    @{ Tag="qwen2.5-coder:3b";             Name="Qwen 2.5 Coder 3B";   Desc="Código, equilibrado"; Size="~2.5 GB"; Check="qwen2.5-coder:3b" },
    @{ Tag="phi3.5:latest";                Name="Phi 3.5 Mini";         Desc="Razonamiento";        Size="~3.0 GB"; Check="phi3.5" },
    @{ Tag="mistral:7b-instruct-q4_K_M";   Name="Mistral 7B Instruct";  Desc="General, maduro";     Size="~4.8 GB"; Check="mistral:7b-instruct" },
    @{ Tag="qwen2.5-coder:7b";             Name="Qwen 2.5 Coder 7B";   Desc="Código, potente";     Size="~5.2 GB"; Check="qwen2.5-coder:7b" }
)

Clear-Host
Write-Host ""
Write-Host "  ╔═══════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "  ║           💠  Ge-mini  —  Instalador             ║" -ForegroundColor Cyan
Write-Host "  ╚═══════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Sistema: Windows  |  Ruta: $ProjectRoot" -ForegroundColor DarkGray
Write-Host ""

Write-Sep
Write-Host "  PASO 1/5 — Entorno Python (uv)" -ForegroundColor White
Write-Sep

if (Get-Command uv -ErrorAction SilentlyContinue) {
    Write-Ok "uv ya instalado ($(uv --version))"
} else {
    Write-Step "Instalando uv..."
    try {
        Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
        $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","User") + ";" + $env:PATH
        Write-Ok "uv instalado"
    } catch {
        Write-Err "No se pudo instalar uv: $_"
        exit 1
    }
}

if (Test-Path ".venv") {
    Write-Ok ".venv ya existe"
} else {
    Write-Step "Instalando Python 3.12 y creando entorno virtual..."
    uv python install 3.12
    uv venv .venv --python 3.12
    Write-Ok "Entorno virtual creado"
}

Write-Step "Sincronizando dependencias..."
uv pip install -r requirements.txt --quiet
Write-Ok "Dependencias instaladas"

Write-Sep
Write-Host "  PASO 2/5 — Ollama" -ForegroundColor White
Write-Sep

if (Get-Command ollama -ErrorAction SilentlyContinue) {
    Write-Ok "Ollama ya instalado"
} else {
    Write-Step "Descargando Ollama (puede pedir permisos de administrador)..."
    $ollamaInstaller = "$env:TEMP\OllamaSetup.exe"
    try {
        Invoke-WebRequest "https://ollama.com/download/OllamaSetup.exe" -OutFile $ollamaInstaller -UseBasicParsing
        Start-Process $ollamaInstaller -ArgumentList "/VERYSILENT", "/NORESTART" -Wait
        $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","Machine") + ";" +
                    [System.Environment]::GetEnvironmentVariable("PATH","User")
        Remove-Item $ollamaInstaller -ErrorAction SilentlyContinue
        Write-Ok "Ollama instalado"
    } catch {
        Write-Err "No se pudo instalar Ollama: $_"
        exit 1
    }
}

Write-Step "Verificando servicio Ollama..."
$ollamaRunning = $false
try {
    Invoke-RestMethod "http://localhost:11434/api/tags" -TimeoutSec 3 | Out-Null
    $ollamaRunning = $true
    Write-Ok "Ollama activo"
} catch {
    Write-Step "Arrancando Ollama..."
    Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 5
    try {
        Invoke-RestMethod "http://localhost:11434/api/tags" -TimeoutSec 5 | Out-Null
        $ollamaRunning = $true
        Write-Ok "Ollama arrancado"
    } catch {
        Write-Warn "Ollama no responde. Los modelos locales no estarán disponibles."
    }
}

Write-Sep
Write-Host "  PASO 3/5 — Modelos de IA local" -ForegroundColor White
Write-Sep
Write-Host "  Selecciona los modelos que quieres descargar." -ForegroundColor DarkGray
Write-Host ""

$installedNames = @()
if ($ollamaRunning) {
    try {
        $tags = Invoke-RestMethod "http://localhost:11434/api/tags" -TimeoutSec 5
        $installedNames = $tags.models | ForEach-Object { $_.name }
    } catch { }
}

function Is-Installed { param($check) return ($installedNames | Where-Object { $_ -like "*$check*" }).Count -gt 0 }

Write-Host ("  {0,-4} {1,-28} {2,-22} {3,-10} {4}" -f "Nº","Modelo","Descripción","Tamaño","Estado")
Write-Host ("  {0,-4} {1,-28} {2,-22} {3,-10} {4}" -f "──","───────────────────────────","─────────────────────","────────","──────")

for ($i = 0; $i -lt $MODELS.Count; $i++) {
    $m = $MODELS[$i]
    $status = if (Is-Installed $m.Check) { "[OK]" } else { "[ ]" }
    $color  = if (Is-Installed $m.Check) { "Green" } else { "DarkGray" }
    Write-Host ("  [{0}] {1,-28} {2,-22} {3,-10}" -f ($i+1), $m.Name, $m.Desc, $m.Size) -NoNewline
    Write-Host " $status" -ForegroundColor $color
}

Write-Host ""
Write-Host "  Números separados por comas (ej: 1,3)  |  t=todos  |  n=ninguno" -ForegroundColor DarkGray
Write-Host ""
$selection = Read-Host "  Tu selección"

$toDownload = @()
if ($selection -eq "t" -or $selection -eq "T") {
    $toDownload = 0..($MODELS.Count-1)
} elseif ($selection -ne "n" -and $selection -ne "N" -and $selection -ne "") {
    $toDownload = $selection -split "," | ForEach-Object {
        $n = [int]$_.Trim() - 1
        if ($n -ge 0 -and $n -lt $MODELS.Count) { $n }
        else { Write-Warn "Fuera de rango: $($_.Trim())" }
    } | Where-Object { $_ -ne $null }
}

Write-Host ""
$downloadedTags = @($installedNames | Where-Object { $_ })

foreach ($idx in $toDownload) {
    $m = $MODELS[$idx]
    if (Is-Installed $m.Check) {
        Write-Ok "$($m.Name) ya descargado"
    } elseif (-not $ollamaRunning) {
        Write-Warn "Ollama no activo — no se puede descargar $($m.Name)"
    } else {
        Write-Step "Descargando $($m.Name) ($($m.Size))..."
        ollama pull $m.Tag
        if ($LASTEXITCODE -eq 0) { Write-Ok "$($m.Name) descargado"; $downloadedTags += $m.Tag }
        else { Write-Err "Fallo: $($m.Name)" }
    }
}

if (-not (Test-Path "data")) { New-Item -ItemType Directory "data" | Out-Null }
$allTags   = $MODELS | ForEach-Object { $_.Tag }
$installed = $downloadedTags | Where-Object { $_ } | Select-Object -Unique
@{ installed = @($installed); available = @($allTags) } | ConvertTo-Json -Depth 3 |
    Set-Content "data\installed_models.json" -Encoding UTF8
Write-Ok "Estado guardado en data\installed_models.json"

Write-Sep
Write-Host "  PASO 4/5 — Claves API" -ForegroundColor White
Write-Sep

if (Test-Path ".env") {
    Write-Ok ".env ya existe — sin cambios"
} else {
    Write-Host "  Deja en blanco para omitir un proveedor." -ForegroundColor DarkGray
    Write-Host ""
    $envLines = @("OLLAMA_BASE_URL=http://localhost:11434")

    function Read-ApiKey {
        param([string]$Label,[string]$Provider,[string]$Format,[string]$Url,[string]$Pattern)
        Write-Host "  $Label" -ForegroundColor Yellow
        Write-Host "        Proveedor  : $Provider"
        Write-Host "        Formato    : $Format"
        Write-Host "        Obtener en : $Url"
        Write-Host ""
        while ($true) {
            $v = Read-Host "  > "
            if ($v -eq "") { Write-Warn "$Label omitida."; return "" }
            elseif ($v -match $Pattern) { Write-Ok "Clave válida"; return $v }
            else { Write-Warn "Formato incorrecto: $Format"; Write-Host "  Enter para omitir." -ForegroundColor DarkGray }
        }
    }

    Write-Host "  [1/2] " -NoNewline
    $gk = Read-ApiKey "GEMINI_API_KEY" "Google Gemini" "AIzaSy + 33 chars (39 total)" "https://aistudio.google.com/app/apikey" "^AIzaSy[0-9A-Za-z_-]{33}$"
    if ($gk) { $envLines += "GEMINI_API_KEY=$gk" }
    Write-Host ""
    Write-Host "  [2/2] " -NoNewline
    $grk = Read-ApiKey "GROQ_API_KEY" "Groq (Llama cloud)" "gsk_ + 52+ chars" "https://console.groq.com/keys" "^gsk_[0-9A-Za-z]{52,}$"
    if ($grk) { $envLines += "GROQ_API_KEY=$grk" }

    $envLines | Set-Content ".env" -Encoding UTF8
    Write-Ok ".env creado"
}

Write-Sep
Write-Host "  PASO 5/5 — Base de datos y arranque" -ForegroundColor White
Write-Sep

Write-Step "Migraciones..."
& ".venv\Scripts\python.exe" -m alembic upgrade head
Write-Ok "Base de datos actualizada"

Write-Host ""
Write-Host "  ╔═══════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "  ║       ✅  Instalación completada                  ║" -ForegroundColor Green
Write-Host "  ║   http://127.0.0.1:8000/static/index.html         ║" -ForegroundColor Green
Write-Host "  ║   Futuros arranques: start.bat                    ║" -ForegroundColor Green
Write-Host "  ╚═══════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

Start-Process "http://127.0.0.1:8000/static/index.html"
Start-Sleep 2
& ".venv\Scripts\python.exe" -m uvicorn app.main:app --port 8000
