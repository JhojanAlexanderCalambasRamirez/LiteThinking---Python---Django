#!/usr/bin/env bash
# =============================================================================
# LiteThinking 2026 — Full provisioning script
# Supports: macOS (Homebrew) | Ubuntu/Debian (apt)
# Usage:  bash setup.sh
# =============================================================================

set -euo pipefail

# ── Colors ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

info()    { echo -e "${CYAN}[INFO]${RESET}  $*"; }
success() { echo -e "${GREEN}[OK]${RESET}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${RESET}  $*"; }
error()   { echo -e "${RED}[ERROR]${RESET} $*"; exit 1; }
step()    { echo -e "\n${BOLD}━━━  $* ${RESET}"; }

# ── Detect OS ─────────────────────────────────────────────────────────────────
OS="unknown"
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ -f /etc/debian_version ]]; then
    OS="debian"
else
    error "OS not supported. Run on macOS or Ubuntu/Debian."
fi
info "Detected OS: $OS"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

# =============================================================================
# STEP 1 — System dependencies
# =============================================================================
step "1/8  System dependencies"

if [[ "$OS" == "macos" ]]; then
    if ! command -v brew &>/dev/null; then
        info "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        eval "$(/opt/homebrew/bin/brew shellenv 2>/dev/null || /usr/local/bin/brew shellenv)"
    fi
    success "Homebrew ready"

    info "Installing system packages (python, node, postgresql, pgvector)..."
    brew install python@3.13 node@20 postgresql@17 pgvector 2>/dev/null || true
    brew link --overwrite python@3.13 node@20 postgresql@17 2>/dev/null || true

    # Start PostgreSQL
    brew services start postgresql@17 2>/dev/null || brew services restart postgresql@17 2>/dev/null || true
    export PATH="$(brew --prefix postgresql@17)/bin:$PATH"

elif [[ "$OS" == "debian" ]]; then
    info "Updating apt..."
    sudo apt-get update -qq

    info "Installing system packages..."
    sudo apt-get install -y -qq \
        python3.11 python3.11-venv python3-pip \
        nodejs npm \
        postgresql postgresql-contrib \
        curl build-essential

    # pgvector for Debian/Ubuntu
    PG_VERSION=$(pg_config --version | grep -oP '\d+' | head -1)
    sudo apt-get install -y -qq "postgresql-${PG_VERSION}-pgvector" 2>/dev/null || {
        warn "pgvector not in apt. Building from source..."
        sudo apt-get install -y -qq git make gcc postgresql-server-dev-${PG_VERSION}
        tmp=$(mktemp -d)
        git clone --depth 1 https://github.com/pgvector/pgvector.git "$tmp/pgvector"
        pushd "$tmp/pgvector"
        make && sudo make install
        popd
    }

    sudo systemctl enable postgresql --now
fi
success "System packages installed"

# =============================================================================
# STEP 2 — Poetry
# =============================================================================
step "2/8  Poetry"

if ! command -v poetry &>/dev/null; then
    info "Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
fi

# Ensure poetry is on PATH for rest of script
export PATH="$HOME/.local/bin:$PATH"
poetry --version
success "Poetry ready"

# =============================================================================
# STEP 3 — Environment variables
# =============================================================================
step "3/8  Environment variables (.env)"

if [[ ! -f "$ROOT_DIR/.env" ]]; then
    cp "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
    warn ".env created from .env.example"
    echo ""
    echo -e "${YELLOW}  Fill in these required values in .env before continuing:${RESET}"
    echo "    DB_USER        — your PostgreSQL username (usually 'postgres' or your OS user)"
    echo "    DB_PASSWORD    — your PostgreSQL password (can be empty for local trust auth)"
    echo "    DATABASE_URL   — postgresql://USER:PASS@localhost:5432/litethinking_db"
    echo "    DJANGO_SECRET_KEY — any long random string"
    echo "    GROQ_API_KEY   — free at console.groq.com  (needed for the AI agent)"
    echo ""
    read -rp "  Press ENTER when you have edited .env to continue... "
