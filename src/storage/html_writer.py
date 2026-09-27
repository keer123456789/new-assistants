"""HTML 报告生成器（H5 移动端友好）

特点：
- 移动端自适应
- 卡片式布局
- 类别色标
- 深色模式（prefers-color-scheme）
- 单文件自包含（CSS inline），不依赖外部资源
"""
from __future__ import annotations
import html
import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Iterable

from ..fetcher.base import NewsItem


CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }
:root {
  --bg: #f5f5f7; --card: #ffffff; --text: #1d1d1f; --muted: #6e6e73;
  --border: #e5e5ea; --accent: #0071e3; --link: #0071e3;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #000000; --card: #1c1c1e; --text: #f5f5f7; --muted: #98989d;
    --border: #38383a; --accent: #0a84ff; --link: #64d2ff;
  }
}
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC",
               "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
  background: var(--bg); color: var(--text); line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}
.container { max-width: 720px; margin: 0 auto; padding: 16px; }
.header {
  position: sticky; top: 0; background: var(--bg); padding: 16px 0;
  border-bottom: 1px solid var(--border); z-index: 10;
  backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
}
.header h1 { font-size: 24px; font-weight: 700; margin-bottom: 4px; }
.header .meta { font-size: 13px; color: var(--muted); }
.stats {
  display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px;
  margin: 16px 0;
}
.stat-card {
  background: var(--card); padding: 12px; border-radius: 12px;
  border: 1px solid var(--border);
}
.stat-card .num { font-size: 24px; font-weight: 700; color: var(--accent); }
.stat-card .label { font-size: 12px; color: var(--muted); }

.section-title {
  font-size: 18px; font-weight: 700; margin: 24px 0 12px;
  padding-left: 8px; border-left: 4px solid var(--accent);
}

.event {
  background: var(--card); border-radius: 16px; padding: 16px;
  margin-bottom: 12px; border: 1px solid var(--border);
  box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}
