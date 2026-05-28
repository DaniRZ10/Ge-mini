# =============================================================================
#  Ge-mini -- Instalador Windows (PowerShell) -- smart-model-selection
#  Ejecutado por install.bat -- no llamar directamente.
# =============================================================================
param (
    [string]$ProjectRoot = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
)

Set-Location $ProjectRoot
$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "Ge-mini -- Instalador"

function Write-Ok   { param($m) Write-Host "[OK] $m" -ForegroundColor Green }
function Write-Step { param($m) Write-Host "[..] $m" -ForegroundColor Cyan }
function Write-Warn { param($m) Write-Host "[!!] $m" -ForegroundColor Yellow }
function Write-Err  { param($m) Write-Host "[ERROR] $m" -ForegroundColor Red }
function Write-Sep  { Write-Host ("-" * 54) -ForegroundColor DarkGray }

# -- Catalogo de 11 modelos ----------------------------------------------------
$CATALOG = @(
    @{ Tag="qwen2.5-coder:0.5b";         Name="Qwen Coder 0.5B";     Category="Codigo, ultra ligero";   RamGB=2;  Check="qwen2.5-coder:0.5b" },
    @{ Tag="llama3.2:1b";                 Name="Llama 3.2 1B";        Category="Chat ligero";            RamGB=2;  Check="llama3.2:1b" },
    @{ Tag="qwen2.5-coder:1.5b";         Name="Qwen Coder 1.5B";     Category="Codigo, ligero";         RamGB=3;  Check="qwen2.5-coder:1.5b" },
    @{ Tag="llama3.2:3b";                 Name="Llama 3.2 3B";        Category="Chat general";           RamGB=5;  Check="llama3.2:3b" },
    @{ Tag="qwen2.5-coder:3b";           Name="Qwen Coder 3B";       Category="Codigo, equilibrado";    RamGB=5;  Check="qwen2.5-coder:3b" },
    @{ Tag="phi3.5:latest";               Name="Phi 3.5 Mini";        Category="Razonamiento";           RamGB=6;  Check="phi3.5" },
    @{ Tag="mistral:7b-instruct-q4_K_M"; Name="Mistral 7B Instruct"; Category="General, maduro";        RamGB=8;  Check="mistral:7b-instruct" },
    @{ Tag="qwen2.5-coder:7b";           Name="Qwen Coder 7B";       Category="Codigo, capaz";          RamGB=8;  Check="qwen2.5-coder:7b" },
    @{ Tag="llama3.1:8b";                 Name="Llama 3.1 8B";        Category="Multiproposito";         RamGB=8;  Check="llama3.1:8b" },
    @{ Tag="qwen2.5:14b";                 Name="Qwen 2.5 14B";        Category="Razonamiento avanzado";  RamGB=12; Check="qwen2.5:14b" },
    @{ Tag="mixtral:8x7b";               Name="Mixtral 8x7B";        Category="Top tier MoE";           RamGB=28; Check="mixtral:8x7b" }
)

Clear-Host
Write-Host ""
Write-Host "  =================================================" -ForegroundColor Cyan
Write-Host "  ||        Ge-mini  --  Instalador             ||" -ForegroundColor Cyan
Write-Host "  =================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Ge-mini se va a instalar en este equipo. El proceso es automatico:" -ForegroundColor Gray
Write-Host ""
Write-Host "    1. Prepara Python y el entorno aislado del proyecto." -ForegroundColor Gray
Write-Host "    2. Instala Ollama (motor de IA local)." -ForegroundColor Gray
Write-Host "    3. Detecta tu hardware y recomienda modelos adaptados." -ForegroundColor Gray
Write-Host "    4. Al final te pregunta si quieres usar tambien modelos cloud." -ForegroundColor Gray
Write-Host "    5. Arranca la aplicacion y abre tu navegador." -ForegroundColor Gray
Write-Host ""
Write-Host "  Puedes parar con Ctrl+C en cualquier momento." -ForegroundColor DarkGray
Write-Host ""

# -- Deteccion de RAM ----------------------------------------------------------
$ramBytes = (Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory
$RAM_GB = [math]::Round($ramBytes / 1GB)
$RAM_USABLE = $RAM_GB - 2
Write-Host "  RAM detectada: $RAM_GB GB  |  Usable para modelos: $RAM_USABLE GB" -ForegroundColor DarkGray
Write-Host ""

# =============================================================================
Write-Sep; Write-Host "  PASO 1/5 -- Entorno Python (uv)" -ForegroundColor White; Write-Sep

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

# =============================================================================
Write-Sep; Write-Host "  PASO 2/5 -- Ollama" -ForegroundColor White; Write-Sep

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
        Write-Warn "Ollama no responde. Los modelos locales no estaran disponibles."
    }
}

