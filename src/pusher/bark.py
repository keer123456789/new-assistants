"""Bark (iOS 推送服务)"""
from __future__ import annotations
import logging
import urllib.parse

import httpx

from .base import BasePusher, PushMessage

log = logging.getLogger(__name__)


class BarkPusher(BasePusher):
    """
    Bark 推送，URL 形如 https://api.day.app/yourkey/
    也可以是自建 Bark server
    """

    def __init__(self, bark_url: str, proxy: str = ""):
        self.bark_url = bark_url.rstrip("/")
        self.proxy = proxy or None

    def send(self, message: PushMessage) -> bool:
        if not self.bark_url:
            return False
        try:
            # Bark URL: /{key}/{title}/{body}
            encoded_title = urllib.parse.quote(message.title[:60])
            body = message.summary or message.body[:500]
            encoded_body = urllib.parse.quote(body)

            url = f"{self.bark_url}/{encoded_title}/{encoded_body}"
            if message.url:
                encoded_url = urllib.parse.quote(message.url, safe="")
                url += f"?url={encoded_url}"

            transport = httpx.HTTPTransport(proxy=self.proxy) if self.proxy else None
            with httpx.Client(transport=transport, timeout=15) as client:
                r = client.get(url)
                if r.status_code == 200:
                    log.info("Bark sent: %s", message.title)
                    return True
                log.warning("Bark send %d: %s", r.status_code, r.text[:200])
                return False
        except Exception as e:
            log.error("Bark send failed: %s", e)
            return False
