"""RSS / Atom Feed 抓取器"""
from __future__ import annotations
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import feedparser
import httpx
from dateutil import parser as dtparser

from .base import BaseFetcher, NewsItem

log = logging.getLogger(__name__)


def fetch_rss_url(url: str, proxy: Optional[str] = None,
                  timeout: int = 30, user_agent: str = "") -> feedparser.FeedParserDict:
    """用 httpx 抓取 RSS 原始内容，返回 feedparser 解析结果"""
    headers = {"User-Agent": user_agent or "NewsAssistant/1.0"}
    transport = httpx.HTTPTransport(proxy=proxy) if proxy else None
    with httpx.Client(transport=transport, timeout=timeout,
                      follow_redirects=True, headers=headers) as client:
        resp = client.get(url)
        resp.raise_for_status()
        return feedparser.parse(resp.content)


class RSSFetcher(BaseFetcher):
    """通用 RSS/Atom 抓取器"""

    def __init__(self, source_name: str, feed_url: str,
                 proxy: Optional[str] = None, timeout: int = 30,
                 user_agent: str = "", category_hint: str = ""):
        super().__init__(source_name, proxy, timeout, user_agent)
        self.feed_url = feed_url
        self.category_hint = category_hint

    def fetch(self, hours_back: int = 24, max_items: int = 20) -> list[NewsItem]:
        log.info("[%s] fetching %s", self.source_name, self.feed_url)
        try:
            feed = fetch_rss_url(self.feed_url, self.proxy,
                                 self.timeout, self.user_agent)
        except Exception as e:
            log.warning("[%s] fetch failed: %s", self.source_name, e)
            return []

        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_back)
        items: list[NewsItem] = []
        for entry in feed.entries[:max_items * 3]:   # 先多取，按时间再过滤
            try:
                published = self._parse_date(entry)
                if published and published < cutoff:
                    continue

                title = (entry.get("title") or "").strip()
                if not title:
                    continue

                link = entry.get("link") or ""
                summary = (entry.get("summary") or entry.get("description") or "").strip()
                # 去掉 HTML
                if "<" in summary:
                    from bs4 import BeautifulSoup
                    summary = BeautifulSoup(summary, "lxml").get_text(" ", strip=True)

                author = entry.get("author", "") or ""

                items.append(NewsItem(
                    title=title,
                    url=link,
                    source=self.source_name,
                    published=published or datetime.now(timezone.utc),
                    summary=summary[:1500],
                    author=author,
                    category=self.category_hint,
                ))

                if len(items) >= max_items:
                    break
            except Exception as e:
                log.debug("[%s] skip entry: %s", self.source_name, e)
                continue

        log.info("[%s] got %d items", self.source_name, len(items))
        return items

    @staticmethod
    def _parse_date(entry) -> Optional[datetime]:
        for key in ("published_parsed", "updated_parsed", "created_parsed"):
            v = entry.get(key)
            if v:
                try:
                    return datetime(*v[:6], tzinfo=timezone.utc)
                except Exception:
                    pass
        for key in ("published", "updated"):
            v = entry.get(key)
            if v:
                try:
                    dt = dtparser.parse(v)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    return dt.astimezone(timezone.utc)
                except Exception:
                    pass
        return None