# =============================================================================
Write-Sep; Write-Host "  PASO 3/5 -- Modelos locales" -ForegroundColor White; Write-Sep
Write-Host "  RAM disponible para modelos: $RAM_USABLE GB (margen de 2 GB para el SO)" -ForegroundColor DarkGray
Write-Host ""

$installedNames = @()
if ($ollamaRunning) {
    try {
        $tags = Invoke-RestMethod "http://localhost:11434/api/tags" -TimeoutSec 5
        $installedNames = $tags.models | ForEach-Object { $_.name }
    } catch { }
}

function Is-Installed { param($check) return ($installedNames | Where-Object { $_ -like "*$check*" }).Count -gt 0 }

# -- Calcular recomendados (algoritmo D2 del design.md) -----------------------
function Compute-Recommended {
    param($catalog, $ramUsable)
    $eligible = @()
    for ($i = 0; $i -lt $catalog.Count; $i++) {
        if ($catalog[$i].RamGB -le $ramUsable) { $eligible += $i }
    }
    if ($eligible.Count -eq 0)   { return @(0) }
    if ($eligible.Count -le 3)   { return $eligible }
    $mid = [math]::Floor($eligible.Count / 2)
    return @($eligible[0], $eligible[$mid], $eligible[-1])
}
$recommended = Compute-Recommended $CATALOG $RAM_USABLE

# -- Mostrar tabla -------------------------------------------------------------
Write-Host "  [OK]=instalado [*]=recomendado [!]=excede tu RAM" -ForegroundColor DarkGray
Write-Host ""
Write-Host ("  {0,-4} {1,-22} {2,-22} {3,-7} {4}" -f "No.","Modelo","Uso","RAM","Estado")
Write-Host ("  {0,-4} {1,-22} {2,-22} {3,-7} {4}" -f "--","----------------------","----------------------","-------","------")

for ($i = 0; $i -lt $CATALOG.Count; $i++) {
    $m = $CATALOG[$i]
    $num = $i + 1
    if (Is-Installed $m.Check) {
        $statusText = "[OK]"; $statusColor = "Green"
    } elseif ($m.RamGB -gt $RAM_USABLE) {
        $statusText = "[!]"; $statusColor = "Yellow"
    } elseif ($recommended -contains $i) {
        $statusText = "[*]"; $statusColor = "Cyan"
    } else {
        $statusText = "[ ]"; $statusColor = "DarkGray"
    }
    Write-Host ("  [{0}] {1,-22} {2,-22} {3,-7} " -f $num, $m.Name, $m.Category, "$($m.RamGB) GB") -NoNewline
    Write-Host $statusText -ForegroundColor $statusColor
}

Write-Host ""
Write-Host "  Introduce numeros (ej: 1,3,5)  |  r=recomendados  |  t=todos  |  n=ninguno" -ForegroundColor DarkGray
$selection = Read-Host "  Tu seleccion"

$toDownload = @()
if ($selection -eq "" -or $selection -eq "r" -or $selection -eq "R") {
    $toDownload = $recommended
} elseif ($selection -eq "t" -or $selection -eq "T") {
    $toDownload = 0..($CATALOG.Count - 1)
} elseif ($selection -ne "n" -and $selection -ne "N") {
    $toDownload = $selection -split "," | ForEach-Object {
        $n = [int]$_.Trim() - 1
        if ($n -ge 0 -and $n -lt $CATALOG.Count) { $n }
        else { Write-Warn "Fuera de rango: $($_.Trim())" }
    } | Where-Object { $null -ne $_ }
}

Write-Host ""
$downloadedTags = @($installedNames | Where-Object { $_ })

foreach ($idx in $toDownload) {
    $m = $CATALOG[$idx]
    if (Is-Installed $m.Check) {
        Write-Ok "$($m.Name) ya descargado"
    } elseif (-not $ollamaRunning) {
        Write-Warn "Ollama no activo -- saltando $($m.Name)"
    } else {
        Write-Step "Descargando $($m.Name) ($($m.RamGB) GB recomendados)..."
        ollama pull $m.Tag
        if ($LASTEXITCODE -eq 0) { Write-Ok "$($m.Name) descargado"; $downloadedTags += $m.Tag }
        else { Write-Err "Fallo: $($m.Name)" }
    }
}

