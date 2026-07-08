# CONTEXT

## 1. Stack y estado actual
- **Backend:** Python + FastAPI (`main.py`, `app/routers.py`)
- **Persistencia:** SQLAlchemy ORM + SQLite local (`sysiphus.db`)
- **Migraciones:** Alembic (`alembic/`, `alembic.ini`) — reemplazó el antiguo `ensure_sqlite_schema()`. `render_as_batch=True` habilitado para compatibilidad con SQLite.
- **IA:** OpenAI Chat Completions vía `AsyncOpenAI` (`app/ai_logic.py`)
- **Validación:** Pydantic (`app/schemas.py`)
- **Frontend:** HTML/CSS/JS vanilla (`templates/`, `static/`)
- **Auth:** `Authorization: Bearer <token>` validado con `secrets.compare_digest` (`app/auth.py`)
- **Caché:** `cachetools.TTLCache(maxsize=512, ttl=3600)` en `app/services/ai_service.py`
- **Rate limit:** Ventana deslizante in-memory, thread-safe, cap de 2000 buckets (`app/rate_limit.py`)

## 2. Arquitectura de optimización de contexto (implementada)
Se implementó arquitectura híbrida de 4 capas para ensayos largos:
1. **Chunking semántico** base (`semantic_chunk_text`)
2. **Memoria maestra** por proyecto (`EssayMemory.thesis`, `memory_notes`)
3. **Sliding Window** por párrafo para edición local
4. **Resumen jerárquico + RAG SQL** como contexto global/recuperación selectiva

Código principal: `app/services/context_service.py`.

## 3. Modelo de datos relevante
### Entidades base
- `Project`
- `Document` (texto del ensayo)
- `GuidedState` (modo guía)
- `Interaction` (historial IA)

### Entidades nuevas para contexto
- `EssayMemory` (1:1 con `Project`)
  - `thesis`, `memory_notes`, `chunk_count`, `document_hash`
  - resumen jerárquico: `map_summary`, `global_summary`, `summary_status`, `summary_error`, `summary_hash`
  - RAG local: `rag_status`, `rag_error`, `rag_hash`
- `EssayChunk` (N:1 con `Project`)
  - `chunk_index`, `chunk_text`, `chunk_summary`, `chunk_terms`, `chunk_hash`

### Telemetría de costo/calidad por interacción
`Interaction` ahora persiste:
- `model_used`
- `fallback_used` (0/1)
- `prompt_tokens_estimate`
- `completion_tokens_estimate`
- `total_tokens_estimate`
- `context_chars`

## 4. Flujo backend actual
### Guardado de documento (`PUT /api/projects/{id}/document`)
1. Actualiza `Document.content`
2. Refresca memoria base (`update_master_memory`)
3. Marca `summary_status` y `rag_status` como `queued`
4. Lanza tarea en background (`refresh_project_summary_background`) que ejecuta:
   - `refresh_hierarchical_summary` (map-reduce heurístico)
   - `refresh_rag_index` (reindexación de chunks para retrieval)

### Chat (`POST /api/chat`)
1. Selecciona prompt por modo (`ensayo|mejora|critica|estilo`)
2. Si hay proyecto:
   - carga documento
   - refresca memoria maestra
   - recupera chunks RAG con `retrieve_rag_chunks(top-k)`
   - arma contexto final con `build_project_context(...)`:
     - tesis + señales
     - resumen global (si `summary_status=done`)
     - sliding window (foco/radio)
     - fragmentos RAG relevantes
3. Ejecuta `run_ai_with_meta(...)` con presupuesto de tokens y fallback
4. Persiste `Interaction` + métricas de tokens/contexto

### Modo guía (`POST /api/guided-mode`)
- Mantiene flujo por fases y transición lineal
- También usa `run_ai_with_meta(...)` y guarda métricas en `Interaction`

## 5. Política de tokens/modelos (app/services/ai_service.py)
- Budget de entrada por modo (`MODE_INPUT_BUDGET`)
- Recorte de historial por ventana de tokens (`_trim_messages`)
- Estimación de tokens por heurística de caracteres
- Fallback automático por costo cuando prompt bruto supera umbral:
  - Ejemplo: `ensayo`/`estilo` pueden degradar a `gpt-4o-mini`
- `max_tokens` de salida configurable por modelo (`MODEL_OUTPUT_TOKENS`)
- Caché de respuesta via `TTLCache` por hash de payload final (mensaje+prompt+modelo+max_tokens)
  - `maxsize=512` — evita memory leak
  - `ttl=3600` — respuestas expiran tras 1 hora

## 6. Endpoints clave para otros agentes
- `GET /api/projects`
- `POST /api/projects`
- `GET /api/projects/{project_id}`
- `PUT /api/projects/{project_id}/document`
- `GET /api/projects/{project_id}/memory`  ← estado memoria/resumen/RAG
- `GET /api/projects/{project_id}/interactions`
- `GET /api/projects/{project_id}/metrics` ← métricas agregadas de tokens/fallback/contexto
- `POST /api/chat`
- `POST /api/guided-mode`

## 7. Convenciones y notas operativas
- Dominio/UX en español; infraestructura/código en inglés (mantener).
- Seguridad multiusuario por `owner_id == X-User-Id`.
- Auth via `Authorization: Bearer <token>` — validar siempre con `secrets.compare_digest`, nunca con `==`.
- `rate_limit` y cachés son in-memory (no confiables entre procesos). Si se usan múltiples workers de Uvicorn, migrar a Redis.
- **Migraciones con Alembic** — ante cualquier cambio en `app/models.py`:
  ```bash
  alembic revision --autogenerate -m "descripcion"
  alembic upgrade head
  ```
- `DATABASE_URL` se lee del entorno (default: `sqlite:///./sysiphus.db`). Para PostgreSQL basta cambiar la variable.
- Strings de modo/fase deben mantenerse sincronizados frontend-backend.
- `render_as_batch=True` en `alembic/env.py` — no eliminar, es necesario para SQLite.
