from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime

# Shared Properties
class InteractionBase(BaseModel):
    mode: Literal["ensayo", "mejora", "critica", "estilo", "guia"]
    user_input: str = Field(min_length=1, max_length=6000)
    ai_output: str = Field(min_length=1, max_length=12000)

class DocumentBase(BaseModel):
    content: str = Field(default="", max_length=20000)

class ProjectBase(BaseModel):
    title: str = Field(min_length=1, max_length=120)

# Create Properties
class ProjectCreate(ProjectBase):
    pass

class DocumentUpdate(BaseModel):
    content: str = Field(default="", max_length=20000)

class GuidedRequest(BaseModel):
    project_id: int
    user_input: str = Field(min_length=1, max_length=6000)
    current_stage: Literal["idea", "estructura", "introduccion", "desarrollo", "contraargumento", "conclusion", "completado"]
    accumulated_content: str = Field(default="", max_length=20000)
    draft_content: str = Field(default="", max_length=20000)

class GuidedResponse(BaseModel):
    response: str
    current_stage: Literal["idea", "estructura", "introduccion", "desarrollo", "contraargumento", "conclusion", "completado"]
    accumulated_content: str
    can_advance: bool

class GuidedStateResponse(BaseModel):
    current_stage: Literal["idea", "estructura", "introduccion", "desarrollo", "contraargumento", "conclusion", "completado"]
    accumulated_content: str
    stage_idea: str = ""
    stage_estructura: str = ""
    stage_introduccion: str = ""
    stage_desarrollo: str = ""
    stage_contraargumento: str = ""
    stage_conclusion: str = ""
    
    class Config:
        from_attributes = True


class EssayMemoryResponse(BaseModel):
    thesis: str = ""
    memory_notes: str = ""
    chunk_count: int = 0
    map_summary: str = ""
    global_summary: str = ""
    summary_status: str = "idle"
    summary_error: str = ""
    rag_status: str = "idle"
    rag_error: str = ""
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Response Models
class InteractionResponse(InteractionBase):
    id: int
    project_id: int
    timestamp: datetime

    class Config:
        from_attributes = True

class DocumentResponse(DocumentBase):
    id: int
    project_id: int
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ProjectResponse(ProjectBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Aggregated Response Models
class ProjectDetailResponse(ProjectResponse):
    documents: List[DocumentResponse] = []
    guided_state: Optional[GuidedStateResponse] = None
    essay_memory: Optional[EssayMemoryResponse] = None

    class Config:
        from_attributes = True


class InteractionListResponse(BaseModel):
    items: List[InteractionResponse]
    total: int
    limit: int
    offset: int


class ProjectMetricsResponse(BaseModel):
    interactions_total: int
    total_tokens_estimate: int
    avg_tokens_per_interaction: float
    avg_prompt_tokens: float
    avg_completion_tokens: float
    fallback_rate: float
    avg_context_chars: float


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str = Field(min_length=1, max_length=6000)


class ChatRequest(BaseModel):
    modo: Literal["ensayo", "mejora", "critica", "estilo"]
    messages: List[ChatMessage] = Field(min_length=1, max_length=20)
    estilo_seleccionado: Optional[str] = Field(default=None, max_length=120)
    project_id: Optional[int] = None
    draft_content: str = Field(default="", max_length=20000)
    oracle_prompt: str = Field(default="", max_length=4000)
    focus_paragraph_index: Optional[int] = Field(default=None, ge=0, le=5000)
    sliding_window_radius: int = Field(default=1, ge=0, le=4)
