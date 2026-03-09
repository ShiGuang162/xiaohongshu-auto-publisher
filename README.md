# 小红书全自动发布工具 (Xiaohongshu Auto Publisher)

🤖 全自动发布小红书笔记的工具 - 高效、稳定、易扩展

## 功能特性

- ✅ 图文笔记发布
- ✅ 视频笔记发布
- ✅ 标签管理
- ✅ 定时发布
- ✅ 多账号支持

## 技术栈

- **Python 3.11+**
- **FastAPI** - 后端 API
- **Playwright** - 浏览器自动化
- **SQLite** - 本地配置存储

## 项目结构

```
xiaohongshu-auto-publisher/
├── src/
│   ├── core/          # 核心业务逻辑
│   ├── adapters/      # 平台适配器
│   └── utils/         # 工具函数
├── tests/             # 单元测试
├── docs/              # 文档
└── config/            # 配置文件
```

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 配置 API Key
export XHS_API_KEY="your-api-key"

# 运行
python -m src.main
```

## License

MIT License
