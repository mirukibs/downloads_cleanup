from abc import ABC, abstractmethod
from typing import Optional
from .models import FileItem
from src.domain.interfaces import IMimeDetector

class Rule(ABC):
    def __init__(self, target: str):
        self.target = target

    @abstractmethod
    def matches(self, file_item: FileItem, magic_mime_detector: Optional[IMimeDetector] = None) -> bool:
        pass

    @property
    @abstractmethod
    def rule_id(self) -> str:
        pass

class KeywordRule(Rule):
    def __init__(self, keyword: str, target: str):
        super().__init__(target)
        self.keyword = keyword.lower()

    def matches(self, file_item: FileItem, magic_mime_detector: Optional[IMimeDetector] = None) -> bool:
        return self.keyword in file_item.name.lower()

    @property
    def rule_id(self) -> str:
        return self.keyword

class ExtensionRule(Rule):
    def __init__(self, extension: str, target: str):
        super().__init__(target)
        self.extension = extension.lower().lstrip(".")

    def matches(self, file_item: FileItem, magic_mime_detector: Optional[IMimeDetector] = None) -> bool:
        return self.extension == file_item.extension.lower()

    @property
    def rule_id(self) -> str:
        return self.extension

class MimeRule(Rule):
    def __init__(self, mime_pattern: str, target: str):
        super().__init__(target)
        self.mime_pattern = mime_pattern.lower()

    def matches(self, file_item: FileItem, magic_mime_detector: Optional[IMimeDetector] = None) -> bool:
        if not magic_mime_detector:
            return False
        mime_type = magic_mime_detector.detect(file_item.path)
        if not mime_type:
            return False
        mime_type = mime_type.lower()
        
        if mime_type == self.mime_pattern:
            return True
            
        prefix = mime_type.split("/", 1)[0]
        if prefix == self.mime_pattern:
            return True
            
        return False

    @property
    def rule_id(self) -> str:
        return self.mime_pattern
