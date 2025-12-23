---
title: Video Extractor API
emoji: 📹
colorFrom: blue
colorTo: indigo
sdk: docker
app_file: app.py
pinned: false
---

# Video Extractor API

这是一个基于 Botasaurus 的 API 服务，用于从 https://qushuiyin.me/ 提取视频下载链接。

## 功能

- 通过 API 输入视频 URL
- 自动绕过 Cloudflare 盾牌
- 模拟浏览器操作获取视频下载链接
- Docker 部署支持

## API 端点

### GET /get_video

提取视频下载链接。

**参数：**
- `url` (string): 要处理的视频 URL

**示例：**
```
GET /get_video?url=https://example.com/video
```

**响应：**
```json
{
  "video_url": "https://download.example.com/video.mp4"
}
```

## 部署

### 本地运行

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 运行 API：
```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

### Docker 部署

1. 构建镜像：
```bash
docker build -t video-extractor .
```

2. 运行容器：
```bash
docker run -p 8000:8000 video-extractor
```

### 配置代理（可选）

如果遇到 Cloudflare 检测问题，可以配置代理：

```bash
# 设置环境变量
export PROXY_URL="http://your_proxy_address:your_proxy_port"

# 或者在 Docker 中
docker run -p 8000:8000 -e PROXY_URL="http://your_proxy_address:your_proxy_port" video-extractor
```

在 Hugging Face Spaces 中，可以在 Settings -> Variables and secrets 中添加 `PROXY_URL` 环境变量。

### Hugging Face Spaces 部署

项目已配置自动同步到 HF Spaces，通过 GitHub Actions 实现。

## 注意事项

- 确保系统安装了 Chrome 浏览器
- API 依赖 Botasaurus 的反检测功能来绕过防护