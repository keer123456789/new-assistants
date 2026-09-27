"""Server酱 (推送到微信)"""
from __future__ import annotations
import logging

import httpx

from .base import BasePusher, PushMessage

log = logging.getLogger(__name__)


class ServerChanPusher(BasePusher):
    """
    Server酱 Turbomini 版
    文档：https://sct.ftqq.com/
    """

    def __init__(self, send_key: str, proxy: str = ""):
        self.send_key = send_key
        self.endpoint = f"https://sctapi.ftqq.com/{send_key}.send"
        self.proxy = proxy or None

    def send(self, message: PushMessage) -> bool:
        if not self.send_key:
            return False
        try:
            data = {
                "title": message.title[:60],
                "desp": message.body[:8000],   # markdown 支持
            }
            transport = httpx.HTTPTransport(proxy=self.proxy) if self.proxy else None
            with httpx.Client(transport=transport, timeout=15) as client:
                r = client.post(self.endpoint, data=data)
                if r.status_code == 200 and r.json().get("code") == 0:
                    log.info("Server酱 sent: %s", message.title)
                    return True
                log.warning("Server酱 send %d: %s", r.status_code, r.text[:200])
                return False
        except Exception as e:
            log.error("Server酱 send failed: %s", e)
            return False
