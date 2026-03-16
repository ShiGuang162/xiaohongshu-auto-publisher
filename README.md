# 小红书全自动发布工具 (Xiaohongshu Auto Publisher)

🤖 全自动发布小红书笔记的工具 - 高效、稳定、易扩展

## ✨ 功能特性

- ✅ **扫码登录** - 支持小红书 APP 扫码登录
- ✅ **Cookie 管理** - 自动保存和刷新登录状态
- ✅ **图文发布** - 一键发布图文笔记
- ✅ **图片压缩** - 自动压缩图片至小红书规格
- ✅ **定时发布** - 支持定时任务队列
- ⏳ **视频发布** - 开发中
- ⏳ **多账号支持** - 计划中

## 🛠️ 技术栈

- **Python 3.11+**
- **Playwright** - 浏览器自动化 (扫码登录)
- **FastAPI** - 后端 API (计划中)
- **Pillow** - 图片处理
- **Requests** - HTTP 请求

## 📦 安装

```bash
# 克隆项目
cd /home/ubuntu/.openclaw/workspace/projects/xiaohongshu-auto-publisher

# 安装依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器
playwright install chromium
```

## 🚀 快速开始

### 1. 扫码登录

```bash
python -m src.main login
```

会弹出浏览器显示二维码，用小红书 APP 扫码即可。登录成功后 Cookie 会自动保存到 `~/.xiaohongshu/cookies.json`。

### 2. 检查登录状态

```bash
python -m src.main check
```

### 3. 发布图文笔记

```bash
python -m src.main publish \
  -t "我的笔记标题" \
  -d "这是笔记的描述内容..." \
  -i image1.jpg image2.jpg image3.jpg \
  --topics "日常，生活，分享"
```

### 4. 压缩图片

```bash
python -m src.main compress -i photo1.jpg photo2.jpg --quality 85
```

## 📁 项目结构

```
xiaohongshu-auto-publisher/
├── src/
│   ├── main.py              # 主入口
│   ├── core/
│   │   ├── auth.py          # 用户认证 (扫码登录)
│   │   └── publisher.py     # 内容发布
│   ├── adapters/
│   │   └── xhs_api.py       # 小红书 API 封装
│   └── utils/
│       ├── cookie_mgr.py    # Cookie 管理
│       └── media.py         # 媒体处理
├── tests/                   # 单元测试
├── docs/                    # 文档
├── requirements.txt         # 依赖
└── README.md
```

## 🔧 API 使用

### Python API

```python
from src.core.auth import XiaohongshuAuth
from src.core.publisher import NotePublisher
from src.utils.media import ImageProcessor

# 登录
auth = XiaohongshuAuth()
await auth.ensure_logged_in()

# 压缩图片
ImageProcessor.compress("photo.jpg", max_width=1080)

# 发布笔记
publisher = NotePublisher()
result = publisher.publish_image_note(
    title="标题",
    desc="描述",
    images=["photo1.jpg", "photo2.jpg"],
    topics=["日常", "生活"]
)

if result["success"]:
    print(f"发布成功！笔记 ID: {result['note_id']}")
```

## ⚠️ 注意事项

1. **合规使用** - 请遵守小红书社区规范，不要发布违规内容
2. **频率限制** - 建议不要短时间内大量发布，避免被限流
3. **账号安全** - 妥善保管 Cookie 文件，不要泄露
4. **功能限制** - 视频发布等功能仍在开发中

## 📝 更新日志

### v0.1.0 (2026-03-11)
- ✅ 扫码登录功能
- ✅ Cookie 管理
- ✅ 图文笔记发布
- ✅ 图片压缩处理
- ⏳ 视频发布 (开发中)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 License

MIT License
