"""Exercise the optional server without initializing a model."""

import asyncio

import pytest

import zink


@pytest.fixture
def send_request():
    pytest.importorskip("fastapi")
    httpx = pytest.importorskip("httpx")

    from zink.server import app

    def request(method, path, **kwargs):
        async def send():
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url="http://testserver",
            ) as client:
                return await client.request(method, path, **kwargs)

        return asyncio.run(send())

    return request


def test_health_reports_version_without_inference(send_request, fake_extractor):
    def unexpected_inference(text, labels):
        pytest.fail("Health endpoint ran inference")

    fake_extractor(unexpected_inference)
    response = send_request("GET", "/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": zink.__version__}


def test_redact_serializes_original_spans(send_request, fake_extractor):
    text = "John Doe lives in New York."

    def predict(passage, labels):
        assert passage == text
        assert tuple(labels) == ("person", "location")
        return [
            {
                "start": 0,
                "end": 8,
                "label": "person",
                "text": "John Doe",
                "score": 0.99,
            },
            {
                "start": 18,
                "end": 26,
                "label": "location",
                "text": "New York",
                "score": 0.85,
            },
        ]

    fake_extractor(predict)
    response = send_request(
        "POST",
        "/redact",
        json={"text": text, "labels": ["person", "location"]},
    )

    assert response.status_code == 200
    assert response.json() == {
        "original_text": text,
        "anonymized_text": "person_REDACTED lives in location_REDACTED.",
        "replacements": [
            {
                "start": 0,
                "end": 8,
                "label": "person",
                "original": "John Doe",
                "pseudonym": "person_REDACTED",
                "score": 0.99,
            },
            {
                "start": 18,
                "end": 26,
                "label": "location",
                "original": "New York",
                "pseudonym": "location_REDACTED",
                "score": 0.85,
            },
        ],
    }


def test_redact_validates_request_text(send_request):
    response = send_request("POST", "/redact", json={"labels": ["person"]})

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "text"]
