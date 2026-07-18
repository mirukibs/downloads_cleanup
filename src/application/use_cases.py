import datetime
from dataclasses import asdict
from typing import Dict, Any, List
from src.domain.models import Action
from src.application.interfaces import IFileSystem, IConfigProvider, INotifier
from src.domain.policies import ArchivePolicy
import logging

logger = logging.getLogger("cleanup_engine")

class OrganizeDownloadsUseCase:
    def __init__(
        self, 
        file_system: IFileSystem, 
        config_provider: IConfigProvider,
        notifier: INotifier,
        mime_detector: Any
    ):
        self.fs = file_system
        self.config = config_provider
        self.notifier = notifier
        self.mime_detector = mime_detector

    def execute(self, dry_run: bool = False) -> Dict[str, Any]:
        paths = self.config.get_paths()
        downloads_dir = paths.get("downloads", "")
        archive_base = paths.get("archive_base", "")
        
        rules = self.config.get_rules()
        archive_policy = self.config.get_archive_policy()
        
        files = self.fs.list_files(downloads_dir)
        counts: Dict[str, int] = {"scanned": len(files), "keyword": 0, "extension": 0, "mime": 0, "archived": 0, "errors": 0}
        actions: List[Action] = []
        
        for file_item in files:
            try:
                matched = False
                for rule in rules:
                    if rule.matches(file_item, self.mime_detector):
                        action = Action(
                            stage=rule.__class__.__name__.replace("Rule", "").lower(),
                            rule_id=rule.rule_id,
                            source_path=file_item.path,
                            target_path=None
                        )
                        matched = True
                        counts[action.stage] += 1
                        
                        if dry_run:
                            action.target_path = f"{rule.target}/{file_item.name}"
                        else:
                            self.fs.ensure_directory(rule.target)
                            dest = self.fs.move_file(file_item.path, rule.target, file_item.name)
                            action.target_path = dest
                        
                        actions.append(action)
                        break
                        
                if not matched:
                    if archive_policy.should_exclude(file_item):
                        actions.append(Action(stage="skip", rule_id="large_file", source_path=file_item.path))
                        logger.info(f"Skipping archive for large file: {file_item.name}")
                    else:
                        today = datetime.date.today().isoformat()
                        archive_dir = f"{archive_base}/{today}"
                        action = Action(stage="archive", rule_id="archive_fallback", source_path=file_item.path)
                        counts["archived"] += 1
                        
                        if dry_run:
                            action.target_path = f"{archive_dir}/{file_item.name}"
                        else:
                            self.fs.ensure_directory(archive_dir)
                            dest = self.fs.move_file(file_item.path, archive_dir, file_item.name)
                            action.target_path = dest
                            
                        actions.append(action)
                        
            except Exception as e:
                counts["errors"] += 1
                actions.append(Action(stage="error", rule_id="error", source_path=file_item.path, error=str(e)))
                logger.error(f"Error processing {file_item.name}: {e}")

        if not dry_run:
            self._evict_old_archives(archive_base, archive_policy)

        summary: Dict[str, Any] = {"counts": counts, "actions": [asdict(a) for a in actions]}
        return summary

    def _evict_old_archives(self, archive_base: str, policy: ArchivePolicy) -> None:
        now = datetime.datetime.now()
        folders = self.fs.get_archive_folders(archive_base)
        for folder in folders:
            try:
                folder_date = datetime.datetime.strptime(folder, "%Y-%m-%d")
                age_days = (now - folder_date).days
                if policy.is_archive_expired(age_days):
                    logger.info(f"Evicting old archive folder: {folder} (age: {age_days} days)")
                    self.fs.delete_directory(f"{archive_base}/{folder}")
            except ValueError:
                pass
            except Exception as e:
                logger.error(f"Error evicting archive folder {folder}: {e}")
