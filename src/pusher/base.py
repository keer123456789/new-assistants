"""推送基类"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class PushMessage:
    title: str
    body: str           # Markdown 格式
    summary: str = ""   # 简短预览
    file_path: str = "" # 附件（可选）
    url: str = ""       # 相关链接（可选）
    level: str = "info" # info / warning / important


class BasePusher(ABC):
    @abstractmethod
    def send(self, message: PushMessage) -> bool:
        """返回是否发送成功"""
        raise NotImplementedError
