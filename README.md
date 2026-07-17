# LiteThinking — Prueba Técnica 2026

Aplicación full-stack empresarial: gestión de empresas, productos e inventario con Clean Architecture, microservicios FastAPI, búsqueda semántica vectorial y auditoría blockchain.

---

## Demo en producción (AWS)

| Recurso            | Valor                                                                                |
|--------------------|--------------------------------------------------------------------------------------|
| URL pública HTTPS  | <https://100.57.100.132.nip.io>                                                      |
| Repositorio        | <https://github.com/JhojanAlexanderCalambasRamirez/LiteThinking---Python---Django>   |

```text
Admin:   admin@litethinking.com   / Admin1234!
Externo: externo@litethinking.com / Externo1234!
```

> Infraestructura: EC2 m7i-flex.large (8 GB RAM, 2 vCPU) + RDS PostgreSQL 16.4 — AWS us-east-1.
> No apagar la instancia para que los links permanezcan activos.

---

## Ramas

| Rama          | Propósito                                                                 |
|---------------|---------------------------------------------------------------------------|
| `main`        | Desarrollo local — configuración para `localhost`                         |
| `produccion`  | Despliegue AWS — HTTPS, cookies HTTP-safe, headers de seguridad, CSP      |

**Diferencias de `produccion` respecto a `main`:**

- Cookie `secure` condicional según protocolo (HTTP en local, HTTPS en producción)
- `NEXT_PUBLIC_API_URL` y `NEXT_PUBLIC_AI_AGENT_URL` apuntan al dominio HTTPS
- Headers de seguridad: `Content-Security-Policy`, `X-Frame-Options`, `COOP`, `CORP`, `Referrer-Policy`
- CSP `connect-src 'self'` (todo el tráfico pasa por nginx como reverse proxy)
- Auto-flush de precio no confirmado al crear producto (UX fix)

---

## Stack

| Capa | Descripcion |
| --- | --- |
| Frontend | Next.js 14, TypeScript, Tailwind CSS, TanStack Query, Atomic Design |
| Backend principal | Django 5 + Django REST Framework |
| Microservicio inventario | FastAPI — PDF (ReportLab) + Email (SMTP) |
| Microservicio agente | FastAPI — LangChain + Groq/Anthropic + pgvector |
| Base de datos | PostgreSQL + pgvector (embeddings vectoriales) |
| Dominio | Python puro, Poetry — sin dependencias de framework |
| Autenticacion | JWT (access 60 min + refresh 7 dias) + bcrypt |
| Blockchain | SHA-256 audit trail + web3.py (Polygon Mumbai ready) |
| Infraestructura AWS | EC2 m7i-flex.large, RDS PostgreSQL 16.4, nginx, PM2, systemd |

---

## Instalación rápida (desde cero)

Scripts de aprovisionamiento completo para equipos sin ningún prerequisito instalado.
Instalan Python, Node.js, PostgreSQL, pgvector, Poetry y configuran la base de datos automáticamente.

### macOS / Linux (Ubuntu · Debian)

```bash
bash setup.sh
```

### Windows 10 / 11

```powershell
# Ejecutar una vez para permitir scripts locales:
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force

.\setup.ps1
```

> **Nota Windows**: requiere **winget** (preinstalado en Windows 11; en Windows 10 instalar *App Installer* desde la Microsoft Store).

Ambos scripts:

1. Instalan Python 3.13, Node 20, PostgreSQL 17 y pgvector
2. Instalan Poetry
3. Crean `.env` desde `.env.example` y piden que lo edites (se abre automáticamente en Windows)
4. Crean la base de datos y corren todas las migraciones
5. Instalan dependencias Python y npm
6. Crean los usuarios por defecto (admin + externo)
7. Imprimen los comandos para levantar los 4 servicios

---

## Requisitos previos

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- pgvector — extensión PostgreSQL para embeddings vectoriales:
  - macOS: `brew install pgvector`
  - Ubuntu/Debian: `sudo apt install postgresql-15-pgvector`
- Poetry:

```bash
curl -sSL https://install.python-poetry.org | python3 -
export PATH="$HOME/.local/bin:$PATH"
```

---

## Instalación manual

### 1. Variables de entorno

```bash
cp .env.example .env
```

Edita `.env` con tus valores. Campos obligatorios:

```env
# Base de datos
DB_NAME=litethinking_db
DB_USER=tu_usuario_postgres
DB_PASSWORD=tu_password
DB_HOST=localhost
DB_PORT=5432
DATABASE_URL=postgresql://tu_usuario:tu_password@localhost:5432/litethinking_db

# Django
DJANGO_SECRET_KEY=cambia-esto-por-una-clave-larga-y-aleatoria

# Agente IA — pon al menos uno (GROQ es gratuito: console.groq.com)
GROQ_API_KEY=gsk_tu_clave_aqui
# ANTHROPIC_API_KEY=sk-ant-tu_clave_aqui

# Email PDF (opcional — sin esto el envío por email no funciona, el PDF sí)
# EMAIL_BACKEND=smtp
# SMTP_USER=tu_email@gmail.com
# SMTP_PASSWORD=tu_app_password
```

### 2. Base de datos

```bash
# Crear la base de datos
createdb litethinking_db

# Tablas gestionadas por Django ORM (empresa, usuario, producto, inventario…)
cd backend/django_core
poetry install
poetry run python manage.py migrate

# Tablas extra: blockchain_log, producto_embedding (pgvector), email_log
psql -U postgres -d litethinking_db -f ../../database/migrations/V3__extra_tables.sql

# Datos iniciales: monedas ISO 4217 + empresa de ejemplo
psql -U postgres -d litethinking_db -f ../../database/seeds/V2__seed_data.sql

# Usuarios por defecto (admin + externo)
poetry run python manage.py seed_users
cd ../..
```

### 3. Dominio (paquete Python independiente)

```bash
cd domain && poetry install && cd ..
```

### 4. Microservicio Inventario

```bash
cd backend/services/inventory_service && poetry install && cd ../../..
```

### 5. Microservicio Agente

```bash
cd backend/services/ai_agent && poetry install && cd ../../..
# El modelo de embeddings (~200MB) se descarga en el primer uso
```

### 6. Frontend

```bash
cd frontend && npm install && cd ..
```

---

## Ejecutar el proyecto

Abrir **4 terminales** desde la raíz del proyecto:

```bash
# T1 — Django API (puerto 8000)
cd backend/django_core && poetry run python manage.py runserver

# T2 — Inventory Service (puerto 8001)
cd backend/services/inventory_service && poetry run uvicorn main:app --port 8001 --reload

# T3 — AI Agent Service (puerto 8002)
cd backend/services/ai_agent && poetry run uvicorn main:app --port 8002 --reload

# T4 — Frontend Next.js (puerto 3000)
cd frontend && npm run dev
```

**Si los embeddings están vacíos (agente sin resultados):**

```bash
cd backend/django_core && poetry run python manage.py reindex_embeddings
```

---

## URLs locales

| Servicio         | URL                                |
|------------------|------------------------------------|
| Aplicación       | <http://localhost:3000>            |
| Django API       | <http://localhost:8000/api/v1/>    |
| Django Admin     | <http://localhost:8000/admin/>     |
| Inventory Docs   | <http://localhost:8001/docs>       |
| Agent Docs       | <http://localhost:8002/docs>       |

---

## Credenciales por defecto

```text
Admin:   admin@litethinking.com   / Admin1234!
Externo: externo@litethinking.com / Externo1234!
```

---

## Flujo de uso

### 1. Login y roles

- **Admin**: acceso completo a todas las vistas
- **Externo**: solo visualiza empresas como visitante

### 2. Empresas (req a)

CRUD completo: NIT (PK editable con CASCADE), nombre, dirección, teléfono. Cada operación genera un registro en blockchain_log.

### 3. Productos (req b)

Crear con código, nombre, características y precios en múltiples monedas (COP, USD, EUR…). Al guardar, el sistema genera el embedding semántico automáticamente para el agente.

### 4. Inventario (req d)

- Ver stock por empresa con edición inline de cantidades
- **Exportar PDF**: genera PDF con ReportLab via microservicio
- **Enviar por email**: adjunta el PDF al correo indicado (requiere SMTP)

### 5. Agente IA + Carrito (req g, k)

- Selecciona empresa en el dropdown
- Escribe en lenguaje natural: "¿Qué laptops tienen más de 16GB RAM?"
- El agente busca por similitud semántica (pgvector cosine similarity)
- Los productos aparecen como chips clicables debajo de la respuesta
- Agrega al carrito, ajusta cantidades y confirma el pedido
- El pedido decrementa stock con `select_for_update()` y escribe en blockchain_log

### 6. Auditoría Blockchain (req g)

Vista `/auditoria` (solo admin): tabla de todas las operaciones críticas con hash SHA-256, filtros por entidad (empresa / producto / inventario) y estado on-chain vs local.

---

## API REST — Endpoints principales

### Auth (Django :8000)

```text
POST /api/v1/auth/login/       { email, password } → { access, refresh }
POST /api/v1/auth/refresh/     { refresh } → { access }
```

### Empresas

```text
GET    /api/v1/empresas/
POST   /api/v1/empresas/           (admin)
GET    /api/v1/empresas/{nit}/
PATCH  /api/v1/empresas/{nit}/     (admin)
DELETE /api/v1/empresas/{nit}/     (admin — soft delete)
```

### Productos

```text
GET    /api/v1/productos/          ?empresa=NIT
POST   /api/v1/productos/          (admin)
PATCH  /api/v1/productos/{id}/     (admin)
DELETE /api/v1/productos/{id}/     (admin — soft delete)
POST   /api/v1/productos/{id}/precios/
GET    /api/v1/monedas/
```

### Inventario

```text
GET    /api/v1/inventario/              ?empresa=NIT
POST   /api/v1/inventario/             (admin)
PATCH  /api/v1/inventario/{id}/        (admin)
POST   /api/v1/inventario/pedido/      { items: [{inventario_id, cantidad}] }
POST   /api/v1/inventario/export-pdf/  { empresa_nit }
POST   /api/v1/inventario/export-email/ { empresa_nit, recipient_email }
```

### Agente (FastAPI :8002)

```text
POST /api/v1/agent/query/              { query, empresa_nit?, empresa_nombre? }
POST /api/v1/agent/search/             { query, empresa_nit?, top_k? }
POST /api/v1/agent/embeddings/upsert/  { producto_id, nombre, caracteristicas }
GET  /api/v1/blockchain/log/           ?entity_type=inventario&limit=50
```

---

## Blockchain — Auditoría de integridad

Cada operación crítica (crear/editar/eliminar empresa, producto o inventario) genera:

```text
payload = { datos del evento }
data_hash = SHA-256(JSON.dumps(payload, sort_keys=True))
→ INSERT INTO blockchain_log (entity_type, entity_id, accion, data_hash)
```

Si alguien modifica un registro directamente en la BD, el hash guardado ya no coincide con el estado actual — la manipulación es detectable.

La infraestructura para anclar hashes en Polygon Mumbai (web3.py) está implementada. Se activa con `BLOCKCHAIN_ENABLED=True` y `BLOCKCHAIN_PRIVATE_KEY` en `.env`.

---

## Arquitectura — Clean Architecture

```text
domain/                 ← Entidades + Value Objects + Repositorios ABC
                          Sin imports de Django, FastAPI, SQLAlchemy
backend/django_core/    ← Capa aplicación + infraestructura
  utils/blockchain.py   ← Helper SHA-256 compartido por todas las apps
  apps/companies/       ← Implementa repositorios del dominio
  apps/products/
  apps/inventory/
  apps/users/
backend/services/       ← Microservicios independientes
  inventory_service/    ← PDF + email (ReportLab + SMTP)
  ai_agent/             ← pgvector + LangChain + blockchain log GET
      routers/agent.py
      services/
          embedding_service.py
          langchain_agent.py
          blockchain_service.py
frontend/               ← Next.js 14, Atomic Design
  atoms → molecules → organisms → templates → pages
```

**El dominio no conoce a Django.** Django consume el dominio como paquete Poetry local (`litethinking-domain = { path = "../../domain", develop = true }`).

---

## Roles

| Rol        | Acceso                                                                    |
|------------|---------------------------------------------------------------------------|
| **admin**  | CRUD empresas, productos, inventario, exportación, agente, auditoría      |
| **externo**| Solo lectura: ver empresas                                                |

---

## Validación de NIT

4 capas de validación:

1. **Frontend (Zod)**: regex antes de enviar
2. **Domain VO**: `NIT` value object con `InvalidNITError`
3. **DRF Serializer**: `validate_nit()` con mensaje descriptivo
4. **DB CHECK CONSTRAINT**: `chk_empresa_nit_format` — última barrera

Formato válido: `^\d{6,10}(-\d)?$` — ej: `900123456` o `900123456-7`

NIT es editable. El cambio se propaga automáticamente a todos los productos asociados via `ON UPDATE CASCADE` en PostgreSQL.

---

## Tests

```bash
# Dominio (entidades + value objects)
cd domain && poetry run pytest -v

# Django
cd backend/django_core && poetry run pytest -v
```

---

## Rendimiento — Lighthouse / GTmetrix

URL analizada: <https://100.57.100.132.nip.io>

| Métrica               | Resultado   |
|-----------------------|-------------|
| Performance           | **100**     |
| Accesibilidad         | **100**     |
| Prácticas recomendadas| **100**     |
| SEO                   | **100**     |
| LCP                   | < 600 ms    |
| TBT                   | 0 ms        |
| CLS                   | 0           |

---

## SonarQube

```bash
docker run -d --name sonarqube -p 9000:9000 sonarqube:community
# Abrir http://localhost:9000 → crear proyecto → obtener token

sonar-scanner \
  -Dsonar.host.url=http://localhost:9000 \
  -Dsonar.token=TU_TOKEN
```

Configuración en `sonar-project.properties` (raíz del proyecto).

**Resultados del análisis (5,033 líneas):**

| Métrica          | Resultado    |
|------------------|--------------|
| Quality Gate     | **Passed**   |
| Bugs             | 0            |
| Vulnerabilities  | 0            |
| Security Hotspots| 0            |
| Code Smells      | 64           |
| Duplications     | 0.0%         |
| Lines of Code    | 5,033        |

---

## Estructura del proyecto

```text
LiteThinking-Python-React/
├── domain/                          # Paquete Poetry — capa dominio pura
│   ├── pyproject.toml
│   └── src/litethinking_domain/
│       ├── entities/                # Empresa, Producto, Usuario, Inventario
│       ├── value_objects/           # NIT, Money, EmailAddress, PasswordHash
│       ├── repositories/            # Interfaces ABC (puertos)
│       └── exceptions/
│
├── backend/
│   ├── django_core/                 # API principal :8000
│   │   ├── utils/
│   │   │   └── blockchain.py        # SHA-256 audit helper compartido
│   │   └── apps/
│   │       ├── companies/           # CRUD empresas + blockchain log
│   │       ├── products/            # CRUD productos + embeddings + blockchain log
│   │       ├── inventory/           # Stock + pedidos + PDF/email + blockchain log
│   │       └── users/               # Auth JWT + roles
│   │
│   └── services/
│       ├── inventory_service/       # FastAPI :8001 — PDF + email
│       └── ai_agent/                # FastAPI :8002 — agente + pgvector + blockchain GET
│           ├── routers/agent.py
│           └── services/
│               ├── embedding_service.py
│               ├── langchain_agent.py
│               └── blockchain_service.py
│
├── frontend/
│   └── src/
│       ├── app/(dashboard)/
│       │   ├── empresas/
│       │   ├── productos/
│       │   ├── inventario/
│       │   ├── agente/              # Agente + carrito
│       │   └── auditoria/           # Blockchain audit (solo admin)
│       └── components/
│           ├── atoms/               # Button, Input, Label, Badge, Spinner
│           ├── molecules/           # FormField, CurrencyDisplay
│           ├── organisms/           # Navbar, CompanyForm/Table, InventoryTable…
│           └── templates/           # AuthTemplate, DashboardTemplate
│
├── database/
│   ├── migrations/
│   │   ├── V1__initial_schema.sql   # Esquema completo (referencia)
│   │   └── V3__extra_tables.sql     # blockchain_log, produto_embedding, email_log
│   └── seeds/
│       └── V2__seed_data.sql        # Monedas ISO 4217 + empresa ejemplo
│
├── setup.sh                         # Aprovisionamiento macOS/Linux
├── setup.ps1                        # Aprovisionamiento Windows
├── sonar-project.properties
└── README.md
```

---

## Autor

Jhojan Alexander Calambas Ramírez
