# 🌍 国际新闻助手 (News Assistant)

每天自动抓取 22 个国际新闻源 → AI 分类/摘要/翻译 → 交叉验证 → 推送到手机 + H5 网页。

## 🎯 两种数据消费方式

### 1️⃣ 推送（主动接收）
- **Telegram**（推荐）/ Email / Bark (iOS) / Server酱 (微信)
- 每天定时收到简报，要点一目了然
- 点击直达原文

### 2️⃣ H5 网页（被动浏览）
- 自动部署到 GitHub Pages，每天生成漂亮 H5 页面
- 移动端自适应，支持深色模式
- 首页列出所有历史日期，可点开看
- 永久存档，随时回看

**实际效果截图**：见 `docs/preview.html` 或访问部署后的 GitHub Pages。

## 🎯 功能特性

- ✅ **22 个数据源**（Reuters, AP, BBC, FT, Bloomberg, WSJ, Economist, Politico, Semafor, Al Jazeera, Nikkei Asia, Rest of World, TechCrunch, The Information, 404 Media, ProPublica, Bellingcat, Our World in Data, SEC EDGAR, Federal Reserve）
- 🤖 **LLM 处理**：自动翻译/分类/摘要（OpenAI / DeepSeek / 通义千问 / Moonshot / Ollama 等任意 OpenAI 兼容 API）
- 🔍 **交叉验证**：聚类同一事件的多源报道，给出"共识 + 分歧 + 最终事实"
- 📱 **多渠道推送**：Telegram / Email / Bark / Server酱
- 🌐 **H5 网页**：每天生成精美 HTML 页面，自动部署到 GitHub Pages
- ⏰ **自动调度**：GitHub Actions（推荐，**云端跑无需 VPN，无需开电脑**）或 Windows Task Scheduler
- 💾 **本地存档**：Markdown + HTML 双格式

## 🚀 快速开始

### 方式 A：GitHub Actions 云端运行（最推荐）⭐

**优势**：无需 VPN，无需开电脑，每天自动跑，自动部署 H5 网页，自动备份报告。

**步骤**：

1. **Fork 这个项目到你的 GitHub 账号**

2. **启用 GitHub Pages**（Settings → Pages → Source 选 GitHub Actions）

3. **添加 Secrets**（Settings → Secrets and variables → Actions）：
   
   | Secret 名称 | 必填 | 说明 |
   |---|---|---|
   | `LLM_API_KEY` | ✅ | LLM 的 API Key |
   | `LLM_MODEL` | ⭕ | 默认 `gpt-4o-mini` |
   | `LLM_BASE_URL` | ⭕ | 兼容 API 时填，如 `https://api.deepseek.com/v1` |
   | `TELEGRAM_BOT_TOKEN` | ⭕ | Telegram Bot Token |
   | `TELEGRAM_CHAT_ID` | ⭕ | 你的 Telegram chat_id |
   | `EMAIL_*` | ⭕ | 邮件推送 |
   | `BARK_URL` | ⭕ | iOS Bark 推送 |
   | `SERVERCHAN_KEY` | ⭕ | 微信推送 |

4. **首次手动触发测试**：Actions → Daily News Assistant → Run workflow
   - 默认 dry_run=true 不推送
   - 确认无问题后改 false

5. **完成！** 每天 UTC 23:30（北京时间次日 07:30）自动跑

6. **访问 H5 页面**：`https://你的用户名.github.io/news-assistant/`

### 方式 B：本地运行（用 VPN 代理）

```powershell
cd C:\Users\keer\Desktop\codex-projects\news-assistant
pip install -r requirements.txt
copy .env.example .env
# 编辑 .env，填 LLM_API_KEY 和 TELEGRAM_BOT_TOKEN

python scripts/run_daily.py --dry-run   # 试运行
python scripts/run_daily.py            # 正式跑

# 设置每日定时（管理员 PowerShell）
powershell -ExecutionPolicy Bypass -File scripts/setup_scheduler.ps1
```

本地报告生成在 `output/`，可以用 `python -m http.server 8765 --directory output` 在浏览器预览。

## 📱 推送渠道配置

### Telegram（最推荐）

**配置步骤**：
1. 在 Telegram 搜索 `@BotFather`，发送 `/newbot` 创建 bot，获取 token
2. 搜索 `@userinfobot`，给它发任意消息获取你的 chat_id
3. 在你的 bot 对话框发一条消息（激活对话）
4. 把 token 和 chat_id 填到 `.env`

