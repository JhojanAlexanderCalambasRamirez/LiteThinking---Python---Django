# Guía de Sustentación — LiteThinking 2026

---

## Arranque rápido (4 terminales)

```bash
# T1 — Django (API principal, auth, CRUD, pedidos, blockchain write)
cd backend/django_core
poetry run python manage.py runserver
# → http://localhost:8000

# T2 — FastAPI Inventory Service (PDF + email)
cd backend/services/inventory_service
poetry run uvicorn main:app --port 8001 --reload
# → http://localhost:8001

# T3 — FastAPI AI Agent (búsqueda semántica + blockchain log GET)
cd backend/services/ai_agent
poetry run uvicorn main:app --port 8002 --reload
# → http://localhost:8002

# T4 — Frontend Next.js
cd frontend
npm run dev
# → http://localhost:3000
```

**Credenciales de prueba:**
- Admin: `admin@litethinking.com` / `Admin1234!`
- Externo: `externo@litethinking.com` / `Externo1234!`

**Si los embeddings están vacíos (agente dice "no hay datos"):**
```bash
cd backend/django_core
poetry run python manage.py reindex_embeddings
```

**Si el stock quedó en 0 después de un pedido:**
```bash
cd backend/django_core
poetry run python manage.py shell -c "from django.db import connection; c = connection.cursor(); c.execute('UPDATE inventario SET cantidad = 20, updated_at = NOW() WHERE cantidad = 0'); print('Updated:', c.rowcount)"
```

---

## Demo completa ante jurados — guion paso a paso

### 1. Login y roles (req e, f)
1. Entra a `http://localhost:3000/login`
2. Login como **Externo** → solo ve "Empresas" en navbar → no puede crear/editar
3. Logout → login como **Admin** → ve todo: Empresas, Productos, Inventario, Agente IA, Auditoría

**Qué decir:** "Dos roles separados. El externo solo puede visualizar empresas como visitante. El admin tiene acceso completo. Las contraseñas usan bcrypt via Django, nunca texto plano."

---

### 2. Gestión de Empresa (req a)
1. Click "Empresas" → tabla con todas las empresas
2. Click "Nueva Empresa" → formulario con NIT, Nombre, Dirección, Teléfono
3. Crea empresa `900111222-1` / `Demo Jurado SAS`
4. Edita la empresa → cambia nombre → guarda

**Qué decir:** "NIT es la llave primaria. Es editable porque implementamos `ON UPDATE CASCADE` en PostgreSQL para propagar el cambio a todas las FKs de productos."

---

### 3. Gestión de Producto (req b)
1. Click "Productos" → click "Nuevo Producto"
2. Completa: Código, Nombre, Características, selecciona empresa
3. Agrega precio en COP y USD
4. Guarda

**Qué decir:** "Precios en múltiples monedas. Al crear el producto, Django llama automáticamente al AI Agent para generar y guardar el embedding del producto en pgvector."

---

### 4. Inventario — PDF y Email (req d)
1. Click "Inventario" → filtra por empresa
2. Click "Descargar PDF" → el PDF se descarga automáticamente
3. Click "Enviar por Email" → ingresa correo → PDF llega al correo

**Qué decir:** "Django delega la generación del PDF al microservicio `inventory_service` (FastAPI en :8001) via HTTP. Es una operación pesada con ReportLab — separarla evita bloquear el servidor principal. El envío de email usa SMTP directo."

---

### 5. Agente IA con carrito (req g, k)
1. Click "Agente IA"
2. Selecciona empresa en el dropdown
3. Escribe: "¿Qué laptops tienen disponibles?"
4. El agente responde con texto + chips de productos debajo
5. Click en un chip → se agrega al carrito derecho
6. Ajusta cantidades con +/-
7. Click "Confirmar pedido"

**Qué decir:** "Búsqueda semántica con pgvector. La query del usuario se convierte en un vector de 384 dimensiones usando sentence-transformers local (sin API key). PostgreSQL calcula cosine similarity con el operador `<=>` de pgvector. LangChain orquesta el agente con Groq (LLaMA 3.3) o Claude como fallback."

---

### 6. Auditoría Blockchain (req g) — DEMO DE INTEGRIDAD

Este es el momento más impactante de la sustentación. Sigue estos pasos en orden:

**Paso 1 — Genera eventos:**
- Crea una empresa nueva → va a /auditoria → aparece fila tipo "empresa" / acción "CREATE"
- Edita el nombre → aparece "empresa" / "UPDATE"
- Ve a /agente → confirma un pedido → aparece "inventario" / "UPDATE"

**Paso 2 — Muestra la tabla:**
- Click en filtro "Empresa" → solo eventos de empresas
- Click en filtro "Inventario" → solo pedidos
- Click "Todos" → vista completa cronológica

**Paso 3 — Muestra el hash en terminal (copia y pega esto):**

```bash
psql -U postgres -d litethinking_db \
  -c "SELECT entity_type, accion, inv.cantidad AS stock_actual, LEFT(bl.data_hash,32) AS hash FROM blockchain_log bl JOIN inventario inv ON inv.id = bl.entity_id::uuid WHERE bl.entity_type = 'inventario' ORDER BY bl.created_at DESC LIMIT 1;"
```

**Qué decir:** "Este es el hash SHA-256 del pedido que confirmamos. Refleja el estado exacto del inventario en ese momento — producto, cantidad solicitada, stock restante. Ahora voy a simular que alguien con acceso directo a la base de datos manipula el stock:"

**Paso 4 — Demo de detección de fraude (el WOW moment):**

```bash
# FRAUDE: alguien sube el stock a 9999 directamente en la DB
psql -U postgres -d litethinking_db \
  -c "UPDATE inventario SET cantidad = 9999 WHERE id = 'e7d0ca91-ae66-49e7-9829-3f00fe5a0485';"
```

```bash
# DETECCIÓN: el hash en blockchain_log NO cambió, pero el stock dice 9999
psql -U postgres -d litethinking_db \
  -c "SELECT bl.data_hash, inv.cantidad AS stock_manipulado FROM blockchain_log bl JOIN inventario inv ON inv.id = bl.entity_id::uuid WHERE bl.entity_id = 'e7d0ca91-ae66-49e7-9829-3f00fe5a0485';"
```

Resultado esperado:

```
                           data_hash                             | stock_manipulado
------------------------------------------------------------------+-----------------
 8c5632114cc9cc420f09aab45c70ada3976861afa5a85628624990501a887cb2 |            9999
```

**Qué decir:** "El hash dice que cuando se confirmó el pedido, el stock resultante era 95. Ahora la base de datos dice 9999. Nadie pasó por el sistema para hacer ese cambio — el blockchain lo expone. En producción este hash estaría anclado en Polygon Mumbai, haciéndolo completamente inmutable. La infraestructura está lista: columnas `tx_hash`, `block_number`, `network` en la tabla y `blockchain_service.py` con la integración web3.py."

```bash
# RESTAURAR después del demo:
psql -U postgres -d litethinking_db \
  -c "UPDATE inventario SET cantidad = 95 WHERE id = 'e7d0ca91-ae66-49e7-9829-3f00fe5a0485';"
```

---

## Arquitectura general

```
┌─────────────────────────────────────────────────────────────────┐
│  Frontend  Next.js 14 (App Router)  :3000                       │
│  Atomic Design: atoms → molecules → organisms → templates       │
└────────────┬────────────────┬───────────────────────────────────┘
             │                │
    :8000    ▼      :8001     ▼      :8002
┌────────────────┐  ┌──────────────────┐  ┌────────────────────────┐
│  Django 5      │  │  FastAPI         │  │  FastAPI               │
│  (Core API)    │  │  Inventory Svc   │  │  AI Agent              │
│                │  │                  │  │                        │
│  Auth JWT      │  │  Genera PDF      │  │  pgvector search       │
│  CRUD empresas │  │  Envía email     │  │  LangChain agent       │
│  CRUD productos│  │  (ReportLab +    │  │  Groq / Anthropic      │
│  Inventario    │  │   smtplib)       │  │  Blockchain log GET    │
│  Pedidos       │  └──────────────────┘  └────────────────────────┘
│  Blockchain ✍  │              │                      │
└────────┬───────┘              └──────────┬───────────┘
         │                                 │
         ▼                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│  PostgreSQL  (misma instancia, misma DB)                        │
│                                                                 │
│  empresa │ producto │ inventario │ usuario │ moneda             │
│  producto_embedding (pgvector vector(384))                      │
│  blockchain_log (SHA-256 + tx_hash Polygon opcional)            │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│  domain/  — Paquete Poetry independiente                        │
│  litethinking_domain                                            │
│  ├── entities/   Empresa, Producto, Usuario, Inventario         │
│  ├── value_objects/  NIT, Money, EmailAddress, PasswordHash     │
│  ├── repositories/   Interfaces abstractas (no Django, no HTTP) │
│  └── exceptions/  DomainException base                         │
└─────────────────────────────────────────────────────────────────┘
```

