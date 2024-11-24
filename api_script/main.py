from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from facade import RepositoryFacade
import subprocess
import os
from typing import Optional
from confluent_kafka import Producer, KafkaException
import json
from datetime import datetime
import logging
import sys

app = FastAPI()
templates = Jinja2Templates(directory="templates")

KAFKA_BOOTSTRAP_SERVERS = 'kafka-service.default.svc.cluster.local:9092'

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

class ScannerEventProducer:
    def __init__(self):
        try:
            self.producer = Producer({
                'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
                'message.max.bytes': 1000000,
                'retry.backoff.ms': 250
            })
        except Exception as e:
            print(f"Failed to initialize Kafka producer: {str(e)}")
            self.producer = None

    async def trigger_scans(self, repo_name: str, org_id: str):
        if not self.producer:
            print("Kafka producer not initialized, skipping scan triggers")
            return
            
        scan_event = {
            "repo_name": repo_name,
            "org_id": org_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            event_data = json.dumps(scan_event).encode('utf-8')
            self.producer.produce('scanner.sast', value=event_data)
            print(f"Sent sast event for {repo_name}")
            self.producer.produce('scanner.secrets', value=event_data)
            print(f"Sent secrets event for {repo_name}")
            self.producer.flush()
        except (KafkaException, BufferError) as e:
            logger.error(f"Failed to send Kafka messages: {str(e)}")

@app.get("/", response_class=HTMLResponse)
async def get_form(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})

@app.post("/repository/")
async def handle_repository(
    repo_type: str = Form(...), 
    repo_name: str = Form(...), 
    user: str = Form(...),
    repo_file: Optional[UploadFile] = File(None), 
    repo_url: Optional[str] = Form(None)
):
    try:
        if not repo_name.isalnum():
            raise HTTPException(status_code=400, detail="Repository name must be alphanumeric")

        logger.info(f"Processing repository: {repo_name}, type: {repo_type}")
        os.makedirs("/data/repos", exist_ok=True)
        scanner_producer = ScannerEventProducer()
        
        if repo_type == "upload":
            if not repo_file:
                raise HTTPException(status_code=400, detail="No file provided")
            
            logger.info(f"Processing uploaded file for repository: {repo_name}")
            
            # Add file size check
            file_size = 0
            chunk_size = 1024 * 1024  # 1MB chunks
            while chunk := await repo_file.read(chunk_size):
                file_size += len(chunk)
                if file_size > 500 * 1024 * 1024:  # 500MB limit
                    raise HTTPException(status_code=400, detail="File too large")
            
            await repo_file.seek(0)
            await RepositoryFacade.handle_upload(repo_name, repo_file)
            logger.info(f"File upload processed successfully for: {repo_name}")
            
            await scanner_producer.trigger_scans(repo_name, org_id="1611")
            
        elif repo_type == "url":
            if not repo_url:
                raise HTTPException(status_code=400, detail="Repository URL is required")

            logger.info(f"Processing repository URL: {repo_url}")

            try:
                # Validate the repository URL using git ls-remote
                result = subprocess.run(
                    ["git", "ls-remote", repo_url],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=30
                )
                if result.returncode != 0:
                    logger.error(f"Git ls-remote failed: {result.stderr}")
                    raise HTTPException(status_code=400, detail=f"Invalid repository URL: {result.stderr}")

                await RepositoryFacade.clone_repo_from_url(repo_name, repo_url)
                logger.info(f"Repository cloned successfully: {repo_name}")
                
                await scanner_producer.trigger_scans(repo_name, org_id="1611")
                
            except subprocess.TimeoutExpired:
                logger.error(f"Git operation timed out for URL: {repo_url}")
                raise HTTPException(status_code=408, detail="Repository operation timed out")
            except Exception as e:
                logger.error(f"Error processing repository URL: {str(e)}")
                raise HTTPException(status_code=400, detail="Invalid repository type")

        return {"message": "Repository processing and scanning started", "status": "success"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
