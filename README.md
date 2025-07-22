# **Email Classification using SBERT**

A fast, containerized email classification service built with FastAPI. It ingests emails via Gmail API, classifies them using a machine learning model, and exposes a RESTful API for predictions.

## Features

* **Email Ingestion**: Connects to Gmail via OAuth2 and fetches emails for classification.
* **ML Classification**: Leverages SBERT embeddings fed into a sequential neural network to classify emails into categories such as Academics, Clubs, Internships, or Seminars.
* **RESTful API**: Exposes endpoints for submitting raw email content and receiving predicted labels.
* **Dockerized**: Ready for container deployment with a `Dockerfile` and `docker-compose.yml`.
* **Environment-Based Config**: Securely manage credentials and settings using environment variables or secret ARNs.
* **Automated Testing**: Includes pytest suite with high coverage for API and classification logic.
* **CI/CD Pipeline**: GitHub Actions workflow for linting, testing, building, and publishing Docker images.

---

## Getting Started

### Prerequisites

* **Python 3.11**
* **conda or pip** for virtual environments
* **Docker & Docker Compose** (optional, for containerized deployment)
* **Gmail API Credentials** (OAuth2 JSON)

---

## Installation & Configuration

We have two separate services in this repo:

1. **Ingestion Service** (Gmail listener & orchestrator)
2. **Classification Service** (SBERT + sequential NN model API)

Follow the steps below for each.

### 1. Ingestion Service

**Clone & install dependencies**

```bash
# From repo root
cd server
python3.11 -m venv venv
source venv/bin/activate   # or `conda activate <env>`
pip install --upgrade -r requirements.txt
```

**Configure environment**

Copy the example and fill in your Gmail credentials:

```bash
cp .env.example .env
# edit .env to include:
# GOOGLE_APPLICATION_CREDENTIALS_JSON=<full OAuth2 JSON or path>
# GOOGLE_TOKEN_PATH=./token.json
# OAUTH2_REDIRECT_URI=http://localhost:8001/oauth2callback
```

**(Optional) Docker**

To build and run in a container:

```bash
cd server
docker build -t email-classifier-server:latest .
# run locally
docker run -d \
  --name email-classifier-server \
  -p 8001:8001 \
  email-classifier-server:latest
```

---

### 2. Classification Service

**Install dependencies**

```bash
# From repo root
cd src
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

**(Optional) Docker**

```bash
cd src
docker build -t email-classifier:latest .
docker run -d \
  --name email-classifier \
  -p 8000:8000 \
  email-classifier:latest
```

---

## Running the Services

You can run each service independently or together via Docker Compose.

### Local Development

1. **Ingestion Service** (port 8001):

   ```bash
   cd server
   source venv/bin/activate
   uvicorn src.app:app --reload --host 0.0.0.0 --port 8001
   ```

2. **Classification Service** (port 8002):

   ```bash
   cd src
   source venv/bin/activate
   uvicorn config.api:app --reload --host 0.0.0.0 --port 8002
   ```

---

## Usage

### API Endpoints

| Method | Endpoint   | Description                |
| ------ | ---------- | -------------------------- |
|        |            |                            |
| POST   | `/predict` | Classify raw email payload |

#### Example: Classify Email

```bash
curl -X POST http://localhost:8001/predict \
  -d '{ "message": "some email related to academics" }'
```

Response:

```json
{ "prediction": "Academics", "id": 0 }
```

---

## Testing

Run the pytest suite:

```bash
pytest --maxfail=1 --disable-warnings -q
```

Ensure all tests pass before merging.

---

## CI/CD

A GitHub Actions workflow (`.github/workflows/server_ci.yml`) automates:

* **Linting** (`flake8`, `black`)
* **Testing** (`pytest`)
* **Docker Build & Push**
* **Deployment** to AWS App Runner / DockerHub (on push to `main`)

---

## Project Structure

```
.
├── .github                    # GitHub workflows and configs
├── data/                      # Raw and processed datasets
├── models/                    # Saved ML models and artifacts
├── notebooks/                 # Exploration and experiment notebooks
├── scripts/                   # Utility scripts (data extraction)
├── server/                    # Gmail ingestion & orchestration service
│   └── src/
│       ├── __init__.py
│       ├── app.py             # FastAPI app for fetching & forwarding emails
│       ├── auth.py            # OAuth2 authentication handlers
│       ├── credentials.json   # Gmail API credentials (gitignored)
│       ├── gmail_client.py    # Gmail API client logic
│       ├── gmail_logs.log     # Runtime email logs
│       └── token.json         # OAuth2 token storage
│       
│   ├── tests/                 # Pytest cases for ingestion service
│   ├── Dockerfile             # Container build for ingestion service
│   ├── .dockerignore
│   ├── .env                   # Service-specific environment variables
│   └── requirements.txt
├── src/                       # Classification API service
│   ├── config/
│       ├── raw_prototypes.yml
│   ├── __init__.py
│   ├── api.py             # REST endpoints for prediction
│   ├── embeddings.py      # SBERT embedding extraction
│   ├── inference.py       # Model inference logic
│   ├── preprocess.py      # Email text preprocessing
│   ├── train.py           # Training pipeline for sequential NN
├── tests/                 # Pytest cases for classification service
├── Dockerfile                 # (Optional) Root-level Dockerfile or example
├── docker-compose.yml         # Orchestrate both services together
└── requirements.txt           # Shared dependencies
```

---

## Technologies

* **Language & Framework**: Python 3.11, FastAPI
* **ML**: SBERT embeddings fed into a sequential neural network (model saved in `models/`)
* **Containerization**: Docker
* **Auth & API**: Google OAuth2, Gmail API
* **CI/CD**: GitHub Actions
* **Testing**: pytest

---

## Contact

**Maintainer**: Karthik Gnana Ezhil S.
**Email**: [skgezhil2005@gmail.com](mailto:skgezhil2005@gmail.com)