# -- Tags personalizados -------------------------------------------------------
Write-Host ""
Write-Host "  Tags personalizados (opcional)" -ForegroundColor White
Write-Host "  Cualquier tag de Ollama (ej: codellama:13b). Enter vacio para terminar." -ForegroundColor DarkGray
$customTags = @()
while ($true) {
    $ctag = Read-Host "  Tag"
    if ($ctag -eq "") { break }
    if ($ollamaRunning) {
        Write-Step "Descargando $ctag..."
        ollama pull $ctag
        if ($LASTEXITCODE -eq 0) { Write-Ok "$ctag descargado"; $customTags += $ctag }
        else { Write-Err "Fallo: $ctag" }
    }
}

# -- Estado a disco ------------------------------------------------------------
if (-not (Test-Path "data")) { New-Item -ItemType Directory "data" | Out-Null }
$allTags  = $CATALOG | ForEach-Object { $_.Tag }
$installed = $downloadedTags | Where-Object { $_ } | Select-Object -Unique
@{ installed = @($installed); available = @($allTags); custom = @($customTags) } |
    ConvertTo-Json -Depth 3 | Set-Content "data\installed_models.json" -Encoding UTF8
Write-Ok "Estado guardado en data\installed_models.json"

# =============================================================================
Write-Sep; Write-Host "  PASO 4/5 -- Modelos cloud (opcional)" -ForegroundColor White; Write-Sep

# -- Leer .env existente -------------------------------------------------------
$existingGemini = ""; $existingGroq = ""; $existingAnthropic = ""
if (Test-Path ".env") {
    $envContent = Get-Content ".env"
    foreach ($line in $envContent) {
        if ($line -match "^GEMINI_API_KEY=(.+)$")    { $existingGemini    = $Matches[1] }
        if ($line -match "^GROQ_API_KEY=(.+)$")      { $existingGroq      = $Matches[1] }
        if ($line -match "^ANTHROPIC_API_KEY=(.+)$") { $existingAnthropic = $Matches[1] }
    }
}

$cloudYes = Read-Host "  Quieres configurar modelos en la nube? (s/N)"

