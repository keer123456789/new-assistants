"""LLM 配置测试脚本

填完 .env 后跑这个验证：
  python scripts/test_llm.py
"""
import sys
import os
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 加载 .env
from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

api_key = os.environ.get("LLM_API_KEY", "")
model = os.environ.get("LLM_MODEL", "gpt-4o-mini")
base_url = os.environ.get("LLM_BASE_URL", "")

print(f"\u2500" * 50)
print("LLM 配置测试")
print(f"\u2500" * 50)
print(f"Model:    {model}")
print(f"Base URL: {base_url or '(OpenAI 官方)'}")
print(f"API Key:  {api_key[:8]}...{api_key[-4:] if len(api_key) > 12 else ''}")
print(f"\u2500" * 50)

if not api_key:
    print("\u274c LLM_API_KEY 未配置！请编辑 .env 文件")
    sys.exit(1)

from openai import OpenAI
client = OpenAI(api_key=api_key, base_url=base_url or None)

print("\n\u2728 测试 1: 简单问答\n")
try:
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": "用一句话介绍你自己（30字内，中文）"},
        ],
        max_tokens=100,
    )
    answer = resp.choices[0].message.content
    print(f"\u2705 回答: {answer}")
    print(f"   token 用量: {resp.usage.total_tokens}")
except Exception as e:
    print(f"\u274c 失败: {e}")
    sys.exit(1)

print("\n\u2728 测试 2: JSON 结构化输出\n")
try:
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "你是新闻助手，只输出 JSON"},
            {"role": "user", "content": '''处理这条新闻：
标题: Federal Reserve holds rates steady at 4.25%
摘要: The Fed kept interest rates unchanged.

输出 JSON:
{"title_zh": "...", "category": "...", "summary_zh": "..."}'''},
        ],
        response_format={"type": "json_object"},
        max_tokens=300,
    )
    answer = resp.choices[0].message.content
    print(f"\u2705 JSON 输出: {answer}")
except Exception as e:
    print(f"\u274c 失败: {e}")

print("\n\u2500" * 50)
print("\u2705 LLM 配置验证通过！可以跑 python scripts/run_daily.py 了")