FROM python:3.13-slim

WORKDIR /build/zink

# Install CPU PyTorch before GLiNER to avoid pulling CUDA packages.
RUN python -m pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY pyproject.toml README.md LICENSE ./
COPY zink ./zink
RUN python -m pip install --no-cache-dir ".[cpu,server]"

ENV HF_HOME=/opt/zink/huggingface \
    HF_HUB_DISABLE_XET=1
COPY scripts/prepare_model.py ./prepare_model.py
RUN python prepare_model.py

# Verify the installed package can use the baked-in model offline.
WORKDIR /app
ENV HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1
RUN python -c 'import zink; result = zink.redact("Alice arrived.", categories=["person"]); assert result.anonymized_text == "person_REDACTED arrived.", result.anonymized_text'

EXPOSE 8000
CMD ["uvicorn", "zink.server:app", "--host", "0.0.0.0", "--port", "8000"]
