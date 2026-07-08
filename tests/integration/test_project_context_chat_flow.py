import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import models
from app.database import get_db
from main import app


@pytest.fixture()
def db_session_factory(tmp_path):
    db_path = tmp_path / "test_sysiphus.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    SessionTesting = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    models.Base.metadata.create_all(bind=engine)
    try:
        yield SessionTesting
    finally:
        engine.dispose()


@pytest.fixture()
def api_client(db_session_factory, monkeypatch):
    os.environ["SYSIPHUS_API_TOKEN"] = "test-token"
    captured = {}

    def override_get_db():
        db = db_session_factory()
        try:
            yield db
        finally:
            db.close()

    async def fake_run_ai_with_meta(messages, system_prompt, mode):
        captured["messages"] = messages
        captured["system_prompt"] = system_prompt
        captured["mode"] = mode
        return (
            "Respuesta simulada del oráculo.",
            {
                "model_used": "gpt-4o-mini",
                "fallback_used": False,
                "prompt_tokens_estimate": 123,
                "completion_tokens_estimate": 45,
                "total_tokens_estimate": 168,
            },
        )

    monkeypatch.setattr("app.routers.refresh_project_summary_background", lambda *_, **__: None)
    monkeypatch.setattr("app.routers.run_ai_with_meta", fake_run_ai_with_meta)

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as client:
            yield client, captured, db_session_factory
    finally:
        app.dependency_overrides.clear()


def test_integration_project_save_then_chat_builds_context_and_persists_interaction(api_client):
    client, captured, db_session_factory = api_client
    headers = {"X-Api-Token": "test-token", "X-User-Id": "qa-user-001"}

    dense_essay = (
        "Sostengo que la libertad no es una conquista luminosa, sino una condena silenciosa: "
        "cada decisión arranca una posibilidad y funda una culpa. En la ciudad húmeda, donde el humo "
        "del tranvía parece una plegaria sin dios, la conciencia aprende a mirarse como si fuera extraña.\n\n"
        "Cuando la costumbre promete consuelo, aparece la sospecha: tal vez vivir no sea pertenecer, "
        "sino resistir la forma en que el mundo nos nombra. Defiendo que la dignidad humana empieza en "
        "ese instante incómodo en que dejamos de obedecer significados heredados.\n\n"
        "El absurdo no destruye la ética; la vuelve urgente. Si nada garantiza el sentido, entonces toda "
        "palabra responsable es un acto de creación moral, y todo silencio cobarde es colaboración con la inercia."
    )

    create_project_response = client.post(
        "/api/projects",
        json={"title": "Ensayo sobre libertad y absurdo"},
        headers=headers,
    )
    assert create_project_response.status_code == 200
    project_id = create_project_response.json()["id"]

    save_response = client.put(
        f"/api/projects/{project_id}/document",
        json={"content": dense_essay},
        headers=headers,
    )
    assert save_response.status_code == 200
    assert save_response.json()["status"] == "guardado"

    chat_response = client.post(
        "/api/chat",
        json={
            "modo": "ensayo",
            "messages": [{"role": "user", "content": "Critica la coherencia de mi tesis."}],
            "project_id": project_id,
            "draft_content": dense_essay,
            "oracle_prompt": "Enfatiza contradicciones internas y riesgos argumentales.",
            "focus_paragraph_index": 1,
            "sliding_window_radius": 1,
        },
        headers=headers,
    )
    assert chat_response.status_code == 200
    assert chat_response.json()["response"] == "Respuesta simulada del oráculo."

    system_prompt = captured["system_prompt"]
    assert "CONTEXTO DEL PROYECTO ACTUAL (seleccionado):" in system_prompt
    assert "MEMORIA MAESTRA (TESIS):" in system_prompt
    assert "VENTANA DESLIZANTE DE EDICIÓN" in system_prompt
    assert "FRAGMENTOS" in system_prompt

    with db_session_factory() as db:
        memory = db.query(models.EssayMemory).filter(models.EssayMemory.project_id == project_id).first()
        assert memory is not None
        assert memory.chunk_count > 0
        assert memory.thesis != ""
        assert memory.summary_status == "queued"
        assert memory.rag_status == "queued"

        interactions = (
            db.query(models.Interaction)
            .filter(models.Interaction.project_id == project_id)
            .order_by(models.Interaction.id.asc())
            .all()
        )
        assert len(interactions) == 1
        interaction = interactions[0]
        assert interaction.mode == "ensayo"
        assert interaction.user_input == "Critica la coherencia de mi tesis."
        assert interaction.ai_output == "Respuesta simulada del oráculo."
        assert interaction.model_used == "gpt-4o-mini"
        assert interaction.total_tokens_estimate == 168
        assert interaction.context_chars > 0
