import json
import os
from pathlib import Path
from typing import Dict, Any, List
from src.application.interfaces import IConfigProvider
from src.domain.rules import Rule, KeywordRule, ExtensionRule, MimeRule
from src.domain.policies import ArchivePolicy

class JsonConfigAdapter(IConfigProvider):
    def __init__(self, config_path: str):
        self.config_path = config_path
        self._config_data = self._load_config()
        self._expand_paths()

    def _load_config(self) -> Dict[str, Any]:
        path = Path(self.config_path).expanduser()
        if not path.is_file():
            raise FileNotFoundError(f"Config file not found: {path}")
        return json.loads(path.read_text(encoding='utf-8'))

    def _expand(self, raw_path: Any) -> Any:
        if not isinstance(raw_path, str):
            return raw_path
        return os.path.expandvars(os.path.expanduser(raw_path))

    def _expand_paths(self):
        if "paths" in self._config_data:
            for k, v in self._config_data["paths"].items():
                self._config_data["paths"][k] = self._expand(v)
                
        if "logging" in self._config_data:
            for k, v in self._config_data["logging"].items():
                if isinstance(v, str):
                    self._config_data["logging"][k] = self._expand(v)
                
        routing = self._config_data.get("routing", {})
        if "keyword_map" in routing:
            for k, v in routing["keyword_map"].items():
                if "target" in v:
                    v["target"] = self._expand(v["target"])
                    
        if "extension_map" in routing:
            for k, v in routing["extension_map"].items():
                routing["extension_map"][k] = self._expand(v)
                
        if "mime_map" in routing:
            for k, v in routing["mime_map"].items():
                routing["mime_map"][k] = self._expand(v)
                
        if "notifications" in self._config_data:
            if "smtp" in self._config_data["notifications"]:
                smtp = self._config_data["notifications"]["smtp"]
                if "user" in smtp:
                    smtp["user"] = self._expand(smtp["user"])
                if "pass" in smtp:
                    smtp["pass"] = self._expand(smtp["pass"])

    def get_paths(self) -> Dict[str, str]:
        return self._config_data.get("paths", {})

    def get_rules(self) -> List[Rule]:
        rules: List[Rule] = []
        routing = self._config_data.get("routing", {})
        
        keyword_map = routing.get("keyword_map", {})
        for keyword, rule_data in keyword_map.items():
            rules.append(KeywordRule(keyword, rule_data.get("target", "")))
            
        extension_map = routing.get("extension_map", {})
        for ext, target in extension_map.items():
            rules.append(ExtensionRule(ext, target))
            
        mime_map = routing.get("mime_map", {})
        for mime, target in mime_map.items():
            rules.append(MimeRule(mime, target))
            
        return rules

    def get_archive_policy(self) -> ArchivePolicy:
        archive_config = self._config_data.get("archive", {})
        return ArchivePolicy(
            max_age_days=archive_config.get("max_age_days", 0),
            exclude_large_files_over_mb=archive_config.get("exclude_large_files_over_mb", 0)
        )

    def get_logging_config(self) -> Dict[str, Any]:
        return self._config_data.get("logging", {})

    def get_notifications_config(self) -> Dict[str, Any]:
        return self._config_data.get("notifications", {})
