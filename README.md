# Sysiphus 🪨

> *Herramienta para pensar mejor y escribir ensayos más profundos.*

Sysiphus es una aplicación web que combina un editor de ensayos con un asistente de IA multimodal. Ofrece retroalimentación contextualizada, un modo guía paso a paso y una arquitectura de contexto inteligente que mantiene la coherencia incluso en textos largos.

---

## ✨ Características

- **Múltiples modos de asistencia IA**
  - `ensayo` — ayuda a desarrollar argumentos y estructura
  - `mejora` — sugiere mejoras de redacción y claridad
  - `crítica` — análisis crítico y detección de debilidades
  - `estilo` — reescritura imitando un estilo específico

- **Modo Guía** — flujo paso a paso por fases: `idea → estructura → párrafos`

- **Gestión de proyectos** — crea y organiza ensayos como proyectos independientes

- **Contexto inteligente** — arquitectura híbrida de 4 capas para ensayos largos:
  - Chunking semántico del texto
  - Memoria maestra por proyecto (tesis + notas)
  - Sliding window por párrafo para edición local
  - Resumen jerárquico (map-reduce) + RAG SQL para recuperación selectiva

- **Telemetría de tokens** — métricas de uso de tokens y tasa de fallback por proyecto

- **Rate limiting** y caché in-memory de respuestas

- **Multi-usuario** — aislamiento por `owner_id` mediante cabecera `X-User-Id`

---

## 🛠️ Stack tecnológico

| Capa | Tecnología |
|------|-----------|
| Backend | Python 3.11+ · FastAPI · Uvicorn |
| ORM / DB | SQLAlchemy · SQLite (configurable vía `DATABASE_URL`) |
| Migraciones | Alembic (versionadas, con soporte `render_as_batch` para SQLite) |
| IA | OpenAI Chat Completions (`AsyncOpenAI`) |
| Validación | Pydantic v2 |
| Frontend | HTML · CSS · JavaScript vanilla (Jinja2) |
| Auth | `Authorization: Bearer <token>` (`SYSIPHUS_API_TOKEN`) + `X-User-Id` header |
| Caché | `cachetools.TTLCache` — tamaño máximo 512, TTL 1 hora |
| Rate limit | Ventana deslizante in-memory, thread-safe, cap de 2000 buckets |

---

## 🚀 Instalación y puesta en marcha

### Requisitos previos

- Python 3.11 o superior
- Una clave de API de OpenAI

### 1. Clonar el repositorio

```bash
git clone https://github.com/Cracksmity/Sisyphus.git
cd Sisyphus
```

### 2. Crear entorno virtual e instalar dependencias

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

```bash
cp .env.example .env
```

Edita `.env` y rellena los valores:

```env
OPENAI_API_KEY=sk-...                        # Tu clave de API de OpenAI
SYSIPHUS_API_TOKEN=dev-token                 # Token que usan los clientes
DATABASE_URL=sqlite:///./sysiphus.db         # Opcional: cambiar a PostgreSQL en producción
```

### 4. Aplicar migraciones de base de datos

```bash
alembic upgrade head
```

> ⚠️ **Importante:** las migraciones deben aplicarse antes del primer arranque y cada vez que se añadan cambios de esquema.

### 5. Arrancar el servidor

```bash
python main.py
```

O directamente con Uvicorn:

```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Abre [http://127.0.0.1:8000](http://127.0.0.1:8000) en tu navegador.

---

## 🔑 Autenticación

Todas las llamadas a la API requieren dos cabeceras:

| Cabecera | Descripción |
|----------|--------------|
| `Authorization: Bearer <token>` | Valor de `SYSIPHUS_API_TOKEN` — validado con `secrets.compare_digest` |
| `X-User-Id: <user_id>` | Identificador del usuario (cadena arbitraria, mínimo 3 caracteres) |

---

## 📡 Endpoints de la API

### Proyectos

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/api/projects` | Listar proyectos del usuario |
| `POST` | `/api/projects` | Crear un nuevo proyecto |
| `GET` | `/api/projects/{id}` | Obtener detalle de un proyecto |
| `DELETE` | `/api/projects/{id}` | Borrar un proyecto |
| `PUT` | `/api/projects/{id}/document` | Guardar el documento del proyecto |
| `GET` | `/api/projects/{id}/memory` | Estado de la memoria / resumen / RAG |
| `GET` | `/api/projects/{id}/interactions` | Historial de interacciones IA |
| `GET` | `/api/projects/{id}/metrics` | Métricas agregadas de tokens y fallback |

