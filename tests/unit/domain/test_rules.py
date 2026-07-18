from src.domain.models import FileItem
from src.domain.rules import KeywordRule, ExtensionRule, MimeRule
from src.domain.interfaces import IMimeDetector

class MockMimeDetector(IMimeDetector):
    def detect(self, path: str) -> str:
        if "img" in path:
            return "image/png"
        return "application/octet-stream"

def test_keyword_rule():
    rule = KeywordRule(keyword="invoice", target="/finance")
    item = FileItem("invoice_2026.pdf", "/invoice_2026.pdf", 1.0, "pdf")
    assert rule.matches(item, None)
    
    item_fail = FileItem("report.pdf", "/report.pdf", 1.0, "pdf")
    assert not rule.matches(item_fail, None)

def test_extension_rule():
    rule = ExtensionRule(extension="pdf", target="/docs")
    item = FileItem("report.pdf", "/report.pdf", 1.0, "pdf")
    assert rule.matches(item, None)

    item_fail = FileItem("report.txt", "/report.txt", 1.0, "txt")
    assert not rule.matches(item_fail, None)

def test_mime_rule():
    detector = MockMimeDetector()
    rule = MimeRule(mime_pattern="image", target="/pictures")
    
    item = FileItem("img_001.png", "/img_001.png", 1.0, "png")
    assert rule.matches(item, detector)
    
    item_fail = FileItem("report.pdf", "/report.pdf", 1.0, "pdf")
    assert not rule.matches(item_fail, detector)
