import os
import json
from pathlib import Path
from typing import Any, Dict
from src.infrastructure.config_parser import JsonConfigAdapter

def test_json_config_adapter(tmp_path: Path):
    config_data: Dict[str, Any] = {
        "paths": {
            "downloads": "$HOME/downloads_test",
            "archive_base": "$HOME/archive_test"
        },
        "routing": {
            "keyword_map": {"invoice": {"target": "$HOME/finance"}},
            "extension_map": {"pdf": "$HOME/docs"},
            "mime_map": {"image": "$HOME/pics"}
        },
        "archive": {
            "max_age_days": 30,
            "exclude_large_files_over_mb": 100
        },
        "logging": {"level": "debug"},
        "notifications": {"email_enabled": False}
    }
    
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(config_data))
    
    adapter = JsonConfigAdapter(str(config_file))
    
    home = os.path.expanduser("~")
    
    paths = adapter.get_paths()
    assert paths["downloads"] == f"{home}/downloads_test"
    
    rules = adapter.get_rules()
    assert len(rules) == 3
    
    policy = adapter.get_archive_policy()
    assert policy.max_age_days == 30
    assert policy.exclude_large_files_over_mb == 100
    
    log_config = adapter.get_logging_config()
    assert log_config["level"] == "debug"
    
    notif_config = adapter.get_notifications_config()
    assert notif_config["email_enabled"] is False
