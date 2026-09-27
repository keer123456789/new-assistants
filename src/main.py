"""主编排器

执行流程：
1. 加载配置
2. 抓取所有源
3. 去重
4. LLM 分类/翻译/摘要
5. 交叉验证聚类
6. 生成报告
7. 推送
"""
from __future__ import annotations
import argparse
import logging
import os
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config
from src.fetcher.sources import SOURCES, make_fetcher
from src.fetcher.base import NewsItem
from src.processor.deduper import Deduplicator
from src.processor.llm import LLMProcessor
from src.processor.verifier import CrossVerifier
from src.processor.progress import ProgressBar
from src.storage import MarkdownReport, HTMLReport
from src.pusher import (
    TelegramPusher, EmailPusher, BarkPusher, ServerChanPusher, PushMessage,
)


def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)


def step(title: str):
    bar = "=" * 60
    print(f"\n{bar}\n{title}\n{bar}")


def run_pipeline(config_path: str = "config.yaml",
                dry_run: bool = False,
                skip_push: bool = False,
                verbose: bool = False):
    setup_logging(verbose)
    log = logging.getLogger("main")

    step("[*] 加载配置")
    cfg = Config.load(config_path)
    proxy_url = cfg.proxy.effective_url()
    log.info("代理: %s", proxy_url or "未启用")
    log.info("LLM 模型: %s", cfg.llm.model)
    log.info("推送渠道: %s", cfg.push.channels)

    step("[*] 抓取新闻源（共 %d 个）" % len(SOURCES))
    all_items = []
    fetch_stats = {}

    for source_cfg in SOURCES:
        try:
            fetcher = make_fetcher(
                source_cfg,
                proxy=proxy_url,
                timeout=cfg.fetch.timeout,
                user_agent=cfg.fetch.user_agent,
            )
            items = fetcher.fetch(
                hours_back=cfg.fetch.hours_back,
                max_items=cfg.fetch.max_items_per_source,
            )
            all_items.extend(items)
            fetch_stats[source_cfg["name"]] = len(items)
        except Exception as e:
            log.warning("[%s] fetch error: %s", source_cfg["name"], e)
            fetch_stats[source_cfg["name"]] = 0

    log.info("总共抓取 %d 条", len(all_items))

    if not all_items:
        log.warning("没有抓到任何新闻，退出")
        return

    step("[*] 去重")
    deduped = Deduplicator().dedupe(all_items)
    log.info("去重后剩余 %d 条", len(deduped))

    step("[*] LLM 处理（分类/翻译/摘要）")
    if not cfg.llm.api_key:
        log.error("LLM_API_KEY 未配置！请在 .env 中设置")
        return

    llm = LLMProcessor(
        api_key=cfg.llm.api_key,
        model=cfg.llm.model,
        base_url=cfg.llm.base_url,
        temperature=cfg.llm.temperature,
        max_concurrent=cfg.llm.max_concurrent,
    )

    bar = ProgressBar(len(deduped), "LLM 处理")

    def cb(done, total):
        bar.done = done
        bar.total = total
        bar.render()

    llm_processed = llm.process_batch(deduped, progress_cb=cb)
    log.info("LLM 处理完成 %d 条", len(llm_processed))


    step("[*] 交叉验证聚类")
    verifier = CrossVerifier(
        api_key=cfg.llm.api_key,
        model=cfg.llm.model,
        base_url=cfg.llm.base_url,
        min_sources=cfg.report.min_sources_for_verification,
    )
    events = verifier.verify(llm_processed)
    log.info("生成 %d 个事件，其中 %d 个多源验证",
            len(events),
            sum(1 for e in events if e["is_verified"]))

    step("[*] 生成报告")
    stats = {
        "fetched": len(all_items),
        "deduped": len(deduped),
        "llm_processed": len(llm_processed),
        "by_source": fetch_stats,
    }

    report = MarkdownReport(output_dir="output")
    html_writer = HTMLReport(output_dir="output")
    brief, full = report.render(events, stats)

    date_str = datetime.now().strftime("%Y-%m-%d")
    brief_path, full_path = report.save(brief, full, date_str)

    # 同时生成 H5 HTML 网页
    html_content = html_writer.render_day(events, stats, date_str)
    html_path = html_writer.save_day(html_content, date_str)

    # 更新首页（聚合所有历史日期）
    all_dates = html_writer.list_existing_dates()
    if date_str not in all_dates:
        all_dates.append(date_str)
    index_content = html_writer.render_index(all_dates)
    index_path = html_writer.save_index(index_content)

    log.info("Markdown 报告: %s, %s", brief_path, full_path)
    log.info("HTML 报告: %s", html_path)
    log.info("HTML 首页: %s", index_path)

    if dry_run:
        step("[*] 报告预览 (brief)")
        print(brief[:2000])
        print("\n...\n（完整报告见文件）\n")

    if skip_push or dry_run:
        log.info("跳过推送（dry-run 或 skip-push）")
        return

    step("[*] 推送")
    pushers = []
    if "telegram" in cfg.push.channels:
        token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
        chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
        if token and chat_id:
            pushers.append(TelegramPusher(token, chat_id, proxy=proxy_url))
    if "email" in cfg.push.channels:
        host = os.environ.get("EMAIL_SMTP_HOST", "")
        port = int(os.environ.get("EMAIL_SMTP_PORT", "587"))
        user = os.environ.get("EMAIL_USERNAME", "")
        pwd = os.environ.get("EMAIL_PASSWORD", "")
        from_a = os.environ.get("EMAIL_FROM", "")
        to_a = os.environ.get("EMAIL_TO", "")
        if all([host, user, pwd, from_a, to_a]):
            pushers.append(EmailPusher(host, port, user, pwd, from_a, to_a))
    if "bark" in cfg.push.channels:
        url = os.environ.get("BARK_URL", "")
        if url:
            pushers.append(BarkPusher(url, proxy=proxy_url))
    if "serverchan" in cfg.push.channels:
        key = os.environ.get("SERVERCHAN_KEY", "")
        if key:
            pushers.append(ServerChanPusher(key, proxy=proxy_url))

    if not pushers:
        log.warning("没有可用的 pusher，请检查 .env 配置")
        return

    msg = PushMessage(
        title=f"国际新闻日报 {date_str}",
        body=brief,
        summary=brief[:500],
        file_path=str(full_path),
        level="info",
    )
    for p in pushers:
        try:
            ok = p.send(msg)
            log.info("%s: %s", type(p).__name__, "OK" if ok else "FAIL")
        except Exception as e:
            log.error("%s push failed: %s", type(p).__name__, e)

    step("[*] 完成")


def main():
    parser = argparse.ArgumentParser(description="国际新闻助手")
    parser.add_argument("--config", default="config.yaml", help="配置文件路径")
    parser.add_argument("--dry-run", action="store_true", help="只跑不推送")
    parser.add_argument("--skip-push", action="store_true", help="跳过推送")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细日志")
    args = parser.parse_args()

    run_pipeline(
        config_path=args.config,
        dry_run=args.dry_run,
        skip_push=args.skip_push,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    main()
