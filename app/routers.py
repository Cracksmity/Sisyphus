from fastapi import APIRouter, Request, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.prompts import ensayo_prompt, mejora_prompt, critica_prompt, estilo_prompt, guia_idea_prompt, guia_estructura_prompt, guia_parrafo_prompt
from app.database import get_db, SessionLocal
from app import models, schemas
from app.auth import require_api_token, get_current_user_id
from app.rate_limit import chat_rate_limiter, write_rate_limiter
from app.services.project_service import list_projects, create_project, get_owned_project_or_404
from app.services.guided_service import validate_stage_transition, update_stage_content
from app.services.ai_service import run_ai_with_meta
from app.services.context_service import (
    update_master_memory,
    build_project_context,
    refresh_hierarchical_summary,
    refresh_rag_index,
    retrieve_rag_chunks,
)

router = APIRouter()
templates = Jinja2Templates(directory="templates")


def refresh_project_summary_background(project_id: int, document_content: str) -> None:
    db = SessionLocal()
    try:
        update_master_memory(db, project_id=project_id, document_content=document_content)
        refresh_hierarchical_summary(db, project_id=project_id, document_content=document_content)
        refresh_rag_index(db, project_id=project_id, document_content=document_content)
        db.commit()
    finally:
        db.close()

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Renderiza el frontend principal en HTML."""
    return templates.TemplateResponse(request=request, name="index.html")

# --- PROYECTOS CRUD ---

@router.get("/api/projects", response_model=List[schemas.ProjectResponse], dependencies=[Depends(require_api_token)])
def get_projects(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    return list_projects(db, owner_id=user_id, limit=limit, offset=offset)

@router.post("/api/projects", response_model=schemas.ProjectDetailResponse, dependencies=[Depends(require_api_token)])
def create_project_endpoint(
    project: schemas.ProjectCreate,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    write_rate_limiter.check(f"projects:create:{user_id}")
    return create_project(db, title=project.title, owner_id=user_id)

@router.get("/api/projects/{project_id}", response_model=schemas.ProjectDetailResponse, dependencies=[Depends(require_api_token)])
def get_project(project_id: int, db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    return get_owned_project_or_404(db, project_id, user_id)

@router.delete("/api/projects/{project_id}", dependencies=[Depends(require_api_token)])
def delete_project(project_id: int, db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    write_rate_limiter.check(f"projects:delete:{user_id}")
    project = get_owned_project_or_404(db, project_id, user_id)
    db.delete(project)
    db.commit()
    return {"status": "borrado"}

@router.put("/api/projects/{project_id}/document", dependencies=[Depends(require_api_token)])
def save_document(
    project_id: int,
    document: schemas.DocumentUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    write_rate_limiter.check(f"projects:save_doc:{user_id}")
    get_owned_project_or_404(db, project_id, user_id)
    doc = db.query(models.Document).filter(models.Document.project_id == project_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado para este proyecto")
    doc.content = document.content
    memory = update_master_memory(db, project_id=project_id, document_content=document.content)
    memory.summary_status = "queued"
    memory.summary_error = ""
    memory.rag_status = "queued"
    memory.rag_error = ""
    db.commit()
    background_tasks.add_task(
        refresh_project_summary_background,
        project_id=project_id,
        document_content=document.content,
    )
    return {"status": "guardado"}


@router.get("/api/projects/{project_id}/memory", response_model=schemas.EssayMemoryResponse, dependencies=[Depends(require_api_token)])
def get_project_memory(project_id: int, db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    get_owned_project_or_404(db, project_id, user_id)
    doc = db.query(models.Document).filter(models.Document.project_id == project_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado para este proyecto")
    memory = update_master_memory(db, project_id=project_id, document_content=doc.content or "")
    db.commit()
    db.refresh(memory)
    return memory

@router.get("/api/projects/{project_id}/interactions", response_model=schemas.InteractionListResponse, dependencies=[Depends(require_api_token)])
def list_interactions(
    project_id: int,
    mode: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    get_owned_project_or_404(db, project_id, user_id)
    query = db.query(models.Interaction).filter(models.Interaction.project_id == project_id)
    if mode:
        query = query.filter(models.Interaction.mode == mode)
    total = query.with_entities(func.count(models.Interaction.id)).scalar() or 0
    items = query.order_by(models.Interaction.timestamp.desc()).offset(offset).limit(limit).all()
    return schemas.InteractionListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/api/projects/{project_id}/metrics", response_model=schemas.ProjectMetricsResponse, dependencies=[Depends(require_api_token)])
def get_project_metrics(project_id: int, db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    get_owned_project_or_404(db, project_id, user_id)
    query = db.query(models.Interaction).filter(models.Interaction.project_id == project_id)
    interactions_total = query.with_entities(func.count(models.Interaction.id)).scalar() or 0
    if interactions_total == 0:
        return schemas.ProjectMetricsResponse(
            interactions_total=0,
            total_tokens_estimate=0,
            avg_tokens_per_interaction=0.0,
            avg_prompt_tokens=0.0,
            avg_completion_tokens=0.0,
            fallback_rate=0.0,
            avg_context_chars=0.0,
        )

    aggregates = query.with_entities(
        func.coalesce(func.sum(models.Interaction.total_tokens_estimate), 0),
        func.coalesce(func.avg(models.Interaction.total_tokens_estimate), 0.0),
        func.coalesce(func.avg(models.Interaction.prompt_tokens_estimate), 0.0),
        func.coalesce(func.avg(models.Interaction.completion_tokens_estimate), 0.0),
        func.coalesce(func.avg(models.Interaction.fallback_used), 0.0),
        func.coalesce(func.avg(models.Interaction.context_chars), 0.0),
    ).first()

    return schemas.ProjectMetricsResponse(
        interactions_total=interactions_total,
        total_tokens_estimate=int(aggregates[0] or 0),
        avg_tokens_per_interaction=float(aggregates[1] or 0.0),
        avg_prompt_tokens=float(aggregates[2] or 0.0),
        avg_completion_tokens=float(aggregates[3] or 0.0),
        fallback_rate=float(aggregates[4] or 0.0),
        avg_context_chars=float(aggregates[5] or 0.0),
    )

# --- CHAT / ORACULO ---

@router.post("/api/chat", dependencies=[Depends(require_api_token)])
async def chat_endpoint(
    req: schemas.ChatRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    Recibe la conversación, interpreta el modo seleccionado,
    asigna el prompt del sistema correspondiente y devuelve la respuesta.
    Incluye contexto del documento si existe.
    """
    system_prompt = "Eres un asistente útil y analítico."
    
    write_rate_limiter.check(f"chat:{user_id}")
    chat_rate_limiter.check(f"chat-heavy:{user_id}")

    if req.modo == "ensayo":
        system_prompt = ensayo_prompt
    elif req.modo == "mejora":
        system_prompt = mejora_prompt
    elif req.modo == "critica":
        system_prompt = critica_prompt
    elif req.modo == "estilo":
        if not req.estilo_seleccionado:
            raise HTTPException(status_code=400, detail="Debes seleccionar un estilo.")
        system_prompt = f"{estilo_prompt}\n\nEL ESTILO SOLICITADO A EMULAR ES: {req.estilo_seleccionado}"
    
    user_input_text = req.messages[-1].content if req.messages else ""

    # Contexto del proyecto si lo hay
    project_context = ""
    if req.project_id:
        get_owned_project_or_404(db, req.project_id, user_id)
        doc = db.query(models.Document).filter(models.Document.project_id == req.project_id).first()
        if doc and doc.content:
            memory = update_master_memory(db, project_id=req.project_id, document_content=doc.content)
            rag_chunks = retrieve_rag_chunks(db, project_id=req.project_id, user_query=user_input_text, limit=3)
            project_context = build_project_context(
                document_content=doc.content,
                user_query=user_input_text,
                memory=memory,
                rag_chunks=rag_chunks,
                focus_paragraph_index=req.focus_paragraph_index,
                sliding_window_radius=req.sliding_window_radius,
            )
            if project_context:
                system_prompt += f"\n\nCONTEXTO DEL PROYECTO ACTUAL (seleccionado):\n{project_context}\n"

    if req.draft_content:
        system_prompt += f"\n\nBORRADOR ACTUAL DEL USUARIO:\n{req.draft_content}\n"

    message_dicts = [{"role": msg.role, "content": msg.content} for msg in req.messages]
    if req.oracle_prompt:
        message_dicts.append({"role": "user", "content": req.oracle_prompt})
    
    try:
        response_text, ai_meta = await run_ai_with_meta(message_dicts, system_prompt, req.modo)
        
        # Si estamos dentro de un proyecto, pre-guardamos la interaccion
        if req.project_id:
            interaction = models.Interaction(
                project_id=req.project_id,
                mode=req.modo,
                user_input=user_input_text,
                ai_output=response_text,
                model_used=ai_meta.get("model_used", ""),
                fallback_used=1 if ai_meta.get("fallback_used") else 0,
                prompt_tokens_estimate=ai_meta.get("prompt_tokens_estimate", 0),
                completion_tokens_estimate=ai_meta.get("completion_tokens_estimate", 0),
                total_tokens_estimate=ai_meta.get("total_tokens_estimate", 0),
                context_chars=len(project_context or ""),
            )
            db.add(interaction)
            db.commit()

        return {"response": response_text}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno al procesar la solicitud.")

