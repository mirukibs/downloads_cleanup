from src.domain.policies import ArchivePolicy
from src.domain.models import FileItem

def test_archive_policy():
    policy = ArchivePolicy(max_age_days=14, exclude_large_files_over_mb=500.0)
    
    # Needs archive: small file (not excluded)
    item_small = FileItem("test.txt", "/test.txt", 1.0, "txt")
    assert not policy.should_exclude(item_small)
    
    # Exclude: large file
    item_large = FileItem("huge.iso", "/huge.iso", 600.0, "iso")
    assert policy.should_exclude(item_large)
    
    # Check expiry
    assert not policy.is_archive_expired(10)
    assert policy.is_archive_expired(20)
