from unittest.mock import patch, MagicMock
from typing import Dict, Any
from src.infrastructure.notifications import SmtpNotifier
from src.application.interfaces import IConfigProvider

class MockConfigProvider(IConfigProvider):
    def __init__(self, email_enabled: bool = True):
        self.email_enabled = email_enabled

    def get_paths(self) -> Dict[str, str]: return {}
    def get_rules(self) -> list[Any]: return []
    def get_archive_policy(self):
        from src.domain.policies import ArchivePolicy
        return ArchivePolicy(max_age_days=0, exclude_large_files_over_mb=0)
    def get_logging_config(self) -> Dict[str, Any]: return {}
    def get_notifications_config(self) -> Dict[str, Any]:
        return {
            "email_enabled": self.email_enabled,
            "email_to": "to@example.com",
            "email_from": "from@example.com",
            "smtp": {"host": "localhost", "port": 25, "user": "", "pass": "", "use_tls": False}
        }

@patch("src.infrastructure.notifications.smtplib.SMTP")
def test_smtp_notifier(mock_smtp: MagicMock):
    config = MockConfigProvider()
    notifier = SmtpNotifier(config)
    
    summary: Dict[str, Any] = {
        "counts": {"scanned": 1, "keyword": 1, "extension": 0, "mime": 0, "archived": 0, "errors": 0},
        "actions": [{"stage": "keyword", "source_path": "/test.txt", "target_path": "/dest/test.txt", "rule_id": "rule_1"}]
    }
    
    notifier.send_summary(summary)
    
    mock_smtp.assert_called_once()
    instance = mock_smtp.return_value
    instance.send_message.assert_called_once()
    
def test_smtp_notifier_disabled():
    with patch("src.infrastructure.notifications.smtplib.SMTP") as mock_smtp:
        config = MockConfigProvider(email_enabled=False)
        notifier = SmtpNotifier(config)
        notifier.send_summary({"counts": {}, "actions": []})
        mock_smtp.assert_not_called()