else
    info ".env already exists — skipping"
fi

# Source the .env so subsequent commands can use DB vars
set -a; source "$ROOT_DIR/.env"; set +a

success ".env loaded"

# =============================================================================
# STEP 4 — Database
# =============================================================================
step "4/8  Database"

DB_NAME="${DB_NAME:-litethinking_db}"
DB_USER="${DB_USER:-postgres}"

# Create DB (ignore error if already exists)
createdb -U "$DB_USER" "$DB_NAME" 2>/dev/null && success "Database '$DB_NAME' created" \
    || info "Database '$DB_NAME' already exists — skipping"

success "Database ready"

# =============================================================================
# STEP 5 — Python dependencies
# =============================================================================
step "5/8  Python dependencies"

info "Installing domain package..."
cd "$ROOT_DIR/domain"
poetry install --no-interaction -q
success "Domain installed"

info "Installing Django backend..."
cd "$ROOT_DIR/backend/django_core"
poetry install --no-interaction -q
success "Django backend installed"

info "Installing inventory microservice..."
cd "$ROOT_DIR/backend/services/inventory_service"
poetry install --no-interaction -q
success "Inventory service installed"

info "Installing AI agent microservice..."
cd "$ROOT_DIR/backend/services/ai_agent"
poetry install --no-interaction -q
success "AI agent installed"

cd "$ROOT_DIR"

# =============================================================================
# STEP 6 — Database schema & seed
# =============================================================================
step "6/8  Database schema & seed"

DJANGO_PYTHON="$ROOT_DIR/backend/django_core"

info "Running Django migrations (ORM tables)..."
cd "$ROOT_DIR/backend/django_core"
poetry run python manage.py migrate --no-input
success "Django migrations applied"

info "Creating extra tables (blockchain_log, producto_embedding, email_log)..."
psql -U "$DB_USER" -d "$DB_NAME" -f "$ROOT_DIR/database/migrations/V3__extra_tables.sql" -q
success "Extra tables created"

info "Seeding currencies and sample company..."
psql -U "$DB_USER" -d "$DB_NAME" -f "$ROOT_DIR/database/seeds/V2__seed_data.sql" -q
success "Seed data applied"

info "Creating default users (admin + externo)..."
poetry run python manage.py seed_users
success "Default users created"

cd "$ROOT_DIR"

# =============================================================================
# STEP 7 — Frontend
# =============================================================================
step "7/8  Frontend"

cd "$ROOT_DIR/frontend"
npm install --silent
success "Frontend dependencies installed"

cd "$ROOT_DIR"

# =============================================================================
# STEP 8 — Done
# =============================================================================
step "8/8  Setup complete"

echo ""
echo -e "${GREEN}${BOLD}  ✔  LiteThinking 2026 is ready!${RESET}"
echo ""
echo -e "${BOLD}  Start the project — open 4 terminals:${RESET}"
echo ""
echo -e "  ${CYAN}# Terminal 1 — Django API (port 8000)${RESET}"
echo "  cd backend/django_core && poetry run python manage.py runserver"
echo ""
echo -e "  ${CYAN}# Terminal 2 — Inventory Service (port 8001)${RESET}"
echo "  cd backend/services/inventory_service && poetry run uvicorn main:app --port 8001 --reload"
echo ""
echo -e "  ${CYAN}# Terminal 3 — AI Agent (port 8002)${RESET}"
echo "  cd backend/services/ai_agent && poetry run uvicorn main:app --port 8002 --reload"
echo ""
echo -e "  ${CYAN}# Terminal 4 — Frontend Next.js (port 3000)${RESET}"
echo "  cd frontend && npm run dev"
echo ""
echo -e "${BOLD}  Credentials:${RESET}"
echo "    Admin:   admin@litethinking.com   / Admin1234!"
echo "    Externo: externo@litethinking.com / Externo1234!"
echo ""
echo -e "${BOLD}  App:${RESET} http://localhost:3000"
echo ""
