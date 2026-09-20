import os

import pytest
from fastapi.testclient import TestClient

from app import MAX_BODY_BYTES, app


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.delenv("MOCK_LLM_API_KEY", raising=False)
    return TestClient(app)


def test_healthz(client: TestClient) -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_docs_disabled_by_default(client: TestClient) -> None:
    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404


def test_chat_completions_echo(client: TestClient) -> None:
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": "hello"}],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["object"] == "chat.completion"
    assert body["model"] == "gpt-4o-mini"
    assert body["choices"][0]["message"]["content"] == (
        "[gpt-4o-mini] Mock response to: hello"
    )
    assert body["id"].startswith("chatcmpl-mock-")
    assert body["usage"]["total_tokens"] >= 2


def test_chat_completions_rejects_empty_messages(client: TestClient) -> None:
    response = client.post(
        "/v1/chat/completions",
        json={"model": "mock", "messages": []},
    )
    assert response.status_code == 422


def test_chat_completions_rejects_empty_content(client: TestClient) -> None:
    response = client.post(
        "/v1/chat/completions",
        json={"model": "mock", "messages": [{"role": "user", "content": "  "}]},
    )
    assert response.status_code == 400


def test_chat_completions_multimodal_text(client: TestClient) -> None:
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "mock",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "hi"},
                        {"type": "image_url", "image_url": {"url": "https://x"}},
                    ],
                }
            ],
        },
    )
    assert response.status_code == 200
    assert "hi" in response.json()["choices"][0]["message"]["content"]


def test_chat_completions_rejects_stream(client: TestClient) -> None:
    response = client.post(
        "/v1/chat/completions",
        json={
            "model": "mock",
            "messages": [{"role": "user", "content": "hi"}],
            "stream": True,
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Streaming is not supported"


def test_oversized_body_rejected(client: TestClient) -> None:
    response = client.post(
        "/v1/chat/completions",
        content=b"{}",
        headers={"Content-Length": str(MAX_BODY_BYTES + 1)},
    )
    assert response.status_code == 413


def test_models_list(client: TestClient) -> None:
    response = client.get("/v1/models")
    assert response.status_code == 200
    assert response.json()["data"][0]["id"] == "mock-llm"


def test_api_key_required_when_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MOCK_LLM_API_KEY", "secret-token")
    client = TestClient(app)

    denied = client.post(
        "/v1/chat/completions",
        json={"model": "mock", "messages": [{"role": "user", "content": "hi"}]},
    )
    assert denied.status_code == 401

    health = client.get("/healthz")
    assert health.status_code == 200

    allowed = client.post(
        "/v1/chat/completions",
        headers={"Authorization": "Bearer secret-token"},
        json={"model": "mock", "messages": [{"role": "user", "content": "hi"}]},
    )
    assert allowed.status_code == 200

    wrong = client.get("/v1/models", headers={"Authorization": "Bearer other"})
    assert wrong.status_code == 401
