
FROM python:3.11

WORKDIR /app

COPY src /app/src
COPY requirements.txt /app/requirements.txt
COPY models /app/models
COPY tests /app/tests

RUN pip install "fastapi[standard]"
RUN pip install --no-cache-dir --upgrade -r requirements.txt

ENV MODEL_PATH=/app/models/model_v2.keras

CMD ["fastapi", "run", "src/api.py", "--port", "8000"]