"""去重：跨源的近似去重 + 同源完全去重"""
from __future__ import annotations
import hashlib
import re
from difflib import SequenceMatcher
from typing import Iterable

from ..fetcher.base import NewsItem


def _normalize_title(t: str) -> str:
    t = t.lower().strip()
    t = re.sub(r"[^ws]", " ", t)
    t = re.sub(r"s+", " ", t)
    return t


def _title_hash(t: str) -> str:
    return hashlib.md5(_normalize_title(t).encode("utf-8")).hexdigest()


class Deduplicator:
    """标题相似的视为同一条"""

    def __init__(self, threshold: float = 0.78):
        self.threshold = threshold

    def dedupe(self, items: Iterable[NewsItem]) -> list[NewsItem]:
        items = list(items)
        kept: list[NewsItem] = []
        for it in items:
            is_dup = False
            nt = _normalize_title(it.title)
            for ex in kept:
                ex_nt = _normalize_title(ex.title)
                if nt == ex_nt:
                    is_dup = True
                    break
                ratio = SequenceMatcher(None, nt, ex_nt).ratio()
                if ratio >= self.threshold:
                    is_dup = True
                    break
            if not is_dup:
                kept.append(it)
        return kept