### IA

| Método | Ruta | Descripción |
|--------|------|-------------|
| `POST` | `/api/chat` | Chat libre con modo seleccionable |
| `POST` | `/api/guided-mode` | Flujo guiado por fases |

#### Ejemplo: `/api/chat`

```json
{
  "messages": [{"role": "user", "content": "¿Cómo mejoro mi tesis?"}],
  "modo": "mejora",
  "project_id": 1
}
```

#### Ejemplo: `/api/guided-mode`

```json
{
  "project_id": 1,
  "current_stage": "idea",
  "user_input": "Quiero escribir sobre el libre albedrío",
  "draft_content": "",
  "accumulated_content": ""
}
```

---

## 🏗️ Arquitectura de contexto

Para ensayos largos, Sysiphus usa una arquitectura híbrida que evita superar el límite de tokens del modelo:

```
Documento completo
       │
       ▼
  [Chunking semántico]  ──►  EssayChunk (N por proyecto)
       │
       ▼
  [Memoria maestra]     ──►  EssayMemory.thesis + memory_notes
       │
       ├──► [Resumen jerárquico]  map_summary → global_summary  (background)
       │
       └──► [RAG SQL]             índice de chunks + retrieval top-k  (background)

En cada chat:
  tesis + resumen global + sliding window local + RAG chunks  =  contexto final
```

El procesamiento en background se dispara automáticamente al guardar el documento (`PUT /api/projects/{id}/document`).

---

## 📁 Estructura del proyecto

```
Sisyphus/
├── main.py                      # Punto de entrada FastAPI
├── requirements.txt
├── .env.example
├── alembic.ini                  # Configuración de Alembic
├── alembic/
│   ├── env.py                   # Carga modelos + DATABASE_URL desde .env
│   └── versions/                # Migraciones versionadas
├── app/
│   ├── routers.py               # Endpoints REST
│   ├── models.py                # Modelos SQLAlchemy
│   ├── schemas.py               # Schemas Pydantic
│   ├── database.py              # Configuración DB (DATABASE_URL configurable)
│   ├── auth.py                  # Auth: Bearer token + secrets.compare_digest
│   ├── prompts.py               # System prompts por modo
│   ├── rate_limit.py            # Rate limiter thread-safe con cap de buckets
│   ├── ai_logic.py              # Lógica auxiliar IA
│   └── services/
│       ├── ai_service.py        # run_ai_with_meta, fallback, TTLCache
│       ├── context_service.py   # Chunking, memoria, resumen, RAG
│       ├── project_service.py   # CRUD de proyectos
│       └── guided_service.py    # Flujo del modo guía
├── templates/
│   └── index.html               # Frontend SPA (Jinja2)
├── static/                      # CSS, JS, imágenes
└── tests/
    ├── unit/
    └── integration/
```

---

## 🧪 Tests

```bash
pytest tests/
```

---

## 📝 Notas de desarrollo

- **Migraciones:** se gestionan con Alembic. Ante cualquier cambio en `models.py` ejecutar:
  ```bash
  alembic revision --autogenerate -m "descripcion"
  alembic upgrade head
  ```
- **`render_as_batch=True`** está habilitado en `alembic/env.py` — necesario para que SQLite soporte `ALTER TABLE` correctamente.
- **`DATABASE_URL`** se lee del entorno; por defecto apunta a SQLite local. Para usar PostgreSQL basta cambiar la variable en `.env`.
- **Auth:** el frontend envía `Authorization: Bearer <token>`. El backend valida con `secrets.compare_digest` (timing-safe). No usar `==` directo.
- **Rate limit y caché** son in-memory y no se comparten entre procesos. Si se usan múltiples workers de Uvicorn en el futuro, migrar a Redis.
- Los modos y fases del frontend y el backend deben mantenerse sincronizados (`ensayo`, `mejora`, `critica`, `estilo`, `guia`; fases: `idea`, `estructura`, y nombres de párrafo).
- El dominio / UX está en español; el código fuente e infraestructura en inglés.

---

## 📄 Licencia

Este proyecto no incluye una licencia explícita. Todos los derechos reservados al autor.
