FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV LLM_MODE=gguf
ENV GGUF_REPO=unsloth/Qwen3.5-4B-GGUF
ENV GGUF_FILENAME=*Q4_K_M*
ENV N_THREADS=4
ENV N_CTX=4096
ENV MAX_TOKENS=12

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py utils.py solver.py llm_client.py validate_output.py ./

RUN mkdir -p /data /output

CMD ["python", "main.py"]
