from src.domain.models import FileItem

def test_file_item_properties():
    item = FileItem(name="report.pdf", path="/downloads/report.pdf", size_mb=1.5, extension="pdf")
    assert item.name == "report.pdf"
    assert item.path == "/downloads/report.pdf"
    assert item.size_mb == 1.5
    assert item.extension == "pdf"