.event.verified { border-left: 4px solid #34c759; }
.event.single { border-left: 4px solid var(--muted); }
.event.importance-high { border-left-color: #ff3b30; }

.event h3 {
  font-size: 17px; font-weight: 600; margin-bottom: 8px;
  line-height: 1.4;
}
.event .badges {
  display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 10px;
  font-size: 12px;
}
.badge {
  display: inline-block; padding: 2px 8px; border-radius: 8px;
  background: var(--border); color: var(--muted);
}
.badge.cat-国际 { background: #e3f2fd; color: #1565c0; }
.badge.cat-政治 { background: #fce4ec; color: #c2185b; }
.badge.cat-经济 { background: #fff3e0; color: #e65100; }
.badge.cat-金融 { background: #e8f5e9; color: #2e7d32; }
.badge.cat-科技 { background: #ede7f6; color: #4527a0; }
.badge.cat-社会 { background: #fff8e1; color: #f57f17; }
.badge.cat-环境 { background: #e0f2f1; color: #00695c; }
.badge.verified { background: #e8f5e9; color: #2e7d32; }
.badge.single { background: #f5f5f5; color: #6e6e73; }
.badge.imp-high { background: #ffebee; color: #c62828; }

@media (prefers-color-scheme: dark) {
  .badge.cat-国际 { background: #1a3a5c; color: #90caf9; }
  .badge.cat-政治 { background: #5c1a3a; color: #f48fb1; }
  .badge.cat-经济 { background: #5c3a1a; color: #ffb74d; }
  .badge.cat-金融 { background: #1a5c2e; color: #81c784; }
  .badge.cat-科技 { background: #3a1a5c; color: #b39ddb; }
  .badge.cat-社会 { background: #5c4a1a; color: #ffd54f; }
  .badge.cat-环境 { background: #1a5c52; color: #4db6ac; }
  .badge.verified { background: #1a3a1a; color: #81c784; }
  .badge.single { background: #2c2c2e; color: #98989d; }
  .badge.imp-high { background: #3a1a1a; color: #ef9a9a; }
}

.event .core {
  background: var(--bg); padding: 10px 12px; border-radius: 8px;
  margin: 10px 0; font-size: 14px; font-weight: 500;
}
.event .summary { font-size: 14px; margin: 10px 0; color: var(--text); }
.event .consensus, .event .divergence {
  font-size: 13px; margin: 6px 0; padding: 8px 10px; border-radius: 6px;
}
.event .consensus { background: rgba(52, 199, 89, 0.1); }
.event .divergence { background: rgba(255, 149, 0, 0.1); }
.event .consensus::before { content: "✅ 共识"; font-weight: 600; margin-right: 6px; }
.event .divergence::before { content: "⚠️ 分歧"; font-weight: 600; margin-right: 6px; }

.sources { margin-top: 12px; font-size: 13px; }
.sources summary { cursor: pointer; color: var(--link); user-select: none; padding: 4px 0; }
.sources ul { list-style: none; padding-left: 0; margin-top: 6px; }
.sources li { padding: 4px 0; border-bottom: 1px solid var(--border); }
.sources li:last-child { border-bottom: none; }
.sources a { color: var(--link); text-decoration: none; }
.sources a:hover { text-decoration: underline; }
.sources .source-name { font-weight: 600; }
.sources .time { color: var(--muted); font-size: 12px; margin-left: 6px; }

.footer {
  margin-top: 32px; padding: 16px 0; text-align: center;
  color: var(--muted); font-size: 12px; border-top: 1px solid var(--border);
}
.footer a { color: var(--link); text-decoration: none; }

@media (max-width: 480px) {
  .container { padding: 12px; }
  .header h1 { font-size: 20px; }
  .event { padding: 14px; }
}
"""


def _esc(text: str) -> str:
    if not text:
        return ""
    return html.escape(str(text))


class HTMLReport:
    """把事件聚类结果渲染成 H5 友好的 HTML 页面"""

    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def render_day(self, events: list[dict], stats: dict,
                   date_str: str) -> str:
        """生成单日 HTML"""
        verified = sum(1 for e in events if e["is_verified"])
        singles = len(events) - verified

        # 按 category 分桶
        by_cat: dict[str, list[dict]] = defaultdict(list)
        for e in events:
            cat = e["items"][0].category or "其他"
            by_cat[cat].append(e)

        category_order = ["国际", "政治", "经济", "金融", "科技", "社会", "环境", "其他"]
        category_emoji = {
            "国际": "🌐", "政治": "🏛️", "经济": "💼", "金融": "💰",
            "科技": "🔬", "社会": "👥", "环境": "🌱", "其他": "📑",
        }

        # 顶部事件（Top stories）
        top_events = sorted(events, key=lambda e: e.get("importance_score", 0),
                          reverse=True)[:8]

        # ---------- HTML ----------
        h = []
        h.append("<!DOCTYPE html>")
        h.append('<html lang="zh-CN">')
        h.append("<head>")
        h.append('<meta charset="UTF-8">')
        h.append('<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">')
        h.append('<meta name="theme-color" content="#0071e3">')
        h.append(f"<title>国际新闻日报 — {date_str}</title>")
        h.append(f"<style>{CSS}</style>")
        h.append("</head>")
        h.append("<body>")
        h.append('<div class="container">')

        # Header
        h.append('<div class="header">')
        h.append(f"<h1>🌍 国际新闻日报</h1>")
        h.append(f'<div class="meta">{date_str} · 自动生成 · '
                f'共 {stats.get("fetched", 0)} 条抓取 · {len(events)} 个事件 · '
                f'{verified} 个多源验证</div>')
        h.append("</div>")

        # Stats
        h.append('<div class="stats">')
        h.append(self._stat_card(len(events), "事件总数"))
        h.append(self._stat_card(verified, "多源验证"))
        h.append(self._stat_card(stats.get("fetched", 0), "抓取条目"))
        h.append(self._stat_card(len(stats.get("by_source", {})), "数据源"))
        h.append("</div>")

        # Top Stories
        h.append('<div class="section-title">📌 今日重点</div>')
        for e in top_events:
            h.append(self._render_event(e))

        # Categories
        for cat in category_order:
            items = by_cat.get(cat, [])
            if not items:
                continue
            h.append(f'<div class="section-title">{category_emoji.get(cat, "📑")} '
                    f'{cat}（{len(items)} 条）</div>')
            items_sorted = sorted(items,
                                 key=lambda x: x.get("importance_score", 0),
                                 reverse=True)
            for e in items_sorted[:15]:
                h.append(self._render_event(e, compact=True))

        # Footer
        h.append('<div class="footer">')
        h.append(f'<div>📡 数据来源: {", ".join(sorted(stats.get("by_source", {}).keys()))}</div>')
        h.append('<div style="margin-top:8px">')
        h.append('<a href="index.html">← 返回首页</a> · ')
        h.append('由 AI 自动生成，仅供参考')
        h.append("</div></div>")

        h.append("</div>")
        h.append("</body></html>")
        return "\n".join(h)

    def render_index(self, dates: list[str]) -> str:
        """生成首页（日期列表）"""
        h = []
        h.append("<!DOCTYPE html>")
        h.append('<html lang="zh-CN">')
        h.append("<head>")
        h.append('<meta charset="UTF-8">')
        h.append('<meta name="viewport" content="width=device-width, initial-scale=1">')
        h.append('<meta name="theme-color" content="#0071e3">')
        h.append('<title>国际新闻日报 — 全部历史</title>')
        h.append(f"<style>{CSS}</style>")
        h.append("<style>")
        h.append(".date-list { display: flex; flex-direction: column; gap: 8px; }")
        h.append(".date-item { background: var(--card); padding: 16px; "
                "border-radius: 12px; border: 1px solid var(--border); "
                "display: flex; justify-content: space-between; "
                "align-items: center; text-decoration: none; color: var(--text); }")
        h.append(".date-item:hover { background: var(--bg); }")
        h.append(".date-item .arrow { color: var(--muted); }")
        h.append("</style>")
        h.append("</head>")
        h.append("<body>")
        h.append('<div class="container">')
        h.append('<div class="header">')
        h.append("<h1>🌍 国际新闻日报</h1>")
        h.append('<div class="meta">点击查看历史报告 · '
                f'共 {len(dates)} 天</div>')
        h.append("</div>")

        if not dates:
            h.append('<div class="event"><p>暂无历史报告</p></div>')
        else:
            h.append('<div class="date-list">')
            for date in sorted(dates, reverse=True):
                # 日期格式 YYYY-MM-DD
                date_label = date
                try:
                    dt = datetime.strptime(date, "%Y-%m-%d")
                    weekday = ["周一", "周二", "周三", "周四",
                              "周五", "周六", "周日"][dt.weekday()]
                    date_label = f"{date} ({weekday})"
                except Exception:
                    pass
                h.append(f'<a href="{date}.html" class="date-item">')
                h.append(f"<span>{date_label}</span>")
                h.append('<span class="arrow">→</span>')
                h.append("</a>")
            h.append("</div>")

        h.append('<div class="footer">')
        h.append("由 AI 自动生成")
        h.append("</div>")

        h.append("</div>")
        h.append("</body></html>")
        return "\n".join(h)

    def save_day(self, html_content: str, date_str: str) -> Path:
        path = self.output_dir / f"{date_str}.html"
        path.write_text(html_content, encoding="utf-8")
        return path

    def save_index(self, html_content: str) -> Path:
        path = self.output_dir / "index.html"
        path.write_text(html_content, encoding="utf-8")
        return path

    def list_existing_dates(self) -> list[str]:
        """扫描 output 目录，找出已有的日期 html"""
        dates = []
        for p in self.output_dir.glob("????-??-??.html"):
            dates.append(p.stem)
        return dates

    # ----- helpers -----
    @staticmethod
    def _stat_card(num: int, label: str) -> str:
        return (f'<div class="stat-card">'
                f'<div class="num">{num}</div>'
                f'<div class="label">{_esc(label)}</div>'
                f'</div>')

    def _render_event(self, event: dict, compact: bool = False) -> str:
        items = event["items"]
        first = items[0]
        verified = event["is_verified"]
        sources = sorted({it.source for it in items})
        importance = event.get("importance_score", 0)

        # Card class
        cls = "event"
        if verified:
            cls += " verified"
        else:
            cls += " single"
        if importance >= 60:
            cls += " importance-high"

        title = event["verified_title_zh"] or first.title_zh or first.title

        h = [f'<article class="{cls}">']
        # 标题
        h.append(f"<h3>{_esc(title)}</h3>")
        # 标签
        h.append('<div class="badges">')
        cat = first.category or "其他"
        h.append(f'<span class="badge cat-{_esc(cat)}">{_esc(cat)}</span>')
        if verified:
            h.append('<span class="badge verified">✅ 多源验证</span>')
            h.append(f'<span class="badge">{len(sources)} 个来源</span>')
        else:
            h.append('<span class="badge single">📄 单源</span>')
        if importance >= 60:
            h.append('<span class="badge imp-high">🔥 重点</span>')
        h.append("</div>")

        if not compact:
            # 核心事实
            core = event.get("final_truth") or event.get("verified_summary_zh") or ""
            if core:
                h.append(f'<div class="core">🎯 {_esc(core)}</div>')

            # 共识/分歧
            if verified:
                consensus = event.get("consensus", "")
                divergences = event.get("divergences", "")
                if consensus and consensus != "无明显分歧":
                    h.append(f'<div class="consensus">{_esc(consensus)}</div>')
                if divergences and divergences not in ("无明显分歧", ""):
                    h.append(f'<div class="divergence">{_esc(divergences)}</div>')

        # 摘要
        summary = event.get("verified_summary_zh") or ""
        if summary:
            # 截断长度，compact 模式更短
            max_len = 100 if compact else 500
            if len(summary) > max_len:
                summary = summary[:max_len] + "..."
            h.append(f'<div class="summary">{_esc(summary)}</div>')

        # 来源列表
        h.append("<details class=\"sources\">")
        h.append(f"<summary>🔗 {len(items)} 个来源</summary>")
        h.append("<ul>")
        for it in items[:10]:
            pub = it.published.strftime("%m-%d %H:%M") if it.published else ""
            time_str = f'<span class="time">{pub}</span>' if pub else ""
            h.append(f'<li><a href="{_esc(it.url)}" target="_blank" rel="noopener">'
                    f'<span class="source-name">{_esc(it.source)}</span></a>'
                    f'{time_str}</li>')
        h.append("</ul>")
        h.append("</details>")

        h.append("</article>")
        return "\n".join(h)