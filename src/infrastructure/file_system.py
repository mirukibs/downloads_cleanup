from typing import List
from pathlib import Path
import os
import shutil
from src.domain.models import FileItem
from src.application.interfaces import IFileSystem

class LocalFileSystemAdapter(IFileSystem):
    def list_files(self, directory: str) -> List[FileItem]:
        files: List[FileItem] = []
        dir_path = Path(directory)
        if not dir_path.exists():
            return files
            
        for file_entry in dir_path.iterdir():
            if file_entry.name.startswith("."):
                continue
            try:
                if file_entry.is_file():
                    size_mb = file_entry.stat().st_size / (1024 * 1024)
                    files.append(FileItem(
                        name=file_entry.name,
                        path=str(file_entry),
                        size_mb=size_mb,
                        extension=file_entry.suffix.lstrip('.')
                    ))
            except Exception:
                continue
        return sorted(files, key=lambda f: f.name.lower())

    def move_file(self, source: str, destination_dir: str, filename: str) -> str:
        dest_dir_path = Path(destination_dir)
        dest_path = dest_dir_path / filename
        
        if dest_path.exists():
            stem = Path(filename).stem
            suffix = Path(filename).suffix
            counter = 1
            while True:
                candidate = dest_dir_path / f"{stem} ({counter}){suffix}"
                if not candidate.exists():
                    dest_path = candidate
                    break
                counter += 1
                
        try:
            os.replace(source, str(dest_path))
        except OSError:
            shutil.move(source, str(dest_path))
            
        return str(dest_path)

    def get_archive_folders(self, archive_base: str) -> List[str]:
        base_path = Path(archive_base)
        if not base_path.exists():
            return []
        return [p.name for p in base_path.iterdir() if p.is_dir()]

    def delete_directory(self, path: str):
        shutil.rmtree(path)

    def ensure_directory(self, path: str):
        Path(path).mkdir(parents=True, exist_ok=True)
