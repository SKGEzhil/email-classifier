
FROM python:3.11

WORKDIR /app

ARG HF_TOKEN

COPY src /app/src
COPY requirements.txt /app/requirements.txt
#COPY models /app/models
COPY tests /app/tests

# ── fetch exactly one model file from HF ─────────────────────────────────
RUN pip install --no-cache-dir huggingface_hub && \
    rm -rf /app/models && mkdir -p /app/models && \
    python - <<EOF
import os
from huggingface_hub import hf_hub_download

hf_hub_download(
    repo_id="skgezhil2005/email_classifier",
    filename="model_v2.keras",
    local_dir="/app/models",
    token=os.environ["HF_TOKEN"]
)
EOF
# ─────────────────────────────────────────────────────────────────────────




RUN pip install "fastapi[standard]"
RUN pip install --no-cache-dir --upgrade -r requirements.txt

ENV MODEL_PATH=/app/models/model_v2.keras

CMD ["fastapi", "run", "src/api.py", "--port", "8000"]