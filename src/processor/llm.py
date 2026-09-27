"""LLM 处理：分类 / 翻译 / 摘要

使用 OpenAI 兼容 API（支持 DeepSeek / 通义千问 / Moonshot / Ollama 等）。
"""
from __future__ import annotations
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterable

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from ..fetcher.base import NewsItem

log = logging.getLogger(__name__)

CATEGORIES = ["国际", "政治", "经济", "金融", "科技", "社会", "环境", "其他"]

SYSTEM_PROMPT = """你是国际新闻编辑，负责把英文新闻处理成结构化的中文摘要。
要求：
1. 标题必须翻译成中文，简洁准确
2. 摘要 100-180 字，客观陈述事实，不添加评论
3. 分类从给定类别中选最贴切的一个
4. 提取 3 个最有信息量的关键词（中文）
5. 只输出 JSON，不要任何额外文字"""


USER_PROMPT_TPL = """请处理以下新闻：

来源：{source}
标题：{title}
内容：{content}

输出格式（JSON）：
{{
  "title_zh": "中文标题",
  "category": "从 [{cats}] 中选一个",
  "summary_zh": "100-180字中文摘要",
  "keywords": ["关键词1", "关键词2", "关键词3"]
}}"""


class LLMProcessor:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini",
                 base_url: str = "", temperature: float = 0.2,
                 max_concurrent: int = 5):
        self.client = OpenAI(
            api_key=api_key or "EMPTY",
            base_url=base_url or None,
        )
        self.model = model
        self.temperature = temperature
        self.max_concurrent = max_concurrent

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def _call(self, system: str, user: str) -> dict:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=self.temperature,
            response_format={"type": "json_object"},
        )
        content = resp.choices[0].message.content or "{}"
        return json.loads(content)

    def process_one(self, item: NewsItem) -> NewsItem:
        """处理单条新闻"""
        if not item.title:
            return item
        content = (item.summary or item.content or item.title)[:2000]
        try:
            data = self._call(
                SYSTEM_PROMPT,
                USER_PROMPT_TPL.format(
                    source=item.source,
                    title=item.title,
                    content=content,
                    cats="、".join(CATEGORIES),
                ),
            )
            item.title_zh = data.get("title_zh", "").strip() or item.title
            item.category = data.get("category", "其他")
            item.summary_zh = data.get("summary_zh", "").strip()
            item.keywords = data.get("keywords", []) or []
            if item.category not in CATEGORIES:
                item.category = "其他"
        except Exception as e:
            log.warning("[%s] LLM failed for '%s': %s",
                        item.source, item.title[:40], e)
            item.title_zh = item.title
            item.category = item.category or "其他"
            item.summary_zh = (item.summary or "")[:300]
            item.keywords = []
        return item

    def process_batch(self, items: list[NewsItem],
                      progress_cb=None) -> list[NewsItem]:
        """并发处理一批"""
        results: list[NewsItem | None] = [None] * len(items)

        def work(idx: int, item: NewsItem):
            return idx, self.process_one(item)

        with ThreadPoolExecutor(max_workers=self.max_concurrent) as ex:
            futures = [ex.submit(work, i, it) for i, it in enumerate(items)]
            done = 0
            for f in as_completed(futures):
                try:
                    idx, item = f.result()
                    results[idx] = item
                except Exception as e:
                    log.error("LLM worker error: %s", e)
                done += 1
                if progress_cb:
                    progress_cb(done, len(items))

        return [r for r in results if r is not None]
