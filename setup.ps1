# =============================================================================
# LiteThinking 2026 — Full provisioning script for Windows
# Requires: Windows 10/11, PowerShell 5.1+, winget (pre-installed on Win 11)
#
# Usage (run once to allow scripts):
#   Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force
#   .\setup.ps1
# =============================================================================

#Requires -Version 5.1
$ErrorActionPreference = "Stop"

# ── Helpers ───────────────────────────────────────────────────────────────────
function Step   { param($n, $msg) Write-Host "`n━━━  $n  $msg" -ForegroundColor White }
function Info   { param($msg) Write-Host "[INFO]  $msg" -ForegroundColor Cyan }
function Ok     { param($msg) Write-Host "[OK]    $msg" -ForegroundColor Green }
function Warn   { param($msg) Write-Host "[WARN]  $msg" -ForegroundColor Yellow }
function Fail   { param($msg) Write-Host "[ERROR] $msg" -ForegroundColor Red; exit 1 }

function Install-Winget-Package {
    param([string]$Id, [string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        Info "Installing $Id via winget..."
        winget install --id $Id --silent --accept-source-agreements --accept-package-agreements
    } else {
        Info "$Name already installed — skipping"
    }
}

function Refresh-Path {
    $env:PATH = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                [System.Environment]::GetEnvironmentVariable("Path", "User")
}

$RootDir = $PSScriptRoot

# =============================================================================
# STEP 1 — winget check
# =============================================================================
Step "1/8" "Checking winget"

if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    Fail "winget not found. Install App Installer from the Microsoft Store: https://apps.microsoft.com/detail/9NBLGGH4NNS1"
}
Ok "winget available"

# =============================================================================
# STEP 2 — System packages
# =============================================================================
Step "2/8" "System packages"

Install-Winget-Package "Python.Python.3.13"  "python"
Install-Winget-Package "OpenJS.NodeJS.LTS"   "node"
Install-Winget-Package "PostgreSQL.PostgreSQL" "psql"

Refresh-Path

# Locate PostgreSQL bin dir
$pgBin = (Get-ChildItem "C:\Program Files\PostgreSQL" -ErrorAction SilentlyContinue |
    Sort-Object Name -Descending | Select-Object -First 1)
if ($pgBin) {
    $pgBinPath = Join-Path $pgBin.FullName "bin"
    $env:PATH = "$pgBinPath;$env:PATH"
    $PgVersion = $pgBin.Name
} else {
    Fail "PostgreSQL not found in 'C:\Program Files\PostgreSQL'. Install it manually and re-run."
}
Ok "PostgreSQL $PgVersion found at $pgBinPath"

# =============================================================================
# STEP 3 — pgvector
# =============================================================================
Step "3/8" "pgvector extension"

$PgShareDir = Join-Path "C:\Program Files\PostgreSQL\$PgVersion" "share\extension"
$pgvectorInstalled = Test-Path (Join-Path $PgShareDir "vector.control")

if (-not $pgvectorInstalled) {
    Info "Downloading pgvector for PostgreSQL $PgVersion..."
    $pgvectorUrl = "https://github.com/pgvector/pgvector/releases/latest/download/pgvector-pg$PgVersion-windows-x86_64.zip"
    $zipPath = "$env:TEMP\pgvector.zip"
    $extractPath = "$env:TEMP\pgvector"

    try {
        Invoke-WebRequest -Uri $pgvectorUrl -OutFile $zipPath -UseBasicParsing
        Expand-Archive -Path $zipPath -DestinationPath $extractPath -Force

        $libDir    = Join-Path "C:\Program Files\PostgreSQL\$PgVersion" "lib"
        $shareDir  = Join-Path "C:\Program Files\PostgreSQL\$PgVersion" "share\extension"
        $binDir    = $pgBinPath

        Copy-Item "$extractPath\*.dll"     $libDir    -Force -ErrorAction SilentlyContinue
        Copy-Item "$extractPath\*.so"      $libDir    -Force -ErrorAction SilentlyContinue
        Copy-Item "$extractPath\*.control" $shareDir  -Force -ErrorAction SilentlyContinue
        Copy-Item "$extractPath\*.sql"     $shareDir  -Force -ErrorAction SilentlyContinue
        Ok "pgvector installed"
    } catch {
        Warn "Automatic pgvector install failed. Download manually from:"
        Warn "  https://github.com/pgvector/pgvector/releases"
        Warn "  Copy .dll to 'lib\' and .control/.sql to 'share\extension\' in your PostgreSQL directory."
        Read-Host "Press ENTER to continue without pgvector (AI agent won't work)"
    }
} else {
    Info "pgvector already installed — skipping"
}

# =============================================================================
# STEP 4 — Poetry
# =============================================================================
Step "4/8" "Poetry"

