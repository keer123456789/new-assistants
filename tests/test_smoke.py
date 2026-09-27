"""Smoke test: 验证模块导入、配置加载、模拟数据处理"""
import sys
import os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT))


def test_imports():
    print("Test 1: module imports")
    from src.config import Config
    from src.fetcher.sources import SOURCES, get_source_names
    from src.processor.deduper import Deduplicator
    from src.processor.llm import LLMProcessor
    from src.processor.verifier import CrossVerifier
    from src.storage.markdown_writer import MarkdownReport
    from src.pusher import (
        TelegramPusher, EmailPusher, BarkPusher, ServerChanPusher,
    )
    print(f"  OK. {len(get_source_names())} sources configured.")


def test_config_load():
    print("Test 2: config load")
    from src.config import Config
    cfg = Config.load(str(ROOT / "config.yaml"))
    print(f"  OK. LLM model: {cfg.llm.model}, "
          f"channels: {cfg.push.channels}")


def test_dedup():
    print("Test 3: deduplicator")
    from src.fetcher.base import NewsItem
    from src.processor.deduper import Deduplicator
    from datetime import datetime, timezone

    items = [
        NewsItem(title="Fed keeps interest rates unchanged at 4.25%-4.50%",
                 url="https://example.com/1", source="Reuters",
                 published=datetime.now(timezone.utc)),
        NewsItem(title="Fed keeps interest rates unchanged at 4.25-4.50 percent",
                 url="https://example.com/2", source="AP",
                 published=datetime.now(timezone.utc)),
        NewsItem(title="ECB raises rates by 25bps",
                 url="https://example.com/3", source="FT",
                 published=datetime.now(timezone.utc)),
    ]
    deduped = Deduplicator().dedupe(items)
    assert len(deduped) == 2, f"expected 2, got {len(deduped)}"
    print(f"  OK. Deduped {len(items)} -> {len(deduped)}")


def test_markdown_render():
    print("Test 4: markdown render")
    from src.fetcher.base import NewsItem
    from src.storage.markdown_writer import MarkdownReport
    from datetime import datetime, timezone

    items = [
        NewsItem(
            title="Fed keeps rates",
            url="https://example.com/1",
            source="Reuters",
            published=datetime.now(timezone.utc),
            title_zh="美联储维持利率不变",
            category="金融",
            summary_zh="美联储决定维持基准利率不变。",
            keywords=["美联储", "利率", "货币政策"],
        ),
    ]
    events = [{
        "cluster_id": "abc123",
        "items": items,
        "verified_title_zh": "美联储维持利率不变",
        "verified_summary_zh": "美联储决定维持基准利率不变。",
        "consensus": "美联储维持利率",
        "divergences": "无明显分歧",
        "final_truth": "美联储维持利率",
        "source_count": 1,
        "importance_score": 50,
        "is_verified": False,
    }]
    stats = {"fetched": 1, "deduped": 1, "llm_processed": 1, "by_source": {"Reuters": 1}}

    report = MarkdownReport(output_dir=str(ROOT / "output"))
    brief, full = report.render(events, stats)
    assert "美联储" in full
    assert "美联储" in brief
    print(f"  OK. Brief={len(brief)} chars, Full={len(full)} chars")
    print(f"  Brief preview (first 100 chars):\n{brief[:100]}")
    print(f"  Full report length: {len(full)}")


def test_fetcher_dry():
    print("Test 5: fetcher instantiates")
    from src.fetcher.sources import SOURCES, make_fetcher
    cfg = SOURCES[0]
    f = make_fetcher(cfg, proxy=None, timeout=10)
    print(f"  OK. {f.source_name} fetcher created with URL {f.feed_url}")


if __name__ == "__main__":
    print(f"Running smoke tests at {ROOT}\n")
    test_imports()
    test_config_load()
    test_dedup()
    test_markdown_render()
    test_fetcher_dry()
    print("\n[OK] All smoke tests passed")