@router.post("/api/guided-mode", response_model=schemas.GuidedResponse, dependencies=[Depends(require_api_token)])
async def guided_mode_endpoint(
    req: schemas.GuidedRequest,
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    write_rate_limiter.check(f"guided:{user_id}")
    chat_rate_limiter.check(f"guided-heavy:{user_id}")
    project = get_owned_project_or_404(db, req.project_id, user_id)
    
    guided_state = project.guided_state
    if not guided_state:
        guided_state = models.GuidedState(
            project_id=req.project_id,
            current_stage=req.current_stage,
            accumulated_content=req.accumulated_content,
        )
        db.add(guided_state)
    else:
        validate_stage_transition(guided_state.current_stage, req.current_stage)
        guided_state.current_stage = req.current_stage
        guided_state.accumulated_content = req.accumulated_content
    update_stage_content(guided_state, req.current_stage, req.draft_content.strip())
    
    db.commit()
    db.refresh(guided_state)

    # Determine prompt based on stage
    system_prompt = ""
    if req.current_stage == "idea":
        system_prompt = guia_idea_prompt
    elif req.current_stage == "estructura":
        system_prompt = guia_estructura_prompt
    else:
        system_prompt = guia_parrafo_prompt + f"\n\nROL ACTUAL DEL PÁRRAFO: {req.current_stage.upper()}\n"
        
    system_prompt += f"\n\nCONTENIDO ACUMULADO DEL ENSAYO HASTA AHORA (usa esto como contexto):\n{req.accumulated_content}"

    if req.draft_content:
        system_prompt += f"\n\nBORRADOR EN ESTA FASE:\n{req.draft_content}\n"
    messages = [{"role": "user", "content": req.user_input}]
    
    try:
        response_text, ai_meta = await run_ai_with_meta(messages, system_prompt, "guia")
        
        # Save interaction history
        interaction = models.Interaction(
            project_id=req.project_id,
            mode="guia",
            user_input=f"[{req.current_stage.upper()}] " + req.user_input,
            ai_output=response_text,
            model_used=ai_meta.get("model_used", ""),
            fallback_used=1 if ai_meta.get("fallback_used") else 0,
            prompt_tokens_estimate=ai_meta.get("prompt_tokens_estimate", 0),
            completion_tokens_estimate=ai_meta.get("completion_tokens_estimate", 0),
            total_tokens_estimate=ai_meta.get("total_tokens_estimate", 0),
            context_chars=len(req.accumulated_content or "") + len(req.draft_content or ""),
        )
        db.add(interaction)
        db.commit()

        return schemas.GuidedResponse(
            response=response_text,
            current_stage=req.current_stage,
            accumulated_content=req.accumulated_content,
            can_advance=len(req.draft_content.strip()) >= 80 or req.current_stage in ("idea", "estructura"),
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno al procesar modo guía.")
