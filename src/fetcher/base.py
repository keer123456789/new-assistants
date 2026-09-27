"""基础抓取器类型"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional


@dataclass
class NewsItem:
    """统一的一条新闻条目"""
    title: str
    url: str
    source: str
    published: Optional[datetime] = None
    summary: str = ""              # 原始 summary (英文)
    content: str = ""              # 完整内容（如果有）
    author: str = ""
    category: str = ""             # LLM 分类后的中文类别

    # LLM 处理后的字段
    title_zh: str = ""
    summary_zh: str = ""
    keywords: list[str] = field(default_factory=list)

    # 元数据
    raw: dict = field(default_factory=dict)
    fetched_at: datetime = field(default_factory=datetime.now)
    cluster_id: Optional[str] = None     # 事件聚类 ID
    cluster_rank: int = 0                 # 聚类内重要度排名

    def to_dict(self) -> dict:
        d = asdict(self)
        for k in ("published", "fetched_at"):
            if d.get(k):
                d[k] = d[k].isoformat()
        return d


class BaseFetcher(ABC):
    """抓取器基类"""

    def __init__(self, source_name: str, proxy: Optional[str] = None,
                 timeout: int = 30, user_agent: str = ""):
        self.source_name = source_name
        self.proxy = proxy
        self.timeout = timeout
        self.user_agent = user_agent or "NewsAssistant/1.0"

    @abstractmethod
    def fetch(self, hours_back: int = 24, max_items: int = 20) -> list[NewsItem]:
        """返回新闻条目列表"""
        raise NotImplementedError