if (-not (Get-Command poetry -ErrorAction SilentlyContinue)) {
    Info "Installing Poetry..."
    (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
    $env:PATH = "$env:APPDATA\Python\Scripts;$env:PATH"
}
poetry --version | Out-Null
Ok "Poetry ready"

# =============================================================================
# STEP 5 — Environment variables
# =============================================================================
Step "5/8" "Environment variables (.env)"

$envFile = Join-Path $RootDir ".env"
$envExample = Join-Path $RootDir ".env.example"

if (-not (Test-Path $envFile)) {
    Copy-Item $envExample $envFile
    Warn ".env created from .env.example"
    Write-Host ""
    Write-Host "  Fill in these required values in .env:" -ForegroundColor Yellow
    Write-Host "    DB_USER         — your PostgreSQL username (usually 'postgres')"
    Write-Host "    DB_PASSWORD     — your PostgreSQL password"
    Write-Host "    DATABASE_URL    — postgresql://USER:PASS@localhost:5432/litethinking_db"
    Write-Host "    DJANGO_SECRET_KEY — any long random string"
    Write-Host "    GROQ_API_KEY    — free at console.groq.com  (needed for AI agent)"
    Write-Host ""
    notepad $envFile
    Read-Host "Press ENTER when you have saved .env to continue"
} else {
    Info ".env already exists — skipping"
}

# Load .env values into current session
Get-Content $envFile | Where-Object { $_ -match "^\s*[^#]" -and $_ -match "=" } | ForEach-Object {
    $parts = $_ -split "=", 2
    [System.Environment]::SetEnvironmentVariable($parts[0].Trim(), $parts[1].Trim(), "Process")
}
$DbName = $env:DB_NAME ?? "litethinking_db"
$DbUser = $env:DB_USER ?? "postgres"

Ok ".env loaded"

# =============================================================================
# STEP 6 — Database
# =============================================================================
Step "6/8" "Database"

# Create DB (ignore error if exists)
$createResult = & psql -U $DbUser -c "SELECT 1 FROM pg_database WHERE datname='$DbName'" postgres 2>&1
if ($createResult -notmatch "1 row") {
    Info "Creating database '$DbName'..."
    & createdb -U $DbUser $DbName
    Ok "Database created"
} else {
    Info "Database '$DbName' already exists — skipping"
}

Set-Location (Join-Path $RootDir "backend\django_core")

Info "Running Django migrations (ORM tables)..."
poetry run python manage.py migrate --no-input
Ok "Django migrations applied"

Info "Creating extra tables (blockchain_log, producto_embedding, email_log)..."
$v3 = Join-Path $RootDir "database\migrations\V3__extra_tables.sql"
& psql -U $DbUser -d $DbName -f $v3 -q
Ok "Extra tables created"

Info "Seeding currencies and sample company..."
$v2 = Join-Path $RootDir "database\seeds\V2__seed_data.sql"
& psql -U $DbUser -d $DbName -f $v2 -q
Ok "Seed data applied"

Info "Creating default users (admin + externo)..."
poetry run python manage.py seed_users
Ok "Default users created"

Set-Location $RootDir

# =============================================================================
# STEP 7 — Python microservices
# =============================================================================
Step "7/8" "Python microservices"

Set-Location (Join-Path $RootDir "domain")
poetry install --no-interaction -q
Ok "Domain package installed"

Set-Location (Join-Path $RootDir "backend\services\inventory_service")
poetry install --no-interaction -q
Ok "Inventory service installed"

Set-Location (Join-Path $RootDir "backend\services\ai_agent")
poetry install --no-interaction -q
Ok "AI agent installed"

Set-Location $RootDir

# =============================================================================
# STEP 8 — Frontend
# =============================================================================
Step "8/8" "Frontend"

Set-Location (Join-Path $RootDir "frontend")
npm install --silent
Ok "Frontend dependencies installed"

Set-Location $RootDir

# =============================================================================
# Done
# =============================================================================
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host "  LiteThinking 2026 is ready!" -ForegroundColor Green
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host ""
Write-Host "  Start the project — open 4 terminals:" -ForegroundColor White
Write-Host ""
Write-Host "  # Terminal 1 — Django API (port 8000)" -ForegroundColor Cyan
Write-Host "  cd backend\django_core; poetry run python manage.py runserver"
Write-Host ""
Write-Host "  # Terminal 2 — Inventory Service (port 8001)" -ForegroundColor Cyan
Write-Host "  cd backend\services\inventory_service; poetry run uvicorn main:app --port 8001 --reload"
Write-Host ""
Write-Host "  # Terminal 3 — AI Agent (port 8002)" -ForegroundColor Cyan
Write-Host "  cd backend\services\ai_agent; poetry run uvicorn main:app --port 8002 --reload"
Write-Host ""
Write-Host "  # Terminal 4 — Frontend Next.js (port 3000)" -ForegroundColor Cyan
Write-Host "  cd frontend; npm run dev"
Write-Host ""
Write-Host "  Credentials:" -ForegroundColor White
Write-Host "    Admin:   admin@litethinking.com   / Admin1234!"
Write-Host "    Externo: externo@litethinking.com / Externo1234!"
Write-Host ""
Write-Host "  App: http://localhost:3000" -ForegroundColor White
Write-Host ""
