from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import zink

app = FastAPI(
    title="Zink Redaction API",
    description="API for redacting sensitive information using Zink.",
    version=zink.__version__
)

class RedactRequest(BaseModel):
    text: str
    labels: Optional[List[str]] = None

class RedactResponse(BaseModel):
    original_text: str
    anonymized_text: str
    replacements: List[dict]

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": zink.__version__}

@app.post("/redact", response_model=RedactResponse)
async def redact(request: RedactRequest):
    try:
        result = zink.redact(request.text, request.labels)
        return RedactResponse(
            original_text=result.original_text,
            anonymized_text=result.anonymized_text,
            replacements=[r.dict() if hasattr(r, 'dict') else r.__dict__ for r in result.replacements]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
