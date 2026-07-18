import smtplib
from email.message import EmailMessage
import datetime
import logging
from typing import Dict, Any, Optional
from src.application.interfaces import INotifier, IConfigProvider

logger = logging.getLogger("cleanup_engine")

class SmtpNotifier(INotifier):
    def __init__(self, config_provider: IConfigProvider):
        self.config = config_provider.get_notifications_config()

    def send_summary(self, summary_data: Dict[str, Any], log_file: Optional[str] = None):
        if not self.config.get("email_enabled", False):
            return
            
        smtp_config = self.config.get("smtp", {})
        if not smtp_config:
            logger.warning("Email is enabled but no smtp config provided.")
            return
            
        msg = EmailMessage()
        msg["Subject"] = f"Downloads Cleanup Summary - {datetime.date.today().isoformat()}"
        msg["From"] = self.config.get("email_from", "downloads-cleanup@localhost")
        msg["To"] = self.config.get("email_to", "")
        
        counts = summary_data.get("counts", {})
        body = "Downloads Cleanup completed.\n\n"
        for k, v in counts.items():
            body += f"{k.capitalize()}: {v}\n"
        
        if counts.get("errors", 0) > 0:
            body += "\nThere were some errors during the run. Please check the logs.\n"
            
        if self.config.get("email_format", "plain") == "html":
            html_body = f"<html><body><h3>Downloads Cleanup Summary</h3><pre>{body}</pre></body></html>"
            msg.set_content(body)
            msg.add_alternative(html_body, subtype='html')
        else:
            msg.set_content(body)
            
        if self.config.get("attach_log", False) and log_file:
            try:
                with open(log_file, "rb") as f:
                    msg.add_attachment(f.read(), maintype='text', subtype='plain', filename=log_file.split("/")[-1])
            except Exception as e:
                logger.error(f"Failed to attach log to email: {e}")
                
        try:
            host = smtp_config.get("host", "localhost")
            port = smtp_config.get("port", 25)
            user = smtp_config.get("user", "")
            password = smtp_config.get("pass", "")
            use_tls = smtp_config.get("use_tls", False)
            
            server = smtplib.SMTP(host, port)
            if use_tls:
                server.starttls()
            if user and password:
                server.login(user, password)
                
            server.send_message(msg)
            server.quit()
            logger.info(f"Email summary sent to {msg['To']}")
        except Exception as e:
            logger.error(f"Failed to send email summary: {e}")
