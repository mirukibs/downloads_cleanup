import mimetypes
from typing import Any
from src.domain.interfaces import IMimeDetector

class MagicMimeDetector(IMimeDetector):
    def __init__(self):
        try:
            import magic
            self.magic: Any = magic
            self.have_magic = True
        except ImportError:
            self.magic = None
            self.have_magic = False

    def detect(self, path: str) -> str:
        if self.have_magic:
            try:
                return self.magic.from_file(path, mime=True)
            except Exception:
                pass
        guessed, _ = mimetypes.guess_type(path)
        return guessed or ""
