FROM python:3.11

WORKDIR /app

COPY requirements.txt /app/requirements.txt
COPY src /app/src

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8001"]