import git
import os
import shutil
from pathlib import Path
import aiofiles
import zipfile
from fastapi import UploadFile
import asyncio

class RepositoryFacade:
    REPO_BASE_PATH = '/data/repos'

    @classmethod
    def _ensure_clean_directory(cls, path: str):
        if os.path.exists(path):
            shutil.rmtree(path)
        os.makedirs(path, exist_ok=True)

    @classmethod
    async def handle_upload(cls, repo_name: str, repo_file: UploadFile):
        repo_path = os.path.join(cls.REPO_BASE_PATH, repo_name)
        
        # Remove directory if it exists
        if os.path.exists(repo_path):
            if os.path.isdir(repo_path):
                shutil.rmtree(repo_path)
            else:
                os.remove(repo_path)
        
        # Create directory for the repository
        os.makedirs(repo_path, exist_ok=True)
        
        # Extract the uploaded file
        file_path = os.path.join(repo_path, repo_file.filename)
        try:
            # Save the uploaded file
            async with aiofiles.open(file_path, 'wb') as f:
                while chunk := await repo_file.read(8192):
                    await f.write(chunk)
            
            # If it's a zip file, extract it
            if file_path.endswith('.zip'):
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(repo_path)
                os.remove(file_path)  # Remove the zip file after extraction
                
        except Exception as e:
            # Clean up on error
            if os.path.exists(repo_path):
                shutil.rmtree(repo_path)
            raise Exception(f"Failed to process upload: {str(e)}")

    @classmethod
    async def clone_repo_from_url(cls, repo_name: str, repo_url: str) -> str:
        clone_path = os.path.join(cls.REPO_BASE_PATH, repo_name)
        try:
            cls._ensure_clean_directory(clone_path)
            # Use asyncio.create_subprocess_exec for async git clone
            process = await asyncio.create_subprocess_exec(
                'git', 'clone', '--depth', '1', repo_url, clone_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise Exception(f"Git clone failed: {stderr.decode()}")
                
            return clone_path
        except Exception as e:
            if os.path.exists(clone_path):
                shutil.rmtree(clone_path)
            raise Exception(f"Failed to clone repository: {str(e)}")
