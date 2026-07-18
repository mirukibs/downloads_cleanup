import os
import json
from pathlib import Path
from typing import Dict, Any
from src.application.use_cases import OrganizeDownloadsUseCase
from src.infrastructure.file_system import LocalFileSystemAdapter
from src.infrastructure.config_parser import JsonConfigAdapter
from src.infrastructure.magic_mime import MagicMimeDetector
from src.application.interfaces import INotifier

class DummyNotifier(INotifier):
    def send_summary(self, summary_data: Dict[str, Any], log_file: str | None = None) -> None:
        pass

def test_full_pipeline(tmp_path: Path):
    downloads_dir = tmp_path / "downloads"
    downloads_dir.mkdir()
    
    archive_dir = tmp_path / "archive"
    archive_dir.mkdir()
    
    finance_dir = tmp_path / "finance"
    
    # Create test files
    (downloads_dir / "invoice_2026.pdf").write_text("fake pdf data")
    (downloads_dir / "photo.png").write_text("fake png data")
    (downloads_dir / "unknown.xyz").write_text("fake unknown data")
    
    # Config
    config_data: Dict[str, Any] = {
        "paths": {
            "downloads": str(downloads_dir),
            "archive_base": str(archive_dir)
        },
        "routing": {
            "keyword_map": {"invoice": {"target": str(finance_dir)}},
            "extension_map": {"png": str(tmp_path / "images")},
            "mime_map": {}
        },
        "archive": {
            "max_age_days": 0, # Archive everything immediately
            "exclude_large_files_over_mb": 100
        },
        "logging": {"level": "info"},
        "notifications": {"email_enabled": False}
    }
    
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(config_data))
    
    config_adapter = JsonConfigAdapter(str(config_file))
    fs_adapter = LocalFileSystemAdapter()
    mime_detector = MagicMimeDetector()
    notifier = DummyNotifier()
    
    use_case = OrganizeDownloadsUseCase(fs_adapter, config_adapter, notifier, mime_detector)
    summary = use_case.execute()
    
    # Assertions
    assert summary["counts"]["keyword"] == 1
    assert summary["counts"]["extension"] == 1
    assert summary["counts"]["archived"] == 1
    
    assert os.path.exists(str(finance_dir / "invoice_2026.pdf"))
    assert os.path.exists(str(tmp_path / "images" / "photo.png"))
    
    # Archive puts files in year/month folders
    # Since I don't know the exact year/month it falls into in the test, I just check that unknown.xyz is gone from downloads
    assert not os.path.exists(str(downloads_dir / "unknown.xyz"))
