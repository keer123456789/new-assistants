"""交叉验证：对事件做聚类 + 综合判断

策略：
1. 按 category + 标题关键词粗聚类（同一类别下做相似度比较）
2. 候选聚类交给 LLM 判断是否同一事件
3. 是 → 生成"共识+分歧+最终事实"
"""
from __future__ import annotations
import json
import logging
import re
import uuid
from collections import defaultdict
from difflib import SequenceMatcher
from typing import Optional

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from ..fetcher.base import NewsItem

log = logging.getLogger(__name__)


CLUSTER_SYSTEM_PROMPT = """你是新闻事实核查员。你会拿到一组来自不同源的新闻标题+摘要。
请判断它们是否描述同一事件，并交叉验证事实。

要求：
1. 同一事件 = 同一具体事件/人物/数据/政策（不是同一大主题）
2. 共识 = 所有源都提到的事实
3. 分歧 = 各源描述存在差异的点（数量、时间、原因等），如无分歧写"无明显分歧"
4. 最终事实 = 基于权威性+来源数量做出的最可信判断
5. 综合中文标题 ≤ 25 字，中文摘要 120-200 字
6. 只输出 JSON"""


CLUSTER_USER_PROMPT = """以下来自不同源的新闻，请判断并交叉验证：

{items}

输出 JSON 格式：
{{
  "same_event": true,
  "consensus": "所有源都提到的核心事实",
  "divergences": "各源描述差异（无则写'无明显分歧'）",
  "final_truth": "基于权威性+来源数量给出的最可信判断",
  "verified_title_zh": "≤25字中文综合标题",
  "verified_summary_zh": "120-200字中文摘要"
}}"""


class CrossVerifier:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini",
                 base_url: str = "", min_sources: int = 2,
                 sim_threshold: float = 0.55):
        self.client = OpenAI(api_key=api_key or "EMPTY", base_url=base_url or None)
        self.model = model
        self.min_sources = min_sources
        self.sim_threshold = sim_threshold

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=15))
    def _verify_cluster(self, items: list[NewsItem]) -> dict:
        formatted = []
        for i, it in enumerate(items, 1):
            formatted.append(
                f"[{i}] 来源: {it.source}\\n"
                f"    标题: {it.title}\\n"
                f"    摘要: {(it.summary_zh or it.summary or '')[:400]}"
            )
        user = CLUSTER_USER_PROMPT.format(items="\n\n".join(formatted))
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": CLUSTER_SYSTEM_PROMPT},
                {"role": "user", "content": user},
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        return json.loads(resp.choices[0].message.content or "{}")

    @staticmethod
    def _similar(a: str, b: str) -> float:
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()

    def cluster(self, items: list[NewsItem]) -> list[list[NewsItem]]:
        """基于标题相似度 + 类别粗聚类，返回候选 cluster 列表"""
        # 先按 category 分桶（不同类目下新闻一般不会撞车）
        buckets: dict[str, list[NewsItem]] = defaultdict(list)
        for it in items:
            buckets[it.category or "其他"].append(it)

        clusters: list[list[NewsItem]] = []
        for cat, group in buckets.items():
            remaining = list(group)
            while remaining:
                seed = remaining.pop(0)
                cluster = [seed]
                rest = []
                for other in remaining:
                    # 用标题相似度找邻居
                    if self._similar(seed.title, other.title) >= self.sim_threshold:
                        cluster.append(other)
                    else:
                        rest.append(other)
                clusters.append(cluster)
                remaining = rest
        return clusters

    def verify(self, items: list[NewsItem]) -> list[dict]:
        """
        返回一组"事件"，每个事件 = {
          cluster_id, items, verified_title_zh, verified_summary_zh,
          consensus, divergences, final_truth, importance_score
        }
        """
        log.info("Clustering %d items...", len(items))
        raw_clusters = self.cluster(items)
        # 过滤：只对 ≥2 个源的聚类做交叉验证
        target_clusters = [c for c in raw_clusters
                          if len({it.source for it in c}) >= self.min_sources]
        single_clusters = [c for c in raw_clusters
                          if len({it.source for it in c}) < self.min_sources]

        log.info("Got %d clusters, %d need verification, %d single-source",
                len(raw_clusters), len(target_clusters), len(single_clusters))

        events: list[dict] = []

        for cluster in target_clusters:
            cluster_id = uuid.uuid4().hex[:8]
            for it in cluster:
                it.cluster_id = cluster_id
            try:
                v = self._verify_cluster(cluster)
                if not v.get("same_event", False):
                    # LLM 判定不是同一事件，降级为多个独立条目
                    for it in cluster:
                        events.append(self._single_event_dict(it))
                    continue

                # 重要性评分：源数量 + 类别权重 + 摘要长度
                importance = (
                    len({it.source for it in cluster}) * 10
                    + min(len(v.get("verified_summary_zh", "")), 200)
                )
                events.append({
                    "cluster_id": cluster_id,
                    "items": cluster,
                    "verified_title_zh": v.get("verified_title_zh", ""),
                    "verified_summary_zh": v.get("verified_summary_zh", ""),
                    "consensus": v.get("consensus", ""),
                    "divergences": v.get("divergences", "无明显分歧"),
                    "final_truth": v.get("final_truth", ""),
                    "source_count": len({it.source for it in cluster}),
                    "importance_score": importance,
                    "is_verified": True,
                })
            except Exception as e:
                log.warning("verify cluster failed: %s", e)
                for it in cluster:
                    events.append(self._single_event_dict(it))

        for cluster in single_clusters:
            for it in cluster:
                events.append(self._single_event_dict(it))

        # 按重要性倒序
        events.sort(key=lambda e: e.get("importance_score", 0), reverse=True)
        return events

    def _single_event_dict(self, item: NewsItem) -> dict:
        item.cluster_id = uuid.uuid4().hex[:8]
        return {
            "cluster_id": item.cluster_id,
            "items": [item],
            "verified_title_zh": item.title_zh or item.title,
            "verified_summary_zh": item.summary_zh or item.summary or "",
            "consensus": "单源报道，未做交叉验证",
            "divergences": "无对比来源",
            "final_truth": item.summary_zh or item.summary or "",
            "source_count": 1,
            "importance_score": 5,
            "is_verified": False,
        }
