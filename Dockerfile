FROM python:3.11-slim

WORKDIR /app

COPY . /app

# Install dependencies
RUN pip install --no-cache-dir ".[cpu]" pytest fastapi uvicorn

# Set explicit cache directory for the model
ENV HF_HOME=/app/hf_cache

# Pre-download the model and create a dummy pytorch_model.bin to bypass GLiNER bug
# This ensures the model is baked into the image and works offline
RUN python3 -c "from huggingface_hub import snapshot_download; import os; path = snapshot_download('deepanwa/NuNerZero_onnx'); open(os.path.join(path, 'pytorch_model.bin'), 'w').close()"

# Expose the API port
EXPOSE 8000

# Default command: Start the API server
CMD ["uvicorn", "zink.server:app", "--host", "0.0.0.0", "--port", "8000"]
