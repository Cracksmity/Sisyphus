import re
from hashlib import sha256

from sqlalchemy.orm import Session

from app import models

THESIS_MARKERS = (
    "tesis",
    "sostengo",
    "defiendo",
    "propongo",
    "argumento",
    "mi postura",
    "este ensayo",
    "planteo",
)

STOPWORDS = {
    "como",
    "cuando",
    "desde",
    "donde",
    "entre",
    "esta",
    "estas",
    "estos",
    "hacia",
    "hasta",
    "para",
    "porque",
    "sobre",
    "tras",
    "aunque",
    "tambien",
    "the",
    "and",
    "with",
    "that",
    "this",
    "from",
    "have",
}


def _normalize_spaces(text: str) -> str:
    return re.sub(r"[ \t]+", " ", (text or "")).strip()


def _split_paragraphs(text: str) -> list[str]:
    normalized = (text or "").replace("\r\n", "\n")
    return [_normalize_spaces(part) for part in re.split(r"\n{2,}", normalized) if _normalize_spaces(part)]


def _split_sentences(text: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", _normalize_spaces(text))
    return [s.strip() for s in sentences if s.strip()]


def semantic_chunk_text(text: str, target_chars: int = 900, max_chars: int = 1400) -> list[str]:
    paragraphs = _split_paragraphs(text)
    if not paragraphs:
        return []

    chunks: list[str] = []
    current_chunk = ""

    def flush() -> None:
        nonlocal current_chunk
        value = current_chunk.strip()
        if value:
            chunks.append(value)
        current_chunk = ""

    for paragraph in paragraphs:
        if len(paragraph) > max_chars:
            flush()
            sentence_buffer = ""
            for sentence in _split_sentences(paragraph):
                candidate = f"{sentence_buffer} {sentence}".strip() if sentence_buffer else sentence
                if len(candidate) <= max_chars:
                    sentence_buffer = candidate
                    continue
                if sentence_buffer:
                    chunks.append(sentence_buffer)
                sentence_buffer = sentence
            if sentence_buffer:
                chunks.append(sentence_buffer)
            continue

        candidate_chunk = f"{current_chunk}\n\n{paragraph}".strip() if current_chunk else paragraph
        if len(candidate_chunk) <= target_chars:
            current_chunk = candidate_chunk
            continue
        flush()
        current_chunk = paragraph

    flush()
    return chunks


def extract_master_thesis(text: str, max_chars: int = 320) -> str:
    paragraphs = _split_paragraphs(text)[:4]
    if not paragraphs:
        return ""

    candidates: list[tuple[int, str]] = []
    for paragraph_index, paragraph in enumerate(paragraphs):
        for sentence in _split_sentences(paragraph):
            sentence_lower = sentence.lower()
            score = 0
            if any(marker in sentence_lower for marker in THESIS_MARKERS):
                score += 3
            if 60 <= len(sentence) <= 260:
                score += 2
            if paragraph_index == 0:
                score += 1
            unique_words = {w for w in re.findall(r"\b[\wáéíóúñ]{4,}\b", sentence_lower)}
            score += min(len(unique_words) // 6, 2)
            candidates.append((score, sentence))

    if not candidates:
        fallback = paragraphs[0]
        return fallback[:max_chars].strip()

    best_sentence = sorted(candidates, key=lambda item: item[0], reverse=True)[0][1].strip()
    return best_sentence[:max_chars]


def _document_hash(content: str) -> str:
    return sha256((content or "").encode("utf-8")).hexdigest()


def _build_memory_notes(chunks: list[str]) -> str:
    if not chunks:
        return ""
    opening = chunks[0][:180].strip()
    ending = chunks[-1][:180].strip()
    if opening == ending:
        return f"Inicio del texto: {opening}"
    return f"Inicio del texto: {opening}\nCierre del texto: {ending}"


def update_master_memory(db: Session, project_id: int, document_content: str) -> models.EssayMemory:
    normalized_content = (document_content or "").strip()
    content_hash = _document_hash(normalized_content)
    memory = db.query(models.EssayMemory).filter(models.EssayMemory.project_id == project_id).first()
    if memory and memory.document_hash == content_hash:
        return memory

    chunks = semantic_chunk_text(normalized_content)
    thesis = extract_master_thesis(normalized_content)
    notes = _build_memory_notes(chunks)

    if not memory:
        memory = models.EssayMemory(project_id=project_id)
        db.add(memory)

    memory.thesis = thesis
    memory.memory_notes = notes
    memory.chunk_count = len(chunks)
    memory.document_hash = content_hash
    db.flush()
    return memory


def _truncate(text: str, max_chars: int) -> str:
    value = (text or "").strip()
    if len(value) <= max_chars:
        return value
    return value[:max_chars].rstrip() + "..."


def summarize_chunk(chunk: str, max_chars: int = 280) -> str:
    sentences = _split_sentences(chunk)
    if not sentences:
        return _truncate(chunk, max_chars=max_chars)

    if len(sentences) == 1:
        return _truncate(sentences[0], max_chars=max_chars)

    first = sentences[0]
    last = sentences[-1]
    if first == last:
        return _truncate(first, max_chars=max_chars)
    return _truncate(f"{first} {last}", max_chars=max_chars)


def build_hierarchical_summary(document_content: str, max_chunk_summaries: int = 8) -> tuple[str, str]:
    chunks = semantic_chunk_text(document_content)
    if not chunks:
        return "", ""

    chunk_summaries = [summarize_chunk(chunk) for chunk in chunks]
    chunk_summaries = chunk_summaries[:max_chunk_summaries]
    map_summary = "\n".join([f"- {item}" for item in chunk_summaries])
    reduce_summary = summarize_chunk(" ".join(chunk_summaries), max_chars=420)
    return map_summary, reduce_summary


def refresh_hierarchical_summary(db: Session, project_id: int, document_content: str) -> models.EssayMemory:
    normalized_content = (document_content or "").strip()
    content_hash = _document_hash(normalized_content)
    memory = db.query(models.EssayMemory).filter(models.EssayMemory.project_id == project_id).first()
    if not memory:
        memory = models.EssayMemory(project_id=project_id)
        db.add(memory)
        db.flush()

    if memory.summary_hash == content_hash and memory.summary_status == "done":
        return memory

    memory.summary_status = "running"
    memory.summary_error = ""
    db.flush()

    try:
        map_summary, global_summary = build_hierarchical_summary(normalized_content)
        memory.map_summary = map_summary
        memory.global_summary = global_summary
        memory.summary_hash = content_hash
        memory.summary_status = "done"
        memory.summary_error = ""
        db.flush()
        return memory
    except Exception as exc:
        memory.summary_status = "failed"
        memory.summary_error = _truncate(str(exc), max_chars=400)
        db.flush()
        raise


def _tokenizable_words(text: str) -> set[str]:
    words = {w.lower() for w in re.findall(r"\b[\wáéíóúñ]{4,}\b", (text or "").lower())}
    return {w for w in words if w not in STOPWORDS}


def _sorted_terms(text: str, max_terms: int = 80) -> list[str]:
    return sorted(_tokenizable_words(text))[:max_terms]


def refresh_rag_index(db: Session, project_id: int, document_content: str) -> models.EssayMemory:
    normalized_content = (document_content or "").strip()
    content_hash = _document_hash(normalized_content)
    memory = db.query(models.EssayMemory).filter(models.EssayMemory.project_id == project_id).first()
    if not memory:
        memory = models.EssayMemory(project_id=project_id)
        db.add(memory)
        db.flush()

    if memory.rag_hash == content_hash and memory.rag_status == "done":
        return memory

    memory.rag_status = "running"
    memory.rag_error = ""
    db.flush()

    try:
        chunks = semantic_chunk_text(normalized_content)
        db.query(models.EssayChunk).filter(models.EssayChunk.project_id == project_id).delete()
        for idx, chunk in enumerate(chunks):
            chunk_terms = " ".join(_sorted_terms(chunk))
            db.add(
                models.EssayChunk(
                    project_id=project_id,
                    chunk_index=idx,
                    chunk_text=chunk,
                    chunk_summary=summarize_chunk(chunk, max_chars=220),
                    chunk_terms=chunk_terms,
                    chunk_hash=_document_hash(f"{idx}:{chunk}"),
                )
            )
        memory.rag_hash = content_hash
        memory.rag_status = "done"
        memory.rag_error = ""
        db.flush()
        return memory
    except Exception as exc:
        memory.rag_status = "failed"
        memory.rag_error = _truncate(str(exc), max_chars=400)
        db.flush()
        raise


def retrieve_rag_chunks(db: Session, project_id: int, user_query: str, limit: int = 3) -> list[str]:
    chunks = (
        db.query(models.EssayChunk)
        .filter(models.EssayChunk.project_id == project_id)
        .order_by(models.EssayChunk.chunk_index.asc())
        .all()
    )
    if not chunks:
        return []

    query_terms = _tokenizable_words(user_query)
    if not query_terms:
        return [chunk.chunk_text for chunk in chunks[: min(limit, len(chunks))]]

    scored: list[tuple[int, int, str]] = []
    for chunk in chunks:
        terms = set((chunk.chunk_terms or "").split())
        overlap = len(query_terms.intersection(terms))
        scored.append((overlap, -chunk.chunk_index, chunk.chunk_text))

    scored.sort(reverse=True)
    selected = [item[2] for item in scored[:limit] if item[0] > 0]
    if selected:
        return selected
    return [chunk.chunk_text for chunk in chunks[: min(limit, len(chunks))]]


def select_relevant_chunks(chunks: list[str], user_query: str, limit: int = 3) -> list[str]:
    if not chunks:
        return []

    query_terms = _tokenizable_words(user_query)
    if not query_terms:
        return chunks[: min(limit, len(chunks))]

    scored: list[tuple[int, int, str]] = []
    for idx, chunk in enumerate(chunks):
        chunk_terms = _tokenizable_words(chunk)
        overlap = len(query_terms.intersection(chunk_terms))
        scored.append((overlap, -idx, chunk))

    scored.sort(reverse=True)
    selected = [item[2] for item in scored[:limit] if item[0] > 0]
    if selected:
        return selected
    return chunks[: min(limit, len(chunks))]


def _best_focus_paragraph_index(paragraphs: list[str], user_query: str) -> int:
    if not paragraphs:
        return 0
    query_terms = _tokenizable_words(user_query)
    if not query_terms:
        return min(1, len(paragraphs) - 1)

    scored: list[tuple[int, int]] = []
    for idx, paragraph in enumerate(paragraphs):
        terms = _tokenizable_words(paragraph)
        overlap = len(query_terms.intersection(terms))
        scored.append((overlap, -idx))
    scored.sort(reverse=True)
    if scored[0][0] <= 0:
        return min(1, len(paragraphs) - 1)
    return -scored[0][1]


def build_sliding_window(
    text: str,
    user_query: str,
    focus_paragraph_index: int | None = None,
    radius: int = 1,
    max_window_paragraphs: int = 5,
) -> tuple[list[tuple[int, str]], int]:
    paragraphs = _split_paragraphs(text)
    if not paragraphs:
        return [], 0

    focus = focus_paragraph_index if focus_paragraph_index is not None else _best_focus_paragraph_index(paragraphs, user_query)
    focus = max(0, min(focus, len(paragraphs) - 1))
    window_start = max(0, focus - max(radius, 0))
    window_end = min(len(paragraphs) - 1, focus + max(radius, 0))
    selected = [(idx, paragraphs[idx]) for idx in range(window_start, window_end + 1)]

    if len(selected) > max_window_paragraphs:
        selected = selected[:max_window_paragraphs]
    return selected, focus


def build_project_context(
    document_content: str,
    user_query: str,
    memory: models.EssayMemory | None,
    rag_chunks: list[str] | None = None,
    focus_paragraph_index: int | None = None,
    sliding_window_radius: int = 1,
    max_chars: int = 4200,
) -> str:
    chunks = semantic_chunk_text(document_content)
    relevant_chunks = rag_chunks if rag_chunks else select_relevant_chunks(chunks, user_query=user_query, limit=2)
    local_window, effective_focus = build_sliding_window(
        text=document_content,
        user_query=user_query,
        focus_paragraph_index=focus_paragraph_index,
        radius=sliding_window_radius,
        max_window_paragraphs=5,
    )

    sections: list[str] = []
    if memory and memory.thesis:
        sections.append(f"MEMORIA MAESTRA (TESIS):\n{memory.thesis}")
    if memory and memory.memory_notes:
        sections.append(f"SEÑALES DEL DOCUMENTO:\n{memory.memory_notes}")
    if memory and memory.global_summary and memory.summary_status == "done":
        sections.append(f"RESUMEN GLOBAL JERÁRQUICO:\n{memory.global_summary}")
    if local_window:
        formatted_window = "\n\n".join(
            [f"[Párrafo {paragraph_index}]\n{paragraph}" for paragraph_index, paragraph in local_window]
        )
        sections.append(
            f"VENTANA DESLIZANTE DE EDICIÓN (foco en párrafo {effective_focus}, radio {max(sliding_window_radius, 0)}):\n{formatted_window}"
        )
    if relevant_chunks:
        formatted = "\n\n".join(
            [f"[Fragmento {idx + 1} de {len(relevant_chunks)}]\n{chunk}" for idx, chunk in enumerate(relevant_chunks)]
        )
        heading = "FRAGMENTOS RAG RELEVANTES DEL ENSAYO" if rag_chunks else "FRAGMENTOS DE RESPALDO DEL ENSAYO"
        sections.append(f"{heading}:\n{formatted}")

    context = "\n\n".join(sections).strip()
    if len(context) > max_chars:
        return context[:max_chars].strip()
    return context