### Email

```env
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=your@gmail.com
EMAIL_PASSWORD=xxxx xxxx xxxx xxxx    # 应用专用密码
EMAIL_FROM=your@gmail.com
EMAIL_TO=you@anywhere.com
```

### Bark（iOS 用户）

App Store 搜"Bark"下载，安装后得到 URL 如 `https://api.day.app/yourkey/`。

### Server酱（微信）

https://sct.ftqq.com/ 登录获取 sendkey。

## 🌐 H5 网页效果

每天的报告会自动生成一份 H5 页面，特点是：

- 📱 移动端自适应（响应式布局）
- 🌗 自动适配深色模式（`prefers-color-scheme`）
- 🎨 类别色标（政治=粉、经济=橙、金融=绿、科技=紫 等）
- ✅ 多源验证标识（绿边）/ 📄 单源（灰边）/ 🔥 重点（红边）
- 📊 顶部数据统计卡片
- 📂 来源列表可折叠展开
- ⬅️ 首页返回链接

**截图位置**：

- `output/2026-09-27.html` - 单日报告
- `output/index.html` - 首页（历史日期列表）

部署到 GitHub Pages 后，访问 `https://你的用户名.github.io/news-assistant/` 即可在手机上浏览。

## ⚙️ 配置说明

### config.yaml

```yaml
proxy:
  enabled: true
  url: "http://127.0.0.1:7897"
  # GitHub Actions 上跑时设为 enabled: false

fetch:
  max_items_per_source: 10
  hours_back: 30
  timeout: 30

llm:
  model: "gpt-4o-mini"
  temperature: 0.2
  max_concurrent: 5

push:
  channels:
    - telegram
    # - email
    # - bark
    # - serverchan

report:
  min_sources_for_verification: 2
```

### 调整数据源

编辑 `src/fetcher/sources.py`，可以：
- 添加新的 RSS 源
- 修改已有的 feed URL
- 调整每个源的 `category_hint`

## 💰 成本估算

每天约 200 条新闻：

| 模型 | 每日成本 | 每月成本 |
|---|---|---|
| GPT-4o-mini | $0.02 | **$0.6** |
| DeepSeek-V3 | $0.002 | **$0.06** |
| 通义千问 qwen-turbo | 免费额度 | **~免费** |

GitHub Actions 免费额度：每月 2000 分钟，本项目单次约 2-3 分钟，**完全够用**。

GitHub Pages：免费，无限流量。

## 📂 项目结构

```
news-assistant/
├── src/
│   ├── fetcher/         # RSS 抓取器
│   ├── processor/       # LLM 处理 + 交叉验证
│   ├── pusher/          # 推送（Telegram/Email/Bark/微信）
│   ├── storage/         # 报告生成
│   │   ├── markdown_writer.py  # Markdown 报告
│   │   └── html_writer.py      # ⭐ H5 网页
│   ├── config.py
│   └── main.py          # 主编排
├── scripts/
│   ├── run_daily.py
│   └── setup_scheduler.ps1
├── tests/
│   ├── test_smoke.py
│   └── demo_report.py   # 生成样例报告
├── .github/workflows/
│   └── daily.yml        # ⭐ GitHub Actions（含 Pages 部署）
├── output/              # 生成的报告
└── data/                # 历史数据
```

## 🛠️ 常见问题

**Q: 本地抓不到？**
A: 检查 VPN 是否在 7897 端口运行；用 `--verbose` 看详细日志

**Q: GitHub Pages 没显示？**
A: Settings → Pages → Source 选 "GitHub Actions"；等几分钟生效；查看 Actions 日志

**Q: LLM 限流了？**
A: 调小 `llm.max_concurrent`；换更便宜/更宽松的模型

**Q: 某个源抓不到？**
A: RSS 偶尔会变。脚本会自动跳过失败的源。可以编辑 `src/fetcher/sources.py` 更新 feed URL

**Q: 怎么测试交叉验证？**
A: 跑 `python tests/demo_report.py` 看示例报告（生成 Markdown + HTML）

**Q: 想要更花哨的 H5？**
A: 编辑 `src/storage/html_writer.py` 里的 `CSS` 变量，可以改样式；改 `_render_event()` 改布局

**Q: 想本地预览 H5？**
A: `cd output && python -m http.server 8765`，然后浏览器打开 `http://localhost:8765`

## 📜 License

MIT