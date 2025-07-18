FROM python:3.11

WORKDIR /app

COPY requirements.txt /app/requirements.txt
COPY src /app/src
COPY tests /app/tests

WORKDIR /app/src

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

ENV GOOGLE_TOKEN_PATH=/app/src/token.json

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]