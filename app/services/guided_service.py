from fastapi import HTTPException

GUIDED_STAGES = [
    "idea",
    "estructura",
    "introduccion",
    "desarrollo",
    "contraargumento",
    "conclusion",
    "completado",
]


def validate_stage_transition(previous_stage: str, next_stage: str) -> None:
    if previous_stage not in GUIDED_STAGES or next_stage not in GUIDED_STAGES:
        raise HTTPException(status_code=400, detail="Fase de guía inválida.")
    prev_idx = GUIDED_STAGES.index(previous_stage)
    next_idx = GUIDED_STAGES.index(next_stage)
    if next_idx < prev_idx or next_idx > prev_idx + 1:
        raise HTTPException(
            status_code=400,
            detail=f"Transición inválida de fase: {previous_stage} -> {next_stage}",
        )


def update_stage_content(guided_state, stage: str, text: str) -> None:
    if not text:
        return
    attr = f"stage_{stage}"
    if hasattr(guided_state, attr):
        setattr(guided_state, attr, text)
