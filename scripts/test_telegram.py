"""Telegram 机器人配置测试脚本

填完 .env 后跑这个验证：
  python scripts/test_telegram.py
"""
import sys
import os
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
proxy = os.environ.get("PROXY_URL", "")

print("─" * 50)
print("Telegram 配置测试")
print("─" * 50)
print(f"Bot Token: {token[:10]}...{token[-4:] if len(token) > 14 else '(空)'}")
print(f"Chat ID:   {chat_id or '(空)'}")
print(f"Proxy:     {proxy or '(直连)'}")
print("─" * 50)

if not token or not chat_id:
    print("❌ TELEGRAM_BOT_TOKEN 或 TELEGRAM_CHAT_ID 未配置！")
    sys.exit(1)

import httpx

transport = httpx.HTTPTransport(proxy=proxy) if proxy else None

# 测试 1: 验证 token
print("\n✨ 测试 1: 验证 bot token\n")
try:
    with httpx.Client(transport=transport, timeout=15) as client:
        r = client.get(f"https://api.telegram.org/bot{token}/getMe")
        if r.status_code == 200 and r.json().get("ok"):
            bot_info = r.json()["result"]
            print(f"✅ Bot 验证成功！")
            print(f"   名称: {bot_info.get('first_name')}")
            print(f"   用户名: @{bot_info.get('username')}")
            print(f"   ID: {bot_info.get('id')}")
        else:
            print(f"❌ Token 无效: {r.text[:200]}")
            sys.exit(1)
except Exception as e:
    print(f"❌ 连接失败: {e}")
    print(f"   如果你在中国大陆，可能需要 VPN")
    sys.exit(1)

# 测试 2: 发送消息
print("\n✨ 测试 2: 发送测试消息\n")
try:
    test_msg = "🌍 来自新闻助手的问候！\n\n如果你看到这条消息，说明 Telegram 配置成功 ✅"
    with httpx.Client(transport=transport, timeout=15) as client:
        r = client.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": test_msg,
                "parse_mode": "Markdown",
            },
        )
        if r.status_code == 200 and r.json().get("ok"):
            print(f"✅ 消息发送成功！请查看 Telegram")
        else:
            err = r.json().get("description", r.text[:200])
            print(f"❌ 发送失败: {err}")
            if "chat not found" in err:
                print("   💡 提示：你需要先给 bot 发一条消息（/start）激活对话")
            elif "Forbidden" in err:
                print("   💡 提示：你需要先给 bot 发一条消息（/start）激活对话")
            sys.exit(1)
except Exception as e:
    print(f"❌ 发送异常: {e}")
    sys.exit(1)

print("\n─" * 50)
print("✅ Telegram 配置全部通过！可以跑 python scripts/run_daily.py 了")