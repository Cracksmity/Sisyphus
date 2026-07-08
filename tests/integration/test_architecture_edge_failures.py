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
    db_path = tmp_path / "test_sysiphus_architecture.db"
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
            "Respuesta controlada.",
            {
                "model_used": "gpt-4o-mini",
                "fallback_used": False,
                "prompt_tokens_estimate": 100,
                "completion_tokens_estimate": 30,
                "total_tokens_estimate": 130,
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


def _create_project(client: TestClient, headers: dict[str, str], title: str = "Proyecto QA") -> int:
    response = client.post("/api/projects", json={"title": title}, headers=headers)
    assert response.status_code == 200
    return response.json()["id"]


def test_sliding_window_focus_out_of_range_is_clamped_without_breaking_chat(api_client):
    client, captured, _ = api_client
    headers = {"X-Api-Token": "test-token", "X-User-Id": "qa-user-002"}

    project_id = _create_project(client, headers, "Foco fuera de rango")
    text = (
        "Primer párrafo: la culpa como método de vigilancia interior.\n\n"
        "Segundo párrafo: la lucidez frente al absurdo cotidiano.\n\n"
        "Tercer párrafo: la dignidad como resistencia."
    )
    save_response = client.put(
        f"/api/projects/{project_id}/document",
        json={"content": text},
        headers=headers,
    )
    assert save_response.status_code == 200

    chat_response = client.post(
        "/api/chat",
        json={
            "modo": "ensayo",
            "messages": [{"role": "user", "content": "Evalúa el tercer párrafo"}],
            "project_id": project_id,
            "focus_paragraph_index": 999,
            "sliding_window_radius": 2,
        },
        headers=headers,
    )
    assert chat_response.status_code == 200
    assert "VENTANA DESLIZANTE DE EDICIÓN (foco en párrafo 2, radio 2):" in captured["system_prompt"]


def test_chat_returns_500_when_ai_layer_times_out_or_crashes(db_session_factory, monkeypatch):
    os.environ["SYSIPHUS_API_TOKEN"] = "test-token"

    def override_get_db():
        db = db_session_factory()
        try:
            yield db
        finally:
            db.close()

    async def broken_run_ai_with_meta(*_args, **_kwargs):
        raise RuntimeError("simulated-timeout")

    monkeypatch.setattr("app.routers.run_ai_with_meta", broken_run_ai_with_meta)
    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as client:
            headers = {"X-Api-Token": "test-token", "X-User-Id": "qa-user-003"}
            response = client.post(
                "/api/chat",
                json={
                    "modo": "ensayo",
                    "messages": [{"role": "user", "content": "Analiza esta tesis."}],
                },
                headers=headers,
            )
            assert response.status_code == 500
            assert response.json()["detail"] == "Error interno al procesar la solicitud."
    finally:
        app.dependency_overrides.clear()


def test_save_document_accepts_near_schema_limit_and_keeps_memory_state_consistent(api_client):
    client, _, db_session_factory = api_client
    headers = {"X-Api-Token": "test-token", "X-User-Id": "qa-user-004"}

    project_id = _create_project(client, headers, "Ensayo largo al límite")
    near_limit_essay = ("absurdo responsabilidad libertad " * 600).strip()
    assert len(near_limit_essay) < 20000

    response = client.put(
        f"/api/projects/{project_id}/document",
        json={"content": near_limit_essay},
        headers=headers,
    )
    assert response.status_code == 200

    with db_session_factory() as db:
        memory = db.query(models.EssayMemory).filter(models.EssayMemory.project_id == project_id).first()
        assert memory is not None
        assert memory.chunk_count > 0
        assert memory.summary_status == "queued"
        assert memory.rag_status == "queued"


def test_save_document_rejects_payload_far_beyond_schema_limit(api_client):
    client, _, _ = api_client
    headers = {"X-Api-Token": "test-token", "X-User-Id": "qa-user-005"}
    project_id = _create_project(client, headers, "Exceso de longitud")

    over_limit_text = ("nihilismo " * 3000).strip()
    assert len(over_limit_text) > 20000

    response = client.put(
        f"/api/projects/{project_id}/document",
        json={"content": over_limit_text},
        headers=headers,
    )
    assert response.status_code == 422
