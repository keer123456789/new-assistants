"""示例：生成一份样例报告（不需要 LLM 也能跑）

会同时生成 Markdown 和 HTML 两个版本。
"""
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT))

from src.fetcher.base import NewsItem
from src.storage import MarkdownReport, HTMLReport


def make_sample_events():
    now = datetime.now(timezone.utc)

    fed_event = {
        "cluster_id": "fed001",
        "items": [
            NewsItem(title="Fed keeps interest rates unchanged at 4.25%-4.50%",
                url="https://reuters.com/article/fed-rates-2026",
                source="Reuters", published=now,
                title_zh="美联储维持利率不变于4.25%-4.50%区间",
                category="金融",
                summary_zh="美联储在为期两天的会议后，决定将联邦基金利率维持在4.25%-4.50%区间，符合市场预期。",
                keywords=["美联储", "利率", "货币政策"]),
            NewsItem(title="Federal Reserve holds rates steady, signals patience",
                url="https://apnews.com/article/fed-rates",
                source="AP News", published=now,
                title_zh="美联储维持利率稳定，释放耐心信号",
                category="金融",
                summary_zh="美联储连续第三次维持基准利率不变，主席表示将根据数据决定下一步行动。",
                keywords=["美联储", "利率"]),
            NewsItem(title="Fed rate decision: dot plot shows cuts pushed back",
                url="https://bloomberg.com/news/fed-rates",
                source="Bloomberg", published=now,
                title_zh="美联储决议：点阵图显示降息时点推迟",
                category="金融",
                summary_zh="最新点阵图显示官员们将首次降息预期推迟至2027年。",
                keywords=["美联储", "点阵图", "降息"]),
        ],
        "verified_title_zh": "美联储维持利率不变，最新点阵图推迟降息预期",
        "verified_summary_zh": "美联储9月会议决定将联邦基金利率维持在4.25%-4.50%区间，符合市场普遍预期。本次会议的关键看点是最新点阵图，显示多数官员将首次降息时点推迟至2027年，反映出对通胀粘性的担忧。",
        "consensus": "美联储维持利率不变；声明措辞偏鹰；点阵图推迟降息预期",
        "divergences": "Reuters/Bloomberg 更强调推迟降息；AP 更强调主席的耐心表态",
        "final_truth": "美联储维持利率4.25%-4.50%；点阵图推迟降息至2027年；声明偏鹰",
        "source_count": 3,
        "importance_score": 95,
        "is_verified": True,
    }

    mideast_event = {
        "cluster_id": "me001",
        "items": [
            NewsItem(title="Israel-Hezbollah ceasefire holds for third day",
                url="https://bbc.com/news/middleeast",
                source="BBC World", published=now,
                title_zh="以色列-真主党停火协议进入第三天",
                category="国际",
                summary_zh="自停火协议生效以来，黎巴嫩南部边境保持平静，联合国维和部队加强巡逻。",
                keywords=["以色列", "黎巴嫩", "停火"]),
            NewsItem(title="Cease-fire between Israel and Hezbollah largely holding",
                url="https://aljazeera.com/news/ceasefire",
                source="Al Jazeera", published=now,
                title_zh="以色列与真主党停火基本得到遵守",
                category="国际",
                summary_zh="停火协议基本得到遵守，但双方相互指责对方有轻微违反行为。",
                keywords=["以色列", "真主党"]),
        ],
        "verified_title_zh": "以色列-真主党停火第三天基本维持",
        "verified_summary_zh": "自停火协议生效以来已第三天，黎巴嫩南部边境基本保持平静。联合国维和部队加强巡逻。双方相互指责对方有轻微违反行为，但未发生重大事件。",
        "consensus": "停火协议基本维持；边境相对平静",
        "divergences": "BBC 强调维和巡逻；Al Jazeera 强调双方相互指责",
        "final_truth": "停火第三天基本维持，偶有摩擦",
        "source_count": 2,
        "importance_score": 75,
        "is_verified": True,
    }

    eu_event = {
        "cluster_id": "eu001",
        "items": [
            NewsItem(title="Eurozone inflation falls to 2.1% in September",
                url="https://ft.com/content/eurozone-inflation",
                source="FT", published=now,
                title_zh="欧元区9月通胀降至2.1%",
                category="经济",
                summary_zh="欧元区9月调和CPI同比上涨2.1%，低于市场预期的2.3%。",
                keywords=["欧元区", "通胀", "CPI"]),
            NewsItem(title="ECB rate cut more likely as inflation eases",
                url="https://reuters.com/markets/europe/ecb",
                source="Reuters", published=now,
                title_zh="通胀缓解使欧央行降息可能性上升",
                category="经济",
                summary_zh="欧元区通胀数据走弱，市场押注欧央行10月降息。",
                keywords=["欧央行", "通胀"]),
        ],
        "verified_title_zh": "欧元区通胀降至2.1%，欧央行10月降息预期升温",
        "verified_summary_zh": "欧元区9月调和CPI同比上涨2.1%，低于市场预期。核心通胀也有所放缓。数据公布后，市场对欧央行10月降息25基点的押注升至85%。",
        "consensus": "欧元区通胀降至2.1%；欧央行10月降息预期升温",
        "divergences": "无明显分歧",
        "final_truth": "欧元区通胀2.1%已接近欧央行目标；10月降息预期升至85%",
        "source_count": 2,
        "importance_score": 70,
        "is_verified": True,
    }

    nvda_event = {
        "cluster_id": "nvda001",
        "items": [
            NewsItem(title="Nvidia reports record Q3 revenue, beats expectations",
                url="https://techcrunch.com/2026/09/27/nvidia-q3",
                source="TechCrunch", published=now,
                title_zh="英伟达Q3营收350亿美元创纪录",
                category="科技",
                summary_zh="英伟达公布Q3财报，营收达350亿美元，同比增长94%，数据中心业务表现强劲。",
                keywords=["英伟达", "财报", "AI芯片"]),
        ],
        "verified_title_zh": "英伟达Q3营收350亿美元创纪录",
        "verified_summary_zh": "英伟达公布Q3财报，营收350亿美元同比增长94%，数据中心业务表现强劲，盘后股价上涨4%。",
        "consensus": "单源报道，未做交叉验证",
        "divergences": "无对比来源",
        "final_truth": "英伟达Q3营收350亿美元创新高",
        "source_count": 1,
        "importance_score": 60,
        "is_verified": False,
    }

    return [fed_event, mideast_event, eu_event, nvda_event]


def main():
    events = make_sample_events()
    stats = {
        "fetched": 18,
        "deduped": 8,
        "llm_processed": 8,
        "by_source": {
            "Reuters": 3, "AP News": 2, "BBC World": 2,
            "Bloomberg": 2, "FT": 1, "TechCrunch": 1, "Al Jazeera": 1,
        },
    }

    md = MarkdownReport(output_dir=str(ROOT / "output"))
    html_w = HTMLReport(output_dir=str(ROOT / "output"))

    # Markdown
    brief, full = md.render(events, stats)
    brief_path, full_path = md.save(brief, full, "2026-09-27")

    # HTML
    html_content = html_w.render_day(events, stats, "2026-09-27")
    html_path = html_w.save_day(html_content, "2026-09-27")

    # Index page
    all_dates = html_w.list_existing_dates()
    if "2026-09-27" not in all_dates:
        all_dates.append("2026-09-27")
    index_content = html_w.render_index(all_dates)
    index_path = html_w.save_index(index_content)

    print(f"Markdown brief: {brief_path}")
    print(f"Markdown full:  {full_path}")
    print(f"HTML day:       {html_path}")
    print(f"HTML index:     {index_path}")


if __name__ == "__main__":
    main()