**Quién escribe en blockchain_log:** Django (operaciones de negocio)
**Quién lee blockchain_log:** FastAPI AI Agent (endpoint GET /blockchain/log/)
**Por qué separado:** Django no expone ese endpoint al público. El AI agent actúa como API de consulta de auditoría, sin capacidad de escribir.

---

## Capa de Dominio — Por qué está separada

**Requerimiento h del PDF:** los modelos deben estar en una capa de dominio independiente, sin dependencias con vistas, serializers, controladores ni lógica HTTP.

**Decisión:** el dominio vive en `domain/` como paquete Poetry propio con su `pyproject.toml`. Django lo consume como dependencia local:

```toml
# backend/django_core/pyproject.toml
litethinking-domain = { path = "../../domain", develop = true }
```

**Lo que el dominio contiene:**
```
domain/src/litethinking_domain/
├── entities/
│   ├── empresa.py        # @dataclass Empresa — solo atributos + reglas de negocio
│   ├── producto.py       # @dataclass Producto
│   ├── usuario.py        # @dataclass Usuario + UserRole enum
│   └── inventario.py     # @dataclass Inventario
├── value_objects/
│   ├── nit.py            # NIT valida formato colombiano
│   ├── money.py          # Money con moneda + Decimal
│   ├── email_address.py  # EmailAddress valida formato
│   └── password_hash.py  # PasswordHash — nunca almacena texto plano
├── repositories/
│   └── *.py              # Interfaces abstractas (ABC) — Django implementa
└── exceptions/
    └── domain_exceptions.py  # DomainException, NITInvalidError, etc.
```

**Lo que NO tiene el dominio:** `import django`, `import fastapi`, `import sqlalchemy`, `import requests`. Cero.

---

## Microservicios — Por qué tres servicios

**Requerimiento j/h del PDF:** arquitectura de microservicios.

| Servicio | Puerto | Responsabilidad | Por qué separado |
|---|---|---|---|
| Django | 8000 | CRUD, auth, lógica de negocio central | Núcleo, maneja la DB principal |
| inventory_service | 8001 | PDF + email | Operación pesada (ReportLab), no bloquea Django |
| ai_agent | 8002 | pgvector, LangChain, blockchain audit | Carga modelo embeddings (~500MB en memoria), aislado |

Django llama a inventory_service vía HTTP (httpx) para PDF/email. AI agent es independiente con su propio pool SQLAlchemy a la misma DB.

---

## Blockchain — Cómo funciona en detalle

**Requerimiento g:** tecnologías novedosas incluyendo Blockchain.

### Qué operaciones se auditan

| Entidad | CREATE | UPDATE | DELETE |
|---------|--------|--------|--------|
| Empresa | ✓ al crear empresa | ✓ al editar empresa | ✓ al desactivar |
| Producto | ✓ al crear producto | ✓ al editar producto | ✓ al desactivar |
| Inventario | ✓ al agregar stock | ✓ al editar cantidad inline | — |
| Pedido | — | ✓ al confirmar pedido (reduce stock) | — |

### Flujo técnico

```python
# utils/blockchain.py — módulo compartido por todas las apps Django

def log_blockchain(entity_type, entity_id, action, data):
    payload = {**data, "entity_type": entity_type, "action": action}
    data_hash = SHA256(json.dumps(payload, sort_keys=True))
    INSERT INTO blockchain_log (entity_type, entity_id, accion, data_hash)
```

El módulo `utils/blockchain.py` es importado por `companies/views.py`, `products/views.py` e `inventory/views.py`. Alta cohesión, bajo acoplamiento: la lógica de hashing está en un solo lugar.

### Por qué SHA-256 y no solo un log normal

Un log normal puede ser modificado (UPDATE en la tabla, DELETE de registros). El hash SHA-256 del payload garantiza que **si el dato cambia, el hash no coincide**. La tabla `blockchain_log` tiene solo INSERT, nunca UPDATE ni DELETE desde la aplicación.

### Escalabilidad: Polygon Mumbai

La infraestructura on-chain está completa pero desactivada por defecto:
```
blockchain_log.tx_hash     → Hash de transacción Ethereum
blockchain_log.block_number → Número de bloque
blockchain_log.network     → 'polygon-mumbai' | 'ethereum-sepolia'
```

Con `BLOCKCHAIN_ENABLED=True` en `.env` + `BLOCKCHAIN_PRIVATE_KEY`, web3.py firma y envía el hash a Polygon. Actualmente en modo local (on_chain = False, ícono reloj en /auditoria).

---

## Agente IA — Cómo funciona

**Requerimiento k:** pgvector + LangChain + Anthropic/Groq.

### Flujo de una consulta

```
Usuario escribe → "¿Qué laptops tienen más de 16GB RAM?"
         │
         ▼
aiAgentApi.query(texto, empresa_nit, empresa_nombre)
         │
         ▼
FastAPI :8002  POST /api/v1/agent/query/
         │
         ▼
build_inventory_agent(db, empresa_nit, empresa_nombre)
         │
         ├─ Sistema prompt inyecta contexto empresa
         │   + REGLA: SIEMPRE usa buscar_productos antes de responder
         │   + REGLA: si el usuario quiere comprar sin especificar, busca "producto disponible"
         │
         ▼
LangChain AgentExecutor (LLaMA 3.3 via Groq → fallback Claude)
         │
         ├─ LLM decide llamar buscar_productos("laptops 16GB RAM")
         │
         ▼
buscar_productos(query) — empresa_nit baked en closure
         │
         ▼
semantic_search_productos(db, query, empresa_nit, top_k=5)
         │
         ├─ sentence-transformers genera embedding local (sin API)
         │   modelo: paraphrase-multilingual-MiniLM-L12-v2 (384 dims)
         │
         ▼
SQL pgvector:
  SELECT p.*, inv.id AS inventario_id, inv.cantidad AS stock,
         1 - (pe.embedding <=> query_vector) AS similarity
  FROM producto_embedding pe
  JOIN producto p ON p.id = pe.producto_id
  LEFT JOIN inventario inv ON inv.producto_id = p.id
  WHERE p.activo = TRUE [AND p.empresa_nit = ?]
  ORDER BY similitud DESC LIMIT 5
         │
         ▼
return { response: texto, productos_sugeridos: [con stock > 0] }
         │
         ▼
Frontend: texto en burbuja + chips clicables por producto disponible
```

### Por qué empresa_nit va en closure

Si el LLM recibe `empresa_nit` como parámetro del tool, puede olvidarse de pasarlo. Al bakearlo en el closure, el filtro se aplica siempre.

### Cuándo se generan los embeddings

Al crear o editar un producto, Django hace POST a `/api/v1/agent/embeddings/upsert/`. Si el AI agent estaba caído en ese momento, reindexar con:
```bash
poetry run python manage.py reindex_embeddings
```

---

## Carrito y Pedidos

### Flujo completo

```
1. Agente sugiere productos → chips bajo respuesta (solo stock > 0)
2. Click chip → addToCart() → estado React (sin roundtrip a DB)
3. Panel derecho: ajustar cantidades (+/-), quitar items, límite = stock disponible
4. "Confirmar pedido"
        │
        ▼
   POST /api/v1/inventario/pedido/
   { items: [{inventario_id, cantidad}] }
        │
        ▼
   Django confirmar_pedido:
   - select_for_update() → lock de filas por pedido concurrente
   - Valida stock suficiente por item
   - Decrementa cantidad en transacción atómica
   - Escribe en blockchain_log (SHA-256)
        │
        ▼
   Frontend invalida cache "inventario" → tabla se actualiza
```

### Por qué transacción atómica + select_for_update

Dos usuarios concurrentes para el mismo producto: sin lock ambos verían stock disponible y ambos decrementarían, quedando en negativo. `select_for_update()` serializa el acceso a nivel de fila de PostgreSQL.

---

## Autenticación y roles

- JWT con `djangorestframework-simplejwt`
- Contraseña: bcrypt via Django's `make_password`
- **Admin**: CRUD completo, ve todo el navbar
- **Externo**: solo lectura de empresas

```python
class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.rol == "admin"

class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.rol == "admin"
```

Frontend: `getCurrentUser()` decodifica JWT en cookie sin llamar al servidor. Se llama en `useEffect` (no en render) para evitar hydration mismatch SSR.

---

## Atomic Design en el Frontend

```
components/
├── atoms/          # Sin estado propio
│   ├── Button/     # Variantes: primary, secondary, danger, ghost
│   ├── Input/      # Con manejo de error
│   ├── Badge/      # Roles, estados
│   ├── Label/
│   ├── Spinner/
│   └── Toaster/    # Sistema de toasts
│
├── molecules/      # Combinaciones simples de átomos
│   ├── FormField/      # Label + Input + mensaje error
│   ├── CurrencyDisplay/ # Badges multi-moneda
│   └── ProductCard/
│
├── organisms/      # Secciones con lógica propia
│   ├── CompanyForm/    # Formulario crear/editar empresa
│   ├── CompanyTable/   # Tabla empresas con acciones
│   ├── InventoryTable/ # Tabla inventario con edición inline
│   ├── LoginForm/
│   ├── Navbar/         # Navegación con roles
│   ├── ProductForm/    # Formulario producto + precios
│   └── ProductTable/
│
└── templates/
    ├── AuthTemplate/       # Centra contenido, fondo degradado
    └── DashboardTemplate/  # header Navbar + main
```

**Regla estricta:** átomos no importan moléculas, moléculas no importan organismos, organismos no importan templates. Cada nivel solo conoce el nivel inferior.

---

## Inventario — PDF y Email

```
/inventario → "Descargar PDF"
        │
        ▼
Django POST /api/v1/inventario/export-pdf/
  └─ Construye payload (productos + precios de empresa)
  └─ httpx.post → FastAPI :8001 /export-pdf/
        │
        ▼
FastAPI inventory_service:
  └─ ReportLab genera PDF con tabla, logo, precios multi-moneda
  └─ Devuelve bytes (application/pdf)
        │
        ▼
Django hace streaming del PDF → descarga automática inventario_{nit}.pdf

Para email: mismo flujo + SMTP → PDF va al correo
```

---

## GTmetrix — Resultados

URL pública: https://lite-thinking-python-django.vercel.app/login

| Métrica | Resultado |
|---------|-----------|
| Performance | 🟢 **100%** |
| Structure | 🟢 **100%** |
| LCP | 🟢 592ms |
| TBT | 🟢 0ms |
| CLS | 🟢 0 |

**Qué decir ante los jurados:**
> "GTmetrix 100% en Performance y Structure. LCP de 592ms (excelente — umbral bueno es < 2.5s). TBT 0ms y CLS 0 — sin bloqueo de renderizado ni saltos de layout. Estos resultados se logran por Next.js App Router con SSR, Tailwind CSS sin JS en runtime, y las correcciones de hidratación implementadas."

---

## Lighthouse / Rendimiento

Fixes para 100/100/100/100 en producción:

| Problema | Fix |
|---|---|
| Hydration mismatch | `isAdmin()` en `useEffect`, `useState(false)` inicial |
| No landmark main | `<main>` en templates |
| Heading order h3→h1 | `h3` → `h2` en "Exportar inventario" |
| Contrast insuficiente | `text-gray-400` → `text-gray-600` |
| Select sin label | `htmlFor` + `id` en todos los selects |
| CLS 0.18 | Skeleton table (misma estructura DOM que tabla real) |

En `npm run dev` el score de Performance es ~77 (normal: polyfills dev, webpack sin minificar). En `npm run build && npm start` sube a 97-100.

---

## SonarQube — Resultados del análisis

Dashboard: http://localhost:9000/dashboard?id=litethinking

| Métrica | Resultado |
|---------|-----------|
| **Quality Gate** | ✅ **Passed** |
| Bugs | 🟢 **0** |
| Vulnerabilities | 🟢 **0** |
| Security Hotspots | 🟢 **0** |
| Code Smells | 🟡 64 (normal para 5,033 líneas) |
| Duplications | 🟢 **0.0%** |
| Lines of Code | 5,033 |

**Qué decir ante los jurados:**
> "Quality Gate pasado. 0 bugs, 0 vulnerabilidades, 0 duplicaciones. Los 64 code smells son principalmente patrones de tipado en TypeScript que SonarQube marca conservadoramente — ninguno representa riesgo en producción. El único falso positivo suprimido fue `S2068` en `testing.py`: una contraseña hardcodeada exclusiva del entorno de test, que no es una credencial de producción."

