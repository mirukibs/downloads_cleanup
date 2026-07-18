from dataclasses import dataclass
from typing import Optional

@dataclass
class FileItem:
    name: str
    path: str
    size_mb: float
    extension: str

@dataclass
class Action:
    stage: str
    rule_id: str
    source_path: str
    target_path: Optional[str] = None
    error: Optional[str] = None
