#!/usr/bin/env python3

import argparse
import sys
import logging
import json
import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from src.application.use_cases import OrganizeDownloadsUseCase
from dotenv import load_dotenv

load_dotenv()
from src.application.interfaces import IConfigProvider
from src.infrastructure.file_system import LocalFileSystemAdapter
from src.infrastructure.config_parser import JsonConfigAdapter
from src.infrastructure.notifications import SmtpNotifier
from src.infrastructure.magic_mime import MagicMimeDetector

logger = logging.getLogger("cleanup_engine")

def setup_logging(config_provider: IConfigProvider) -> Optional[Path]:
    log_config = config_provider.get_logging_config()
    log_dir_str = log_config.get("log_dir", "/var/log/downloads_cleanup")
    log_level_str = log_config.get("level", "info").upper()
    
    level = getattr(logging, log_level_str, logging.INFO)
    logger.setLevel(level)
    
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        log_dir = Path(log_dir_str)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        text_handler = logging.FileHandler(log_dir / "engine.log")
        text_handler.setFormatter(formatter)
        logger.addHandler(text_handler)
        
        console = logging.StreamHandler(sys.stdout)
        console.setFormatter(formatter)
        logger.addHandler(console)
        
        return log_dir
    except Exception as e:
        print(f"Failed to setup file logging: {e}", file=sys.stderr)
        console = logging.StreamHandler(sys.stdout)
        console.setFormatter(formatter)
        logger.addHandler(console)
        return None

def write_jsonl_log(
    config_provider: IConfigProvider,
    summary: Dict[str, Any],
    log_dir: Optional[Path],
) -> Optional[Path]:
    log_config = config_provider.get_logging_config()
    if not log_dir or not log_config.get("jsonl_per_run", False):
        return None
    try:
        today = datetime.date.today().isoformat()
        log_file = log_dir / f"run_{today}.jsonl"
        with log_file.open("a", encoding="utf-8") as f:
            run_data: Dict[str, Any] = {
                "timestamp": datetime.datetime.now().isoformat(),
                "counts": summary["counts"],
                "actions": summary["actions"]
            }
            f.write(json.dumps(run_data) + "\n")
        return log_file
    except Exception as e:
        logger.error(f"Failed to write jsonl log: {e}")
        return None

def pretty_print_plan(summary: Dict[str, Any], dry_run: bool) -> None:
    counts = summary["counts"]
    actions = summary["actions"]
    logger.info(f"Total files scanned: {counts['scanned']}")
    logger.info(f"Matched by keyword: {counts['keyword']}")
    logger.info(f"Matched by extension: {counts['extension']}")
    logger.info(f"Matched by mime: {counts['mime']}")
    logger.info(f"Archived fallback: {counts['archived']}")
    logger.info(f"Errors: {counts['errors']}")

    if dry_run:
        logger.info("Planned actions (dry-run):")
    else:
        logger.info("Performed actions:")
        
    for action in actions:
        if action["stage"] == "error":
            logger.error(f"[ERROR] {Path(action['source_path']).name} -> {action.get('error', '')}")
        elif action["stage"] == "skip":
            logger.info(f"[SKIP] {Path(action['source_path']).name} (rule: {action['rule_id']})")
        else:
            logger.info(f"[{action['stage'].upper():7}] {Path(action['source_path']).name} -> {action['target_path']} (rule: {action['rule_id']})")

def main():
    parser = argparse.ArgumentParser(description="Downloads Cleanup Engine (DDD)")
    parser.add_argument('--config', required=True, help='Path to config.json')
    parser.add_argument('--dry-run', action='store_true', help='Do not move files')
    args = parser.parse_args()

    # 1. Initialize Configuration Adapter
    try:
        config_provider = JsonConfigAdapter(args.config)
    except Exception as e:
        print(f"Failed to load config: {e}", file=sys.stderr)
        sys.exit(2)

    # 2. Setup Logging
    log_dir = setup_logging(config_provider)
    logger.info("Config loaded successfully.")

    # 3. Initialize Infrastructure Adapters
    file_system = LocalFileSystemAdapter()
    notifier = SmtpNotifier(config_provider)
    mime_detector = MagicMimeDetector()

    # 4. Initialize and Execute Use Case
    use_case = OrganizeDownloadsUseCase(
        file_system=file_system,
        config_provider=config_provider,
        notifier=notifier,
        mime_detector=mime_detector
    )
    
    summary = use_case.execute(dry_run=args.dry_run)
    
    pretty_print_plan(summary, args.dry_run)
    
    if not args.dry_run:
        jsonl_file = write_jsonl_log(config_provider, summary, log_dir)
        notifier.send_summary(summary, str(jsonl_file) if jsonl_file else None)

    if summary["counts"]["errors"] > 0:
        sys.exit(4)
    sys.exit(0)

if __name__ == "__main__":
    main()