**Para levantar SonarQube si no está corriendo:**
```bash
docker start sonarqube
# o desde cero:
docker run -d --name sonarqube -p 9000:9000 sonarqube:community
```

`sonar-project.properties` en raíz configura fuentes: `frontend/src`, `backend/django_core`, `backend/services`, `domain/src`.

---

## Estructura de carpetas completa

```
LiteThinking-Python-React/
│
├── domain/                          # Paquete Poetry independiente
│   ├── pyproject.toml               # Sin deps Django/FastAPI/SQLAlchemy
│   └── src/litethinking_domain/
│       ├── entities/
│       ├── value_objects/
│       ├── repositories/            # Interfaces abstractas (ABC)
│       └── exceptions/
│
├── backend/
│   ├── django_core/
│   │   ├── utils/
│   │   │   └── blockchain.py        # SHA-256 audit helper compartido
│   │   └── apps/
│   │       ├── companies/           # views usan log_blockchain
│   │       ├── products/            # views usan log_blockchain + reindex
│   │       ├── inventory/           # views usan log_blockchain + select_for_update
│   │       └── users/
│   │
│   └── services/
│       ├── inventory_service/       # FastAPI :8001 — PDF + email
│       └── ai_agent/                # FastAPI :8002 — IA + blockchain log GET
│           ├── routers/agent.py
│           └── services/
│               ├── embedding_service.py
│               ├── langchain_agent.py
│               └── blockchain_service.py  # web3.py (listo, desactivado por defecto)
│
├── frontend/
│   └── src/
│       ├── app/(dashboard)/
│       │   ├── empresas/
│       │   ├── productos/
│       │   ├── inventario/
│       │   ├── agente/              # Agente IA + carrito
│       │   └── auditoria/           # Blockchain audit (admin only)
│       └── components/              # Atomic Design completo
│
├── database/migrations/V1__initial_schema.sql
├── sonar-project.properties
└── GUIA_SUSTENTACION.md
```

---

## Preguntas frecuentes en sustentación

**¿Por qué Django Y FastAPI?**
Django maneja la lógica central, auth y DB. FastAPI maneja operaciones que no deben bloquear Django: PDFs pesados y modelos de IA (~500MB en memoria). Microservicios por responsabilidad técnica real, no por moda.

**¿Por qué Poetry para el dominio?**
El PDF lo pide explícitamente (req i). Poetry permite versionar el dominio como paquete independiente. Cualquier microservicio puede consumirlo sin copiar código.

**¿Por qué pgvector y no Pinecone/Weaviate?**
Misma BD PostgreSQL ya existente. Sin infraestructura adicional. El modelo de embeddings corre local, sin API key. Costo operacional cero.

**¿Por qué sentence-transformers local y no OpenAI?**
Sin dependencia de API externa. El modelo `paraphrase-multilingual-MiniLM-L12-v2` soporta español. Funciona offline.

**¿Por qué LLaMA 3.3 (Groq) con fallback a Claude?**
Groq ofrece inferencia ~10x más rápida para queries simples. Fallback automático sin cambio de código.

**¿Por qué el carrito es estado React y no BD?**
Sin persistencia entre sesiones no se necesita modelo adicional. Estado local = UX instantánea sin roundtrips. El pedido confirmado sí persiste (stock decrementado + blockchain_log).

**¿La blockchain es real?**
La infraestructura completa: web3.py, columnas tx_hash/block_number/network, `blockchain_service.py`. Requiere `BLOCKCHAIN_ENABLED=True` + private key en `.env`. Sin eso, SHA-256 local garantiza integridad del dato igualmente.

**¿Por qué `select_for_update()` en pedidos?**
Previene race conditions. Sin lock: dos usuarios concurrentes ven stock disponible y ambos decrementan → stock negativo. Con lock: el segundo espera a que termine el primero.

**¿Qué pasa si el AI Agent cae?**
Los embeddings no se actualizan para nuevos productos. El CRUD de Django sigue funcionando (el error de embedding es `non-fatal`, nunca falla la creación del producto). Se puede reindexar con `manage.py reindex_embeddings` cuando vuelva a subir.

**¿Cómo se detecta manipulación en blockchain?**
El hash en `blockchain_log` refleja el estado del dato en el momento del evento. Si alguien hace UPDATE directo en la DB, el hash guardado ya no coincide con el payload actual. Discrepancia detectable sin necesidad de on-chain.
