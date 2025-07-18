import json
import logging
import asyncio
import os
from contextlib import asynccontextmanager
from .gmail_client import GmailMonitor
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from .auth import router as auth_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gmail_logs.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Instantiate Gmail monitor
gmail_monitor = GmailMonitor()

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     # Startup
#     try:
#         gmail_monitor.authenticate()
#         gmail_monitor.get_initial_history_id()
#         # Start monitoring in background
#         asyncio.create_task(gmail_monitor.monitor_emails())
#         logger.info("Gmail monitoring started")
#     except Exception as e:
#         logger.error(f"Failed to start Gmail monitoring: {e}")
#
#     yield
#
#     # Shutdown
#     gmail_monitor.stop_monitoring()
#     logger.info("Gmail monitoring stopped")



# FastAPI app
app = FastAPI(
    title="Gmail Email Logger",
    description="Monitor and log incoming Gmail emails",
    version="1.0.0",
    # lifespan=lifespan
)

# Register auth routes
app.include_router(auth_router)


@app.get("/")
async def root():
    return {"message": "Gmail Email Logger is running", "monitoring": gmail_monitor.monitoring}


@app.get("/status")
async def get_status():
    return {
        "monitoring": gmail_monitor.monitoring,
        "authenticated": gmail_monitor.service is not None,
        "last_history_id": gmail_monitor.last_history_id
    }


@app.get("/start-monitoring")
async def start_monitoring():
    if gmail_monitor.monitoring:
        return {"message": "Monitoring is already active"}

    try:
        if not gmail_monitor.service:
            gmail_monitor.authenticate()

        gmail_monitor.get_initial_history_id()

        asyncio.create_task(gmail_monitor.monitor_emails())
        return {"message": "Monitoring started successfully"}
    except Exception as e:
        logger.error(f"Failed to start monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/stop-monitoring")
async def stop_monitoring():
    gmail_monitor.stop_monitoring()
    return {"message": "Monitoring stopped"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)