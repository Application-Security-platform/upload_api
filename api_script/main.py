from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from facade import RepositoryFacade
import subprocess
import os
from typing import Optional

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def get_form(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})

@app.post("/repository/")
async def handle_repository(
    background_tasks: BackgroundTasks,
    repo_type: str = Form(...), 
    repo_name: str = Form(...), 
    user: str = Form(...),
    repo_file: Optional[UploadFile] = File(None), 
    repo_url: Optional[str] = Form(None)
):
    # Validate repo_name (no special characters, spaces)
    if not repo_name.isalnum():
        raise HTTPException(status_code=400, detail="Repository name must be alphanumeric")

    # Create base directory if it doesn't exist
    os.makedirs("/data/repos", exist_ok=True)

    try:
        if repo_type == "upload":
            if not repo_file:
                raise HTTPException(status_code=400, detail="No file provided")
            
            # Add file size check
            file_size = 0
            chunk_size = 1024 * 1024  # 1MB chunks
            while chunk := await repo_file.read(chunk_size):
                file_size += len(chunk)
                if file_size > 500 * 1024 * 1024:  # 500MB limit
                    raise HTTPException(status_code=400, detail="File too large")
            
            await repo_file.seek(0)
            background_tasks.add_task(RepositoryFacade.handle_upload, repo_name, repo_file)
            
        elif repo_type == "url":
            if not repo_url:
                raise HTTPException(status_code=400, detail="Repository URL is required")

        try:
            # Validate the repository URL using git ls-remote
            result = subprocess.run(
                ["git", "ls-remote", repo_url],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=30  # Add timeout
            )
            if result.returncode != 0:
                raise HTTPException(status_code=400, detail=f"Invalid repository URL: {result.stderr}")

            background_tasks.add_task(RepositoryFacade.clone_repo_from_url, repo_name, repo_url)
            
        else:
            raise HTTPException(status_code=400, detail="Invalid repository type")

        return {"message": "Repository processing started", "status": "success"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
