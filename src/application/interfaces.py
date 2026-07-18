from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Protocol
from src.domain.models import FileItem
from src.domain.rules import Rule
from src.domain.policies import ArchivePolicy

class IFileSystem(ABC):
    @abstractmethod
    def list_files(self, directory: str) -> List[FileItem]:
        pass
        
    @abstractmethod
    def move_file(self, source: str, destination_dir: str, filename: str) -> str:
        pass
        
    @abstractmethod
    def get_archive_folders(self, archive_base: str) -> List[str]:
        pass
        
    @abstractmethod
    def delete_directory(self, path: str):
        pass
        
    @abstractmethod
    def ensure_directory(self, path: str):
        pass

class IConfigProvider(ABC):
    @abstractmethod
    def get_paths(self) -> Dict[str, str]:
        pass
        
    @abstractmethod
    def get_rules(self) -> List[Rule]:
        pass
        
    @abstractmethod
    def get_archive_policy(self) -> ArchivePolicy:
        pass
        
    @abstractmethod
    def get_logging_config(self) -> Dict[str, Any]:
        pass
        
    @abstractmethod
    def get_notifications_config(self) -> Dict[str, Any]:
        pass

class INotifier(ABC):
    @abstractmethod
    def send_summary(self, summary_data: Dict[str, Any], log_file: Optional[str] = None):
        pass

class IMimeDetector(Protocol):
    def detect(self, path: str) -> str:
        ...

