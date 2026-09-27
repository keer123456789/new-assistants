"""生成每日 Markdown 报告"""
from __future__ import annotations
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Iterable

from ..fetcher.base import NewsItem


class MarkdownReport:
    """把事件聚类结果渲染成结构化 Markdown"""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def render(self, events: list[dict], stats: dict,
               top_n: int = 8) -> tuple[str, str]:
        """返回 (brief_md, full_md)"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        full = self._render_full(events, stats, date_str)
        brief = self._render_brief(events[:top_n], stats, date_str)
        return brief, full

    def save(self, brief: str, full: str, date_str: str = "") -> tuple[Path, Path]:
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")
        full_path = self.output_dir / f"{date_str}.md"
        brief_path = self.output_dir / f"{date_str}-brief.md"
        full_path.write_text(full, encoding="utf-8")
        brief_path.write_text(brief, encoding="utf-8")
        return brief_path, full_path

    # ---------------------- 渲染 ----------------------

    def _render_full(self, events: list[dict], stats: dict, date_str: str) -> str:
        verified = [e for e in events if e["is_verified"]]
        singles = [e for e in events if not e["is_verified"]]

        # 按 category 分桶
        by_cat: dict[str, list[dict]] = defaultdict(list)
        for e in events:
            cat = e["items"][0].category or "其他"
            by_cat[cat].append(e)

        category_order = ["国际", "政治", "经济", "金融", "科技", "社会", "环境", "其他"]

        lines: list[str] = []
        lines.append(f"# 🌍 国际新闻日报 — {date_str}\n")
        lines.append(f"> 自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} · "
                    f"抓取 {stats.get('fetched', 0)} 条 · "
                    f"事件 {len(events)} 个 · "
                    f"多源验证 {len(verified)} 个\n")

        # 顶部统计
        lines.append("## 📊 数据统计\n")
        lines.append(f"- 总抓取条目：{stats.get('fetched', 0)}")
        lines.append(f"- 去重后条目：{stats.get('deduped', 0)}")
        lines.append(f"- LLM 处理成功：{stats.get('llm_processed', 0)}")
        lines.append(f"- 事件聚类数：{len(events)}")
        lines.append(f"- 多源交叉验证：{len(verified)}")
        lines.append(f"- 单源事件：{len(singles)}\n")

        # 今日重点
        lines.append("## 📌 今日重点\n")
        for i, e in enumerate(events[:8], 1):
            lines.append(self._render_event(i, e, compact=False))
            lines.append("")

        # 分领域速览
        lines.append("---\n\n## 📰 分领域速览\n")
        for cat in category_order:
            items = by_cat.get(cat, [])
            if not items:
                continue
            lines.append(f"### {self._cat_emoji(cat)} {cat}（{len(items)} 条）\n")
            # 领域内只列前 12 条最热的
            items_sorted = sorted(items,
                                 key=lambda x: x.get("importance_score", 0),
                                 reverse=True)
            for e in items_sorted[:12]:
                lines.append(self._render_event_brief(e))
            lines.append("")

        # 附录：源统计
        lines.append("---\n\n## 📡 数据来源清单\n")
        for source, count in sorted(stats.get("by_source", {}).items(),
                                   key=lambda x: -x[1]):
            lines.append(f"- {source}: {count} 条")
        lines.append("")

        return "\n".join(lines)

    def _render_event(self, idx: int, event: dict, compact: bool = False) -> str:
        """渲染一个事件（可能是聚类）"""
        items = event["items"]
        first = items[0]
        verified = event["is_verified"]
        sources = sorted({it.source for it in items})

        icon = "🔥" if event["importance_score"] >= 60 else "📰"
        badge = "✅ 多源验证" if verified else "📄 单源"

        lines = []
        title = event["verified_title_zh"] or first.title_zh or first.title
        lines.append(f"### {icon} {idx}. {title}")
        lines.append(f"**{badge}** · 类别: {first.category} · "
                    f"来源数: {len(sources)}\n")

        if event["verified_summary_zh"]:
            lines.append(f"**核心事实**: {event['final_truth'] or event['verified_summary_zh']}\n")

        if verified:
            if event["consensus"]:
                lines.append(f"**✅ 共识** ({len(sources)} 源): {event['consensus']}\n")
            if event["divergences"] and event["divergences"] not in ("无明显分歧", ""):
                lines.append(f"**⚠️ 分歧**: {event['divergences']}\n")

        lines.append(f"**📝 摘要**: {event['verified_summary_zh']}\n")

        # 来源列表
        lines.append(f"**🔗 来源**:")
        for it in items[:8]:   # 最多列 8 个
            pub = it.published.strftime("%m-%d %H:%M") if it.published else ""
            lines.append(f"- [{it.source}]({it.url})" +
                        (f" — {pub}" if pub else ""))
        if len(items) > 8:
            lines.append(f"- ... 另外 {len(items) - 8} 条相关报道")

        return "\n".join(lines)

    def _render_event_brief(self, event: dict) -> str:
        items = event["items"]
        first = items[0]
        sources = sorted({it.source for it in items})
        title = event["verified_title_zh"] or first.title_zh or first.title
        badge = "✅" if event["is_verified"] else "📄"
        sources_label = ", ".join(sources[:3]) + ("..." if len(sources) > 3 else "")
        summary = (event["verified_summary_zh"] or "")[:120]
        url = items[0].url

        return (f"- {badge} **{title}**\n"
                f"  _{sources_label}_ — {summary}..."
                f" ([详情]({url}))\n")

    def _render_brief(self, top_events: list[dict], stats: dict,
                     date_str: str) -> str:
        """手机推送用的精简版"""
        lines: list[str] = []
        lines.append(f"📰 *国际新闻日报 — {date_str}*\n")
        lines.append(f"共 {stats.get('fetched', 0)} 条抓取 · "
                    f"{len(top_events)} 条重点\n")

        for i, e in enumerate(top_events, 1):
            items = e["items"]
            title = e["verified_title_zh"] or items[0].title_zh or items[0].title
            badge = "✅" if e["is_verified"] else "📄"
            summary = (e["verified_summary_zh"] or "")[:140]
            source_count = len({it.source for it in items})

            lines.append(f"\n*{i}. {badge} {title}*")
            lines.append(f"_{source_count}源_ · {items[0].category}")
            lines.append(f"\n{summary}...")
            lines.append(f"\n🔗 [阅读原文]({items[0].url})")

        lines.append("\n\n_完整报告见附件_")
        return "\n".join(lines)

    @staticmethod
    def _cat_emoji(cat: str) -> str:
        return {
            "国际": "🌐",
            "政治": "🏛️",
            "经济": "💼",
            "金融": "💰",
            "科技": "🔬",
            "社会": "👥",
            "环境": "🌱",
            "其他": "📑",
        }.get(cat, "📑")
