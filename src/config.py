"""代理 / 配置加载"""
from __future__ import annotations
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import yaml
from dotenv import load_dotenv

log = logging.getLogger(__name__)

load_dotenv()  # 加载 .env


@dataclass
class ProxyConfig:
    enabled: bool
    url: str = ""

    def effective_url(self) -> Optional[str]:
        if not self.enabled:
            return None
        return self.url or os.environ.get("PROXY_URL", "")


@dataclass
class FetchConfig:
    max_items_per_source: int = 10
    hours_back: int = 30
    timeout: int = 30
    user_agent: str = ""


@dataclass
class LLMConfig:
    api_key: str = ""
    model: str = "gpt-4o-mini"
    base_url: str = ""
    temperature: float = 0.2
    max_concurrent: int = 5
    batch_size: int = 10


@dataclass
class PushConfig:
    channels: list[str] = None


@dataclass
class ReportConfig:
    categories_order: list[str] = None
    min_sources_for_verification: int = 2


@dataclass
class Config:
    proxy: ProxyConfig
    fetch: FetchConfig
    llm: LLMConfig
    push: PushConfig
    report: ReportConfig

    @classmethod
    def load(cls, config_path: str = "config.yaml") -> "Config":
        path = Path(config_path)
        if not path.exists():
            log.warning("config.yaml not found, using defaults")
            data = {}
        else:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

        proxy_data = data.get("proxy", {})
        proxy = ProxyConfig(
            enabled=proxy_data.get("enabled", False),
            url=proxy_data.get("url", "") or os.environ.get("PROXY_URL", ""),
        )

        fetch_data = data.get("fetch", {})
        fetch = FetchConfig(
            max_items_per_source=fetch_data.get("max_items_per_source", 10),
            hours_back=fetch_data.get("hours_back", 30),
            timeout=fetch_data.get("timeout", 30),
            user_agent=fetch_data.get("user_agent", ""),
        )

        llm_data = data.get("llm", {})
        llm = LLMConfig(
            api_key=os.environ.get("LLM_API_KEY", llm_data.get("api_key", "")),
            model=os.environ.get("LLM_MODEL", llm_data.get("model", "gpt-4o-mini")),
            base_url=os.environ.get("LLM_BASE_URL", llm_data.get("base_url", "")),
            temperature=llm_data.get("temperature", 0.2),
            max_concurrent=llm_data.get("max_concurrent", 5),
        )

        push_data = data.get("push", {})
        push = PushConfig(channels=push_data.get("channels", ["telegram"]))

        report_data = data.get("report", {})
        report = ReportConfig(
            categories_order=report_data.get("categories_order",
                ["国际", "政治", "经济", "金融", "科技", "社会", "环境", "其他"]),
            min_sources_for_verification=report_data.get(
                "min_sources_for_verification", 2),
        )

        return cls(proxy=proxy, fetch=fetch, llm=llm,
                  push=push, report=report)
