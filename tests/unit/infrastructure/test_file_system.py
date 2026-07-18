import os
from pathlib import Path
from src.infrastructure.file_system import LocalFileSystemAdapter

def test_list_files(tmp_path: Path):
    fs = LocalFileSystemAdapter()
    
    file1 = tmp_path / "file1.txt"
    file1.write_text("hello")
    
    # Create a directory (should be ignored)
    sub = tmp_path / "subdir"
    sub.mkdir()
    
    items = fs.list_files(str(tmp_path))
    assert len(items) == 1
    assert items[0].name == "file1.txt"
    assert items[0].extension == "txt"

def test_move_file(tmp_path: Path):
    fs = LocalFileSystemAdapter()
    
    src_file = tmp_path / "src.txt"
    src_file.write_text("data")
    
    dest_dir = tmp_path / "dest"
    fs.ensure_directory(str(dest_dir))
    
    result = fs.move_file(str(src_file), str(dest_dir), "src.txt")
    
    assert os.path.exists(result)
    assert not os.path.exists(str(src_file))
    assert open(result).read() == "data"
