# LiteThinking — Prueba Técnica 2026

Aplicación full-stack empresarial desarrollada como prueba técnica para **LiteThinking**. Implementa gestión de empresas, productos e inventario con arquitectura limpia, microservicios y búsqueda semántica vectorial.

---

## Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind CSS, TanStack Query |
| Backend principal | Django 5 + Django REST Framework |
| Microservicio inventario | FastAPI + ReportLab + SMTP/SendGrid |
| Microservicio agente | FastAPI + LangChain + Anthropic + pgvector |
| Base de datos | PostgreSQL 18 + pgvector |
| Dominio | Python puro (Poetry) — sin dependencias de framework |
| Autenticación | JWT (SimpleJWT) — Access 60min + Refresh 7 días |
| Hashing | Argon2 (bcrypt fallback) |
| ORM | Django ORM (core) + SQLAlchemy (microservicios) |

---

## Arquitectura

El proyecto sigue **Clean Architecture** con separación estricta de capas:

```
┌─────────────────────────────────────────────┐
│                  FRONTEND                    │
│         Next.js 14 — Atomic Design           │
│  atoms → molecules → organisms → templates  │
└──────────────────┬──────────────────────────┘
                   │ HTTP / JWT
┌──────────────────▼──────────────────────────┐
│            APLICACIÓN / API                  │
│     Django 5 + DRF  (puerto 8000)           │
│  users | companies | products | inventory   │
└────────┬──────────────────┬─────────────────┘
         │ httpx             │ httpx
┌────────▼────────┐  ┌──────▼──────────────────┐
│ inventory_svc   │  │      ai_agent_svc        │
│  FastAPI :8001  │  │     FastAPI :8002        │
│  PDF + Email    │  │  LangChain + pgvector    │
└─────────────────┘  └──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│              DOMINIO (Python puro)           │
│     litethinking-domain  (Poetry pkg)        │
│  Entities | Value Objects | Repositories     │
│  Empresa | Producto | Usuario | Inventario  │
│  NIT | Money | EmailAddress | PasswordHash  │
└─────────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│           INFRAESTRUCTURA                    │
│     PostgreSQL 18 + pgvector extension       │
└─────────────────────────────────────────────┘
```

### Capa de Dominio (independiente)

La capa de dominio es un **paquete Python instalable via Poetry** (`litethinking-domain`) sin dependencias de framework. Contiene:

- **Entidades**: `Empresa`, `Producto`, `Usuario`, `Inventario` — dataclasses con lógica de negocio pura
- **Value Objects**: `NIT`, `Money`, `EmailAddress`, `PasswordHash` — inmutables, con validación
- **Repositorios**: Interfaces ABC (puertos) — implementadas por Django ORM e SQLAlchemy
- **Excepciones**: Jerarquía tipada de errores de dominio

---

## Estructura del Proyecto

```
LiteThinking-Python-React/
│
├── domain/                          # Paquete de dominio (Poetry)
│   ├── pyproject.toml
│   └── src/litethinking_domain/
│       ├── entities/                # Empresa, Producto, Usuario, Inventario
│       ├── value_objects/           # NIT, Money, EmailAddress, PasswordHash
│       ├── repositories/            # Interfaces ABC (puertos)
│       └── exceptions/              # Excepciones de dominio tipadas
│
├── backend/
│   ├── django_core/                 # API principal Django + DRF
│   │   ├── apps/
│   │   │   ├── users/               # Modelo usuario custom, JWT, roles
│   │   │   ├── companies/           # CRUD empresas, repositorio Django
│   │   │   ├── products/            # CRUD productos, precios multi-moneda
│   │   │   └── inventory/           # Inventario, delegación a microservicios
│   │   └── config/
│   │       ├── settings/            # base / development / production / testing
│   │       └── urls.py
│   │
│   └── services/
│       ├── inventory_service/       # FastAPI: generación PDF, envío email
│       │   ├── routers/
│       │   └── services/            # pdf_service.py, email_service.py
│       │
│       └── ai_agent/                # FastAPI: agente semántico + blockchain
│           ├── routers/
│           └── services/            # embedding_service.py, langchain_agent.py,
│                                    # blockchain_service.py
│
├── frontend/                        # Next.js 14 — App Router + Atomic Design
│   └── src/
│       ├── app/
│       │   ├── (auth)/login/        # Vista inicio de sesión
│       │   └── (dashboard)/
│       │       ├── empresas/        # CRUD empresas
│       │       ├── productos/       # CRUD productos + precios multi-moneda
│       │       ├── inventario/      # Tabla + exportar PDF + enviar email
│       │       └── agente/          # Chat con agente semántico
│       ├── components/
│       │   ├── atoms/               # Button, Input, Label, Spinner, Badge
│       │   ├── molecules/           # FormField, CurrencyDisplay
│       │   ├── organisms/           # LoginForm, CompanyForm, CompanyTable, Navbar
│       │   └── templates/           # AuthTemplate, DashboardTemplate
│       ├── lib/                     # api.ts (axios + JWT), auth.ts
│       └── types/                   # Tipos TypeScript globales
│
└── database/
    ├── migrations/V1__initial_schema.sql   # Schema completo con constraints
    └── seeds/V2__seed_data.sql             # Monedas ISO 4217
```

---

## Requisitos Previos

- **Python** 3.11 – 3.13
- **Node.js** 18+
- **PostgreSQL** 15+ con extensión `pgvector`
- **Poetry** (`curl -sSL https://install.python-poetry.org | python3 -`)

---

## Instalación y Configuración

### 1. Variables de entorno

```bash
cp .env.example .env
# Editar .env con tus valores
```

Variables críticas:

```env
DB_NAME=litethinking_db
DB_USER=tu_usuario_postgres
DB_PASSWORD=tu_password
DATABASE_URL=postgresql://tu_usuario@localhost:5432/litethinking_db

DJANGO_SECRET_KEY=genera-una-clave-secreta-larga

ANTHROPIC_API_KEY=sk-ant-tu-clave-aqui   # Para el agente semántico

EMAIL_BACKEND=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu@gmail.com
SMTP_PASSWORD=tu_app_password
```

### 2. Base de datos

```bash
# Crear base de datos
createdb litethinking_db

# Habilitar pgvector
psql -d litethinking_db -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### 3. Dominio (capa independiente)

```bash
cd domain
poetry install
poetry run pytest        # Ejecutar tests unitarios del dominio
cd ..
```

### 4. Backend Django

```bash
cd backend/django_core
poetry install
poetry run python manage.py migrate
poetry run python manage.py createsuperuser
# Email: admin@litethinking.com  |  Password: Admin1234!
poetry run python manage.py runserver 0.0.0.0:8000
```

### 5. Microservicio Inventario

```bash
cd backend/services/inventory_service
poetry install
poetry run uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### 6. Microservicio Agente

```bash
cd backend/services/ai_agent
poetry install
# El modelo de embeddings (~200MB) se descarga automáticamente al primer uso
poetry run uvicorn main:app --host 0.0.0.0 --port 8002 --reload
```

### 7. Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## Servicios y Puertos

| Servicio | URL | Descripción |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | Next.js — interfaz de usuario |
| Django API | http://localhost:8000 | REST API principal |
| Django Admin | http://localhost:8000/admin/ | Panel de administración |
| Inventory Service | http://localhost:8001/docs | FastAPI — PDF + email |
| AI Agent Service | http://localhost:8002/docs | FastAPI — agente semántico |

---

## API Endpoints Principales

### Autenticación
```
POST /api/v1/auth/login/       → Obtener access + refresh token
POST /api/v1/auth/refresh/     → Renovar access token
```

