import git
import os
import shutil
from pathlib import Path

class RepositoryFacade:
    REPO_BASE_PATH = '/data/repos'

    @classmethod
    def _ensure_clean_directory(cls, path: str):
        if os.path.exists(path):
            shutil.rmtree(path)
        os.makedirs(path, exist_ok=True)

    @classmethod
    async def handle_upload(cls, repo_name: str, uploaded_file) -> str:
        upload_path = os.path.join(cls.REPO_BASE_PATH, repo_name)
        try:
            cls._ensure_clean_directory(upload_path)
            
            # Save file in chunks to handle large files
            chunk_size = 1024 * 1024  # 1MB chunks
            with open(upload_path, 'wb') as dest:
                while chunk := await uploaded_file.read(chunk_size):
                    dest.write(chunk)
            
            return upload_path
        except Exception as e:
            if os.path.exists(upload_path):
                shutil.rmtree(upload_path)
            raise Exception(f"Failed to handle upload: {str(e)}")

    @classmethod
    def clone_repo_from_url(cls, repo_name: str, repo_url: str) -> str:
        clone_path = os.path.join(cls.REPO_BASE_PATH, repo_name)
        try:
            cls._ensure_clean_directory(clone_path)
            git.Repo.clone_from(repo_url, clone_path, depth=1)  # depth=1 for shallow clone
            return clone_path
        except Exception as e:
            if os.path.exists(clone_path):
                shutil.rmtree(clone_path)
            raise Exception(f"Failed to clone repository: {str(e)}")
