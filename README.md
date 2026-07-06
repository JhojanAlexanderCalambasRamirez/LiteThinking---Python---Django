# LiteThinking — Prueba Técnica 2026

Aplicación full-stack empresarial: gestión de empresas, productos e inventario con Clean Architecture, microservicios FastAPI, búsqueda semántica vectorial y agente de lenguaje natural.

---

## Stack

| Capa | Tecnología |
|------|-----------|
| Frontend | Next.js 14, TypeScript, Tailwind CSS, TanStack Query |
| Backend principal | Django 5 + Django REST Framework |
| Microservicio inventario | FastAPI — PDF (ReportLab) + Email (SMTP/SendGrid) |
| Microservicio agente | FastAPI — LangChain + Groq + pgvector |
| Base de datos | PostgreSQL 18 + pgvector |
| Dominio | Python puro, Poetry — sin dependencias de framework |
| Autenticación | JWT (access 60min + refresh 7 días) |
| Hashing | Argon2 |

---

## Requisitos

- Python 3.11 – 3.13
- Node.js 18+
- PostgreSQL 15+ con extensión `pgvector`
- Poetry — instalar si no está:

```bash
curl -sSL https://install.python-poetry.org | python3 -
export PATH="$HOME/.local/bin:$PATH"
```

---

## Configuración inicial (una sola vez)

### 1. Variables de entorno

```bash
cp .env.example .env
```

Editar `.env` con los valores reales. Mínimo requerido:

```env
# Base de datos
DB_NAME=litethinking_db
DB_USER=tu_usuario_postgres      # en Mac con Homebrew: tu usuario del sistema
DB_PASSWORD=                     # vacío si usas autenticación por OS (trust)
DB_HOST=localhost
DB_PORT=5432
DATABASE_URL=postgresql://tu_usuario@localhost:5432/litethinking_db

# Django
DJANGO_SECRET_KEY=cambia-esto-por-una-clave-larga-y-aleatoria

# Agente IA — obtener gratis en console.groq.com (sin tarjeta)
GROQ_API_KEY=gsk_tu_clave_aqui
```

### 2. Base de datos

```bash
createdb litethinking_db
psql -d litethinking_db -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### 3. Dominio (paquete Python independiente)

```bash
cd domain
poetry install
cd ..
```

### 4. Backend Django

```bash
cd backend/django_core
poetry install
poetry run python manage.py migrate
poetry run python manage.py createsuperuser
# Ingresar: email=admin@litethinking.com / password=Admin1234!
cd ../..
```

### 5. Microservicio Inventario

```bash
cd backend/services/inventory_service
poetry install
cd ../../..
```

### 6. Microservicio Agente IA

```bash
cd backend/services/ai_agent
poetry install
# El modelo de embeddings (~200MB) se descarga automáticamente al primer uso
cd ../../..
```

### 7. Frontend

```bash
cd frontend
npm install
cd ..
```

---

## Ejecutar el proyecto

Abrir **4 terminales** (o usar tmux/iterm). Cada terminal desde la raíz del proyecto:

### Terminal 1 — Django API (puerto 8000)

```bash
cd backend/django_core
poetry run python manage.py runserver 0.0.0.0:8000
```

### Terminal 2 — Inventory Service (puerto 8001)

```bash
cd backend/services/inventory_service
poetry run uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### Terminal 3 — AI Agent Service (puerto 8002)

```bash
cd backend/services/ai_agent
poetry run uvicorn main:app --host 0.0.0.0 --port 8002 --reload
```

### Terminal 4 — Frontend Next.js (puerto 3000)

```bash
cd frontend
npm run dev
```

---

## URLs

| Servicio | URL |
|---------|-----|
| **Aplicación** | http://localhost:3000 |
| **Django API** | http://localhost:8000/api/v1/ |
| **Django Admin** | http://localhost:8000/admin/ |
| **Inventory Docs** | http://localhost:8001/docs |
| **AI Agent Docs** | http://localhost:8002/docs |

---

## Credenciales por defecto

```
Email:    admin@litethinking.com
Password: Admin1234!
Rol:      Administrador (acceso completo)
```

---

## Flujo de uso

### 1. Login
Ir a http://localhost:3000 → ingresar credenciales → redirige al dashboard.

### 2. Empresas
- **Admin**: crear, editar, eliminar empresas
- **Externo**: solo visualizar
- NIT editable en cualquier momento; el cambio se propaga automáticamente a todos los productos asociados (ON UPDATE CASCADE)

### 3. Productos
- Crear producto con código, nombre, características y precios en múltiples monedas (COP, USD, EUR, etc.)
- Al guardar, el embedding semántico se genera automáticamente para el agente IA

### 4. Inventario
- Ver productos agrupados por empresa
- **Exportar PDF**: genera un PDF con la tabla completa
- **Enviar por email**: adjunta el PDF y lo envía al correo indicado (requiere SMTP configurado)

### 5. Agente IA
- Chat en lenguaje natural: "¿Qué laptops tienen más de 16GB RAM?"
- El agente busca productos por similitud semántica usando pgvector
- Responde en español con los productos más relevantes

---

## API REST — Endpoints principales

### Auth
```
POST /api/v1/auth/login/       → { email, password } → { access, refresh }
POST /api/v1/auth/refresh/     → { refresh } → { access }
```

### Empresas
```
GET    /api/v1/empresas/           → listar
POST   /api/v1/empresas/           → crear (admin)
GET    /api/v1/empresas/{nit}/     → detalle
PUT    /api/v1/empresas/{nit}/     → editar (admin)
DELETE /api/v1/empresas/{nit}/     → eliminar/desactivar (admin)
```

### Productos
```
GET    /api/v1/productos/          → listar (filtrar: ?empresa=NIT)
POST   /api/v1/productos/          → crear con precios (admin)
GET    /api/v1/productos/{id}/     → detalle
PUT    /api/v1/productos/{id}/     → editar (admin)
DELETE /api/v1/productos/{id}/     → desactivar (admin)
GET    /api/v1/monedas/            → listar monedas ISO 4217
```

### Inventario
```
GET    /api/v1/inventario/                → listar (filtrar: ?empresa=NIT)
POST   /api/v1/inventario/               → agregar stock (admin)
PATCH  /api/v1/inventario/{id}/          → actualizar cantidad
POST   /api/v1/inventario/export-pdf/    → generar PDF
POST   /api/v1/inventario/export-email/  → enviar PDF por email
```

### Agente IA (puerto 8002)
```
POST /api/v1/agent/query/              → consulta en lenguaje natural
POST /api/v1/agent/search/             → búsqueda semántica directa
POST /api/v1/agent/embeddings/upsert/  → indexar producto manualmente
```

---

## Roles

| Rol | Acceso |
|-----|--------|
| **admin** | CRUD completo: empresas, productos, inventario, exportación |
| **externo** | Solo lectura: ver empresas |

---

## Validaciones de NIT

El NIT colombiano se valida en 4 capas:

1. **Frontend (Zod)**: regex antes de enviar el formulario
2. **Domain VO**: `NIT` value object inmutable con `InvalidNITError`
3. **DRF Serializer**: `validate_nit()` con mensaje descriptivo; bloquea cambio de NIT si la empresa tiene productos asociados
4. **DB CHECK CONSTRAINT**: `chk_empresa_nit_format` — última barrera

Formato válido: `^\d{6,10}(-\d)?$`
- `900123456` → válido
- `900123456-7` → válido
- `12345` → rechazado (muy corto)
- `ABC12345` → rechazado (letras)

El NIT puede editarse mientras la empresa no tenga productos asociados.

---

## Docker (alternativa)

```bash
# Levantar todos los servicios con Docker
docker-compose up --build

# Solo la base de datos
docker-compose up db
```

---

## Tests del dominio

```bash
cd domain
poetry run pytest -v
```

---

## Estructura del proyecto

```
LiteThinking-Python-React/
├── domain/                          # Paquete Python independiente (Poetry)
│   └── src/litethinking_domain/
│       ├── entities/                # Empresa, Producto, Usuario, Inventario
│       ├── value_objects/           # NIT, Money, EmailAddress, PasswordHash
│       ├── repositories/            # Interfaces ABC (puertos)
│       └── exceptions/              # Errores de dominio tipados
│
├── backend/
│   ├── django_core/                 # API principal (puerto 8000)
│   │   └── apps/
│   │       ├── users/               # Auth JWT, roles, modelo custom
│   │       ├── companies/           # CRUD empresas + constraints NIT
│   │       ├── products/            # CRUD productos, precios multi-moneda
│   │       └── inventory/           # Stock, exportación PDF/email
│   │
│   └── services/
│       ├── inventory_service/       # FastAPI PDF + email (puerto 8001)
│       └── ai_agent/                # FastAPI LangChain + pgvector (puerto 8002)
│
├── frontend/                        # Next.js 14 — Atomic Design
│   └── src/
│       ├── app/                     # App Router: login, empresas, productos,
│       │                            #             inventario, agente
│       ├── components/
│       │   ├── atoms/               # Button, Input, Label, Spinner, Badge
│       │   ├── molecules/           # FormField, CurrencyDisplay
│       │   ├── organisms/           # LoginForm, CompanyForm, CompanyTable, Navbar
│       │   └── templates/           # AuthTemplate, DashboardTemplate
│       └── lib/                     # api.ts (axios + JWT interceptor), auth.ts
│
└── database/
    ├── migrations/V1__initial_schema.sql
    └── seeds/V2__seed_data.sql
```

---

## Autor

**Jhojan Alexander Calamabas Ramírez**