if ($cloudYes -eq "s" -or $cloudYes -eq "S") {
    Write-Host ""
    Write-Host "  Proveedores cloud disponibles:" -ForegroundColor White
    $g1 = if ($existingGemini)    { " [ya configurado]" } else { "" }
    $g2 = if ($existingGroq)      { " [ya configurado]" } else { "" }
    $g3 = if ($existingAnthropic) { " [ya configurado]" } else { "" }
    Write-Host "    [1] Google Gemini       $g1" -ForegroundColor Gray
    Write-Host "    [2] Groq (Llama)        $g2" -ForegroundColor Gray
    Write-Host "    [3] Anthropic (Claude)  $g3" -ForegroundColor Gray
    Write-Host ""
    $provs = Read-Host "  Selecciona (ej: 1,3)"

    $newGemini    = $existingGemini
    $newGroq      = $existingGroq
    $newAnthropic = $existingAnthropic

    function Read-ApiKey {
        param([string]$Label,[string]$Provider,[string]$Format,[string]$Url,[string]$Pattern,[scriptblock]$Ping)
        Write-Host ""
        Write-Host "  $Label" -ForegroundColor Yellow
        Write-Host "        Proveedor : $Provider"
        Write-Host "        Formato   : $Format"
        Write-Host "        Obtener en: $Url"
        while ($true) {
            $v = Read-Host "  > "
            if ($v -eq "") { Write-Warn "Omitida."; return "" }
            if (-not ($v -match $Pattern)) {
                Write-Warn "Formato incorrecto: $Format"
                Write-Host "  Enter para omitir o vuelve a intentarlo." -ForegroundColor DarkGray
                continue
            }
            Write-Step "Validando clave..."
            try {
                $ok = & $Ping $v
                if ($ok) { Write-Ok "Clave valida"; return $v }
                else {
                    Write-Warn "La clave parece invalida segun el proveedor."
                    $force = Read-Host "  Enter para guardarla igual, o vuelve a intentarlo."
                    if ($force -eq "") { return $v }
                }
            } catch {
                Write-Warn "No se pudo validar (sin conexion). Guardando tal como esta."
                return $v
            }
        }
    }

    function Ping-Gemini {
        param($key)
        try {
            $r = Invoke-WebRequest -Uri "https://generativelanguage.googleapis.com/v1beta/models?key=$key" -TimeoutSec 5 -UseBasicParsing
            return $r.StatusCode -eq 200
        } catch { return $false }
    }
    function Ping-Groq {
        param($key)
        try {
            $r = Invoke-WebRequest -Uri "https://api.groq.com/openai/v1/models" -Headers @{Authorization="Bearer $key"} -TimeoutSec 5 -UseBasicParsing
            return $r.StatusCode -eq 200
        } catch { return $false }
    }
    function Ping-Anthropic {
        param($key)
        try {
            $r = Invoke-WebRequest -Uri "https://api.anthropic.com/v1/models" -Headers @{"x-api-key"=$key;"anthropic-version"="2023-06-01"} -TimeoutSec 5 -UseBasicParsing
            return $r.StatusCode -eq 200
        } catch { return $false }
    }

    $provNums = $provs -split "," | ForEach-Object { $_.Trim() }
    foreach ($p in $provNums) {
        switch ($p) {
            "1" {
                if ($existingGemini) { Write-Ok "GEMINI ya configurado, omitido"; break }
                $newGemini = Read-ApiKey "GEMINI_API_KEY" "Google Gemini" "AIzaSy + 33 chars" "https://aistudio.google.com/app/apikey" "^AIzaSy[0-9A-Za-z_-]{33}$" { param($k) Ping-Gemini $k }
            }
            "2" {
                if ($existingGroq) { Write-Ok "GROQ ya configurado, omitido"; break }
                $newGroq = Read-ApiKey "GROQ_API_KEY" "Groq (Llama cloud)" "gsk_ + 52+ chars" "https://console.groq.com/keys" "^gsk_[0-9A-Za-z]{52,}$" { param($k) Ping-Groq $k }
            }
            "3" {
                if ($existingAnthropic) { Write-Ok "ANTHROPIC ya configurado, omitido"; break }
                Write-Host ""
                Write-Host "  [!!] Claude Opus 4.7 tiene coste alto por token (~`$15/M output)." -ForegroundColor Yellow
                Write-Host "    Revisa tu consola de Anthropic si planeas usarlo intensivamente." -ForegroundColor DarkGray
                $newAnthropic = Read-ApiKey "ANTHROPIC_API_KEY" "Anthropic (Claude)" "sk-ant- + 80+ chars" "https://console.anthropic.com/" "^sk-ant-[A-Za-z0-9_`-]{80,}$" { param($k) Ping-Anthropic $k }
            }
        }
    }

    # -- Regenerar .env --------------------------------------------------------
    $envLines = @("OLLAMA_BASE_URL=http://localhost:11434")
    if ($newGemini)    { $envLines += "GEMINI_API_KEY=$newGemini" }
    if ($newGroq)      { $envLines += "GROQ_API_KEY=$newGroq" }
    if ($newAnthropic) { $envLines += "ANTHROPIC_API_KEY=$newAnthropic" }
    $envLines | Set-Content ".env" -Encoding UTF8
    Write-Ok ".env actualizado"
} else {
    if (-not (Test-Path ".env")) {
        "OLLAMA_BASE_URL=http://localhost:11434" | Set-Content ".env" -Encoding UTF8
        Write-Ok ".env creado solo con Ollama"
    } else {
        Write-Ok ".env existente respetado"
    }
}

# =============================================================================
Write-Sep; Write-Host "  PASO 5/5 -- Base de datos y arranque" -ForegroundColor White; Write-Sep

Write-Step "Migraciones..."
& ".venv\Scripts\python.exe" -m alembic upgrade head
Write-Ok "Base de datos actualizada"

Write-Host ""
Write-Host "  =================================================" -ForegroundColor Green
Write-Host "  ||      [OK] Instalacion completada            ||" -ForegroundColor Green
Write-Host "  ||  http://127.0.0.1:8000/static/index.html  ||" -ForegroundColor Green
Write-Host "  ||  Futuros arranques: start.bat              ||" -ForegroundColor Green
Write-Host "  =================================================" -ForegroundColor Green
Write-Host ""

Start-Process "http://127.0.0.1:8000/static/index.html"
Start-Sleep 2
& ".venv\Scripts\python.exe" -m uvicorn app.main:app --port 8000
