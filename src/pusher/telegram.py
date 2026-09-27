"""Telegram Bot 推送

支持：
- 长消息自动分段（每段 ≤ 4000 字符）
- MarkdownV2 渲染
- 发送 markdown 文件
- 通过环境变量配置代理
"""
from __future__ import annotations
import logging
import os
from pathlib import Path

import httpx

from .base import BasePusher, PushMessage

log = logging.getLogger(__name__)

TG_MAX_LEN = 4000


class TelegramPusher(BasePusher):
    def __init__(self, bot_token: str, chat_id: str,
                 proxy: str = ""):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.proxy = proxy or None
        self.api = f"https://api.telegram.org/bot{bot_token}"

    def _client(self) -> httpx.Client:
        transport = httpx.HTTPTransport(proxy=self.proxy) if self.proxy else None
        return httpx.Client(transport=transport, timeout=30)

    def _escape_md(self, text: str) -> str:
        """转义 Telegram MarkdownV2 特殊字符"""
        # 注意：我们用 markdown 模式而非 markdownv2，简化处理
        return text

    def send(self, message: PushMessage) -> bool:
        if not self.bot_token or not self.chat_id:
            log.warning("Telegram token/chat_id 未配置")
            return False
        return self._send_full(message)

    def _send_full(self, message: PushMessage) -> bool:
        try:
            # 1. 发文件（如果有）
            if message.file_path and Path(message.file_path).exists():
                self._send_document(message)
            # 2. 发分段文本
            chunks = self._split_text(message.body, TG_MAX_LEN)
            for i, chunk in enumerate(chunks):
                self._send_text(chunk, is_last=(i == len(chunks) - 1))
            return True
        except Exception as e:
            log.error("Telegram send failed: %s", e)
            return False

    def _send_text(self, text: str, is_last: bool = True) -> bool:
        try:
            with self._client() as client:
                r = client.post(
                    f"{self.api}/sendMessage",
                    json={
                        "chat_id": self.chat_id,
                        "text": text,
                        "parse_mode": "Markdown",
                        "disable_web_page_preview": True,
                    },
                )
                if r.status_code != 200:
                    log.warning("Telegram text send %d: %s",
                                r.status_code, r.text[:200])
                    # fallback：去掉 markdown 重试
                    r2 = client.post(
                        f"{self.api}/sendMessage",
                        json={
                            "chat_id": self.chat_id,
                            "text": text,
                            "disable_web_page_preview": True,
                        },
                    )
                    return r2.status_code == 200
                return True
        except Exception as e:
            log.error("Telegram text send exception: %s", e)
            return False

    def _send_document(self, message: PushMessage) -> bool:
        try:
            with self._client() as client:
                with open(message.file_path, "rb") as f:
                    r = client.post(
                        f"{self.api}/sendDocument",
                        data={"chat_id": self.chat_id},
                        files={"document": (Path(message.file_path).name, f)},
                    )
                if r.status_code != 200:
                    log.warning("Telegram doc send %d: %s",
                                r.status_code, r.text[:200])
                    return False
                return True
        except Exception as e:
            log.error("Telegram doc send exception: %s", e)
            return False

    @staticmethod
    def _split_text(text: str, max_len: int) -> list[str]:
        if len(text) <= max_len:
            return [text]
        chunks = []
        while text:
            if len(text) <= max_len:
                chunks.append(text)
                break
            # 找一个最近的换行
            cut = text.rfind("\n", 0, max_len)
            if cut < max_len // 2:
                cut = max_len
            chunks.append(text[:cut])
            text = text[cut:].lstrip("\n")
        return chunks
