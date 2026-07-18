from abc import ABC, abstractmethod

class IMimeDetector(ABC):
    @abstractmethod
    def detect(self, path: str) -> str:
        pass
