"""20 个新闻源的配置

每个源都通过 RSS/Atom feed 抓取。极少数需要特殊处理（如 SEC EDGAR）。
"""
from __future__ import annotations
from typing import Callable, Optional

from .base import NewsItem
from .rss import RSSFetcher

# ============== 源配置 ==============

SOURCES: list[dict] = [
    # 1. Reuters
    {
        "name": "Reuters",
        "feed": "https://feeds.reuters.com/reuters/topNews",
        "category_hint": "国际",
    },
    {
        "name": "Reuters World",
        "feed": "https://feeds.reuters.com/Reuters/worldNews",
        "category_hint": "国际",
    },
    {
        "name": "Reuters Business",
        "feed": "https://feeds.reuters.com/reuters/businessNews",
        "category_hint": "经济",
    },
    # 2. Associated Press
    {
        "name": "AP News",
        "feed": "https://feeds.apnews.com/rss/apf-topnews",
        "category_hint": "国际",
    },
    # 3. BBC
    {
        "name": "BBC World",
        "feed": "https://feeds.bbci.co.uk/news/world/rss.xml",
        "category_hint": "国际",
    },
    # 4. Financial Times
    {
        "name": "FT",
        "feed": "https://www.ft.com/rss/home",
        "category_hint": "金融",
    },
    # 5. Bloomberg
    {
        "name": "Bloomberg",
        "feed": "https://feeds.bloomberg.com/markets/news.rss",
        "category_hint": "金融",
    },
    # 6. Wall Street Journal
    {
        "name": "WSJ World",
        "feed": "https://feeds.wsj.com/wsj/xml/rss/3_7085.xml",
        "category_hint": "国际",
    },
    # 7. The Economist
    {
        "name": "The Economist",
        "feed": "https://www.economist.com/finance-and-economics/rss.xml",
        "category_hint": "经济",
    },
    # 8. Politico
    {
        "name": "Politico",
        "feed": "https://www.politico.com/rss/politicopicks.xml",
        "category_hint": "政治",
    },
    # 9. Semafor
    {
        "name": "Semafor",
        "feed": "https://www.semafor.com/feed",
        "category_hint": "国际",
    },
    # 10. Al Jazeera
    {
        "name": "Al Jazeera",
        "feed": "https://www.aljazeera.com/xml/rss/all.xml",
        "category_hint": "国际",
    },
    # 11. Nikkei Asia
    {
        "name": "Nikkei Asia",
        "feed": "https://asia.nikkei.com/rss/feed/nba",
        "category_hint": "经济",
    },
    # 12. Rest of World
    {
        "name": "Rest of World",
        "feed": "https://restofworld.org/feed/",
        "category_hint": "科技",
    },
    # 13. TechCrunch
    {
        "name": "TechCrunch",
        "feed": "https://techcrunch.com/feed/",
        "category_hint": "科技",
    },
    # 14. The Information (有付费墙，RSS 公开摘要)
    {
        "name": "The Information",
        "feed": "https://www.theinformation.com/feed",
        "category_hint": "科技",
    },
    # 15. 404 Media
    {
        "name": "404 Media",
        "feed": "https://www.404media.co/rss",
        "category_hint": "科技",
    },
    # 16. ProPublica
    {
        "name": "ProPublica",
        "feed": "https://www.propublica.org/feeds/propublica/main",
        "category_hint": "社会",
    },
    # 17. Bellingcat
    {
        "name": "Bellingcat",
        "feed": "https://www.bellingcat.com/feed/",
        "category_hint": "国际",
    },
    # 18. Our World in Data
    {
        "name": "Our World in Data",
        "feed": "https://ourworldindata.org/atom.xml",
        "category_hint": "社会",
    },
    # 19. SEC EDGAR
    {
        "name": "SEC EDGAR",
        "feed": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&type=8-K&date=&owner=include&count=10&action=getcompany&output=atom",
        "category_hint": "金融",
    },
    # 20. Federal Reserve
    {
        "name": "Federal Reserve",
        "feed": "https://www.federalreserve.gov/feeds/press_all.xml",
        "category_hint": "金融",
    },
]


def get_source_names() -> list[str]:
    return [s["name"] for s in SOURCES]


def make_fetcher(source_cfg: dict, proxy: Optional[str] = None,
                 timeout: int = 30, user_agent: str = "") -> RSSFetcher:
    return RSSFetcher(
        source_name=source_cfg["name"],
        feed_url=source_cfg["feed"],
        proxy=proxy,
        timeout=timeout,
        user_agent=user_agent,
        category_hint=source_cfg.get("category_hint", ""),
    )
