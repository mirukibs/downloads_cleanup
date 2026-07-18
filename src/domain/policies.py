from .models import FileItem

class ArchivePolicy:
    def __init__(self, max_age_days: int, exclude_large_files_over_mb: float):
        self.max_age_days = max_age_days
        self.exclude_large_files_over_mb = exclude_large_files_over_mb

    def should_exclude(self, file_item: FileItem) -> bool:
        if self.exclude_large_files_over_mb <= 0:
            return False
        return file_item.size_mb > self.exclude_large_files_over_mb

    def is_archive_expired(self, age_days: int) -> bool:
        if self.max_age_days <= 0:
            return False
        return age_days > self.max_age_days
