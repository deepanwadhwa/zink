"""Optional HTTP interface for redacting text with Zink."""

from dataclasses import asdict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import zink

app = FastAPI(
    title="Zink Redaction API",
    description="API for redacting sensitive information using Zink.",
    version=zink.__version__,
)


class RedactRequest(BaseModel):
    """Text and optional labels for one redaction request."""

    text: str
    labels: list[str] | None = None


class RedactResponse(BaseModel):
    """Original and redacted text with details for each detected span."""

    original_text: str
    anonymized_text: str
    replacements: list[dict]


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Report service status and the installed Zink version."""
    return {"status": "ok", "version": zink.__version__}


@app.post("/redact", response_model=RedactResponse)
async def redact(request: RedactRequest) -> RedactResponse:
    """Replace detected spans and serialize their original offsets and values."""
    try:
        result = zink.redact(request.text, categories=request.labels)
        return RedactResponse(
            original_text=result.original_text,
            anonymized_text=result.anonymized_text,
            replacements=[asdict(replacement) for replacement in result.replacements],
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
