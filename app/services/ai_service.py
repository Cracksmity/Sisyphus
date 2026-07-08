from fastapi import HTTPException
from app.ai_logic import generate_chat_response
import json
import math
from hashlib import sha256


MODEL_BY_MODE = {
    "ensayo": "gpt-4o",
    "mejora": "gpt-4o-mini",
    "critica": "gpt-4o-mini",
    "estilo": "gpt-4o",
    "guia": "gpt-4o-mini",
}

from cachetools import TTLCache

# Caché de respuestas con límite de tamaño y TTL de 1 hora.
# max_size=512 evita crecimiento ilimitado en memoria.
# ttl=3600 garantiza que las respuestas no se sirven indefinidamente si el contenido cambia.
_response_cache: TTLCache = TTLCache(maxsize=512, ttl=3600)

MODE_INPUT_BUDGET = {
    "ensayo": 9000,
    "mejora": 6500,
    "critica": 6500,
    "estilo": 7500,
    "guia": 7000,
}

MODEL_OUTPUT_TOKENS = {
    "gpt-4o": 1400,
    "gpt-4o-mini": 1200,
}

FALLBACK_MODEL_BY_MODE = {
    "ensayo": "gpt-4o-mini",
    "estilo": "gpt-4o-mini",
}


def _estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, math.ceil(len(text) / 4))


def _cache_key(messages: list[dict], system_prompt: str, model: str, max_tokens: int) -> str:
    payload = {"messages": messages, "system_prompt": system_prompt, "model": model, "max_tokens": max_tokens}
    return sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def _trim_messages(messages: list[dict], max_input_tokens: int) -> tuple[list[dict], int]:
    kept: list[dict] = []
    running_tokens = 0

    for msg in reversed(messages):
        content = (msg.get("content") or "").strip()
        if not content:
            continue
        msg_tokens = _estimate_tokens(content)
        if msg_tokens + running_tokens > max_input_tokens:
            remaining = max_input_tokens - running_tokens
            if remaining <= 48:
                break
            max_chars = remaining * 4
            content = content[-max_chars:]
            msg_tokens = _estimate_tokens(content)
            if msg_tokens + running_tokens > max_input_tokens:
                break
        kept.append({"role": msg.get("role", "user"), "content": content})
        running_tokens += msg_tokens
        if running_tokens >= max_input_tokens:
            break

    kept.reverse()
    return kept, running_tokens


def _build_budgeted_payload(messages: list[dict], system_prompt: str, mode: str) -> tuple[list[dict], str, dict]:
    preferred_model = MODEL_BY_MODE.get(mode, "gpt-4o-mini")
    model = preferred_model
    fallback_used = False

    system_prompt = (system_prompt or "").strip()
    max_system_tokens = 2200
    if _estimate_tokens(system_prompt) > max_system_tokens:
        system_prompt = system_prompt[: max_system_tokens * 4]

    mode_budget = MODE_INPUT_BUDGET.get(mode, 6500)
    raw_prompt_tokens = _estimate_tokens(system_prompt) + sum(_estimate_tokens((msg.get("content") or "")) for msg in messages)
    if raw_prompt_tokens > int(mode_budget * 1.2) and mode in FALLBACK_MODEL_BY_MODE:
        model = FALLBACK_MODEL_BY_MODE[mode]
        fallback_used = model != preferred_model

    system_tokens = _estimate_tokens(system_prompt)
    message_budget = max(400, mode_budget - system_tokens)
    trimmed_messages, message_tokens = _trim_messages(messages, message_budget)
    prompt_tokens_estimate = system_tokens + message_tokens

    if prompt_tokens_estimate > mode_budget and mode in FALLBACK_MODEL_BY_MODE and not fallback_used:
        model = FALLBACK_MODEL_BY_MODE[mode]
        fallback_used = model != preferred_model
        tighter_budget = int(mode_budget * 0.85)
        message_budget = max(320, tighter_budget - system_tokens)
        trimmed_messages, message_tokens = _trim_messages(messages, message_budget)
        prompt_tokens_estimate = system_tokens + message_tokens

    max_response_tokens = MODEL_OUTPUT_TOKENS.get(model, 1200)
    metadata = {
        "model_used": model,
        "fallback_used": fallback_used,
        "prompt_tokens_estimate": prompt_tokens_estimate,
        "max_response_tokens": max_response_tokens,
        "mode_budget_tokens": mode_budget,
        "raw_prompt_tokens_estimate": raw_prompt_tokens,
        "system_tokens_estimate": system_tokens,
        "messages_tokens_estimate": message_tokens,
    }
    return trimmed_messages, system_prompt, metadata


async def run_ai_with_meta(messages: list[dict], system_prompt: str, mode: str) -> tuple[str, dict]:
    trimmed_messages, trimmed_system_prompt, metadata = _build_budgeted_payload(messages, system_prompt, mode)
    key = _cache_key(trimmed_messages, trimmed_system_prompt, metadata["model_used"], metadata["max_response_tokens"])
    if key in _response_cache:
        metadata["cached"] = True
        return _response_cache[key], metadata
    try:
        response = await generate_chat_response(
            trimmed_messages,
            trimmed_system_prompt,
            model=metadata["model_used"],
            max_tokens=metadata["max_response_tokens"],
        )
        _response_cache[key] = response
        metadata["cached"] = False
        metadata["completion_tokens_estimate"] = _estimate_tokens(response)
        metadata["total_tokens_estimate"] = metadata["prompt_tokens_estimate"] + metadata["completion_tokens_estimate"]
        return response, metadata
    except Exception:
        raise HTTPException(status_code=502, detail="Error al consultar el modelo de IA.")


async def run_ai(messages: list[dict], system_prompt: str, mode: str) -> str:
    response, _ = await run_ai_with_meta(messages, system_prompt, mode)
    return response
