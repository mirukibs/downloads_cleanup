from pathlib import Path
from src.infrastructure.magic_mime import MagicMimeDetector

def test_magic_mime_detector(tmp_path: Path):
    detector = MagicMimeDetector()
    
    # Create a dummy text file
    dummy_txt = tmp_path / "dummy.txt"
    dummy_txt.write_text("Hello, world!")
    
    mime_type = detector.detect(str(dummy_txt))
    assert mime_type.startswith("text/plain")
    
    # Empty file
    empty_file = tmp_path / "empty.bin"
    empty_file.write_bytes(b"")
    mime_type_empty = detector.detect(str(empty_file))
    assert mime_type_empty == "application/x-empty" or mime_type_empty == "inode/x-empty"
