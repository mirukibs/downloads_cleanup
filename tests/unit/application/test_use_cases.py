from typing import List, Tuple, Dict, Any
from src.application.use_cases import OrganizeDownloadsUseCase
from src.application.interfaces import IFileSystem, IConfigProvider, INotifier, IMimeDetector
from src.domain.models import FileItem
from src.domain.rules import KeywordRule, ExtensionRule, MimeRule
from src.domain.policies import ArchivePolicy

class MockFileSystem(IFileSystem):
    def __init__(self, files: List[FileItem]):
        self.files = files
        self.moved: List[Tuple[str, str]] = []

    def list_files(self, directory: str) -> List[FileItem]:
        return self.files

    def move_file(self, source: str, destination_dir: str, filename: str) -> str:
        self.moved.append((source, destination_dir))
        return f"{destination_dir}/{filename}"

    def get_archive_folders(self, archive_base: str) -> List[str]:
        return []

    def delete_directory(self, path: str) -> None:
        pass

    def ensure_directory(self, path: str) -> None:
        pass

class MockConfigProvider(IConfigProvider):
    def get_paths(self) -> Dict[str, str]:
        return {"downloads": "/downloads", "archive_base": "/archive"}

    def get_rules(self) -> List[Any]:
        return [
            KeywordRule("invoice", "/finance"),
            ExtensionRule("pdf", "/documents"),
            MimeRule("image", "/pictures")
        ]

    def get_archive_policy(self) -> ArchivePolicy:
        return ArchivePolicy(max_age_days=14, exclude_large_files_over_mb=500)

    def get_logging_config(self) -> Dict[str, Any]:
        return {}

    def get_notifications_config(self) -> Dict[str, Any]:
        return {}

class MockNotifier(INotifier):
    def send_summary(self, summary_data: Dict[str, Any], log_file: str | None = None) -> None:
        pass

class MockMimeDetector(IMimeDetector):
    def detect(self, path: str) -> str:
        if "img" in path:
            return "image/png"
        return "application/octet-stream"

def test_routing_logic():
    fs = MockFileSystem([
        FileItem(name="my_invoice_2026.pdf", path="/downloads/my_invoice_2026.pdf", size_mb=1.0, extension="pdf"),
        FileItem(name="report.pdf", path="/downloads/report.pdf", size_mb=2.0, extension="pdf"),
        FileItem(name="img_001.png", path="/downloads/img_001.png", size_mb=5.0, extension="png"),
        FileItem(name="unknown.xyz", path="/downloads/unknown.xyz", size_mb=10.0, extension="xyz"),
        FileItem(name="huge.iso", path="/downloads/huge.iso", size_mb=600.0, extension="iso")
    ])
    
    use_case = OrganizeDownloadsUseCase(
        file_system=fs,
        config_provider=MockConfigProvider(),
        notifier=MockNotifier(),
        mime_detector=MockMimeDetector()
    )
    
    summary = use_case.execute()
    
    counts = summary["counts"]
    assert counts["keyword"] == 1
    assert counts["extension"] == 1
    assert counts["mime"] == 1
    assert counts["archived"] == 1
    
    actions = summary["actions"]
    assert any(a["stage"] == "keyword" and "invoice" in a["source_path"] for a in actions)
    assert any(a["stage"] == "extension" and "report" in a["source_path"] for a in actions)
    assert any(a["stage"] == "mime" and "img" in a["source_path"] for a in actions)
    assert any(a["stage"] == "archive" and "unknown" in a["source_path"] for a in actions)
    assert any(a["stage"] == "skip" and "huge" in a["source_path"] for a in actions)