### Empresas
```
GET    /api/v1/empresas/           → Listar empresas
POST   /api/v1/empresas/           → Crear empresa (admin)
GET    /api/v1/empresas/{nit}/     → Detalle empresa
PUT    /api/v1/empresas/{nit}/     → Actualizar empresa (admin)
DELETE /api/v1/empresas/{nit}/     → Soft delete empresa (admin)
```

### Productos
```
GET    /api/v1/productos/          → Listar productos
POST   /api/v1/productos/          → Crear producto con precios (admin)
PUT    /api/v1/productos/{id}/     → Actualizar producto (admin)
DELETE /api/v1/productos/{id}/     → Soft delete producto (admin)
```

### Inventario
```
GET    /api/v1/inventario/         → Listar inventario (filtrable por empresa)
POST   /api/v1/inventario/         → Agregar al inventario (admin)
PATCH  /api/v1/inventario/{id}/    → Actualizar cantidad
POST   /api/v1/inventario/export-pdf/      → Exportar PDF (vía microservicio)
POST   /api/v1/inventario/export-email/    → Enviar PDF por email
```

### Monedas
```
GET /api/v1/monedas/               → Listar monedas ISO 4217 disponibles
```

---

## Roles de Usuario

| Rol | Permisos |
|-----|---------|
| **Administrador** | CRUD completo: empresas, productos, inventario |
| **Externo** | Solo lectura: visualizar empresas |

Credenciales por defecto (desarrollo):
- Email: `admin@litethinking.com`
- Password: `Admin1234!`

---

## Modelo de Base de Datos

```
empresa          → producto (RESTRICT delete, CASCADE update NIT)
producto         → producto_precio (multi-moneda, CASCADE delete)
producto_precio  → moneda (RESTRICT delete)
producto         → inventario (RESTRICT delete, UNIQUE por producto)
usuario          → inventario (created_by, SET NULL on delete)
producto         → producto_embedding (CASCADE delete, vector 384 dims)
empresa          → email_log (SET NULL on delete)
```

**Restricciones de integridad:**
- NIT formato colombiano: `^\d{6,10}(-\d)?$`
- Email formato válido con regex
- Password hash validado (nunca texto plano)
- Precios `NUMERIC(18,4)` — nunca `FLOAT`
- Stock `>= 0` enforced a nivel DB
- Monedas `UPPERCASE` ISO 4217
- Soft delete en todas las entidades

---

## Funcionalidad de Exportación

La vista de **Inventario** permite:
1. **Descargar PDF**: Generado por `inventory_service` con ReportLab — tabla con productos, empresa, precios y cantidades
2. **Enviar por email**: El PDF se adjunta y envía al destinatario indicado via SMTP o SendGrid

---

## Agente Semántico

La vista **Agente** expone un chat que permite consultas en lenguaje natural sobre el inventario:

- **Embeddings**: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (384 dims, local, sin costo de API)
- **Vector DB**: PostgreSQL con `pgvector`, índice `IVFFlat` para búsqueda coseno eficiente
- **LLM**: Anthropic Claude via LangChain (`create_tool_calling_agent`)
- **Herramienta**: `buscar_productos` — búsqueda semántica en tiempo real sobre embeddings almacenados
- **Blockchain**: Registro SHA256 de operaciones críticas en `blockchain_log` (Polygon Mumbai opcional)

---

## Docker (opcional)

```bash
docker-compose up --build
```

El `docker-compose.yml` levanta los 5 servicios: PostgreSQL, Django, inventory_service, ai_agent y frontend.

---

## Tests

```bash
# Tests del dominio (entidades y value objects)
cd domain && poetry run pytest -v

# Tests Django
cd backend/django_core && poetry run python manage.py test
```

---

## Despliegue con Docker

Cada servicio tiene su propio `Dockerfile`. El `docker-compose.yml` coordina:
- Healthchecks entre servicios
- Variables de entorno desde `.env`
- Red interna `litethinking_network`
- Volumen persistente para PostgreSQL

---

## Autor

**Jhojan Alexander Calamabas Ramírez**
