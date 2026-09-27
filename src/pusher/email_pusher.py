"""Email 推送 (SMTP)"""
from __future__ import annotations
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from pathlib import Path

from .base import BasePusher, PushMessage

log = logging.getLogger(__name__)


class EmailPusher(BasePusher):
    def __init__(self, smtp_host: str, smtp_port: int,
                 username: str, password: str, from_addr: str, to_addrs: list[str]):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_addr = from_addr
        self.to_addrs = to_addrs if isinstance(to_addrs, list) else [to_addrs]

    def send(self, message: PushMessage) -> bool:
        if not all([self.smtp_host, self.username, self.password, self.from_addr]):
            log.warning("Email config incomplete")
            return False
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = message.title
            msg["From"] = self.from_addr
            msg["To"] = ", ".join(self.to_addrs)

            # 纯文本 + HTML 两份
            text_part = MIMEText(message.summary or message.body[:500], "plain", "utf-8")
            html_body = f"<pre style='font-family: -apple-system, sans-serif; white-space: pre-wrap;'>{message.body}</pre>"
            html_part = MIMEText(html_body, "html", "utf-8")
            msg.attach(text_part)
            msg.attach(html_part)

            # 附件
            if message.file_path and Path(message.file_path).exists():
                with open(message.file_path, "rb") as f:
                    att = MIMEApplication(f.read())
                    att.add_header("Content-Disposition",
                                    "attachment",
                                    filename=Path(message.file_path).name)
                    msg.attach(att)

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as smtp:
                smtp.starttls()
                smtp.login(self.username, self.password)
                smtp.sendmail(self.from_addr, self.to_addrs, msg.as_string())
            log.info("Email sent to %s", self.to_addrs)
            return True
        except Exception as e:
            log.error("Email send failed: %s", e)
            return False
