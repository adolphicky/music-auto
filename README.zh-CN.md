# 网易云音乐下载器

> [English](README.md) | [简体中文](README.zh-CN.md)

一个基于Python和Vue.js的网易云音乐下载工具，支持搜索、批量下载音乐，提供友好的Web界面。

## 🎯 页面功能

### 1. 音乐搜索 (`/search`)
- **功能描述**: 搜索单曲并下载
- **主要特性**:
  - 支持关键词搜索音乐
  - 多种音质选择（标准、极高、无损、Hi-Res等）
  - 实时搜索结果显示
  - 单曲下载和批量下载
  - 下载进度实时显示

### 2. 歌单搜索 (`/playlist-download`)
- **功能描述**: 搜索并批量下载歌单内容
- **主要特性**:
  - 支持歌单ID或关键词搜索
  - 歌单详情预览（包含歌曲列表）
  - 批量下载歌单内所有歌曲
  - 可配置下载音质和并发数
  - 下载进度跟踪

### 3. 歌手搜索 (`/artist-download`)
- **功能描述**: 搜索并下载歌手的所有作品
- **主要特性**:
  - 支持歌手名称搜索
  - 获取歌手所有歌曲列表
  - 多种匹配模式（精确匹配、部分匹配等）
  - 可设置下载数量限制
  - 批量下载歌手作品

### 4. 热门歌单 (`/hot-playlists`)
- **功能描述**: 浏览和下载网易云热门歌单
- **主要特性**:
  - 推荐歌单展示
  - 高品质歌单筛选
  - 分类歌单浏览
  - 按播放量排序
  - 一键下载热门歌单

### 5. 任务管理 (`/task-manager`)
- **功能描述**: 管理所有下载任务
- **主要特性**:
  - 实时任务状态监控
  - 下载进度可视化
  - 任务取消功能
  - 历史任务记录
  - 错误信息查看

### 全局功能
- **二维码登录**: 支持网易云账号扫码登录更新cookie
- **响应式设计**: 适配桌面和移动设备
- **实时通知**: 下载完成和错误提示

### 配置文件说明

配置文件：`config.json`

```json
{
    // ===========================================
    // 网易云音乐工具箱配置文件示例
    // ===========================================
    // 复制此文件为 config.json 并根据需要修改配置
    // ===========================================

    // 服务器配置
    "host": "0.0.0.0",                    // 服务器监听地址，0.0.0.0表示监听所有网络接口
    "port": 5000,                         // 服务器端口号
    "debug": false,                       // 调试模式，生产环境建议设为false
    "max_file_size": 524288000,           // 最大文件大小限制（字节），默认500MB
    "request_timeout": 30,                // 请求超时时间（秒）
    "log_level": "INFO",                  // 日志级别：DEBUG, INFO, WARNING, ERROR
    "cors_origins": "*",                  // CORS允许的源，*表示允许所有域名
    
    // 通用下载配置
    "download": {
        "base_dir": "downloads",          // 基础下载目录
        "max_concurrent": 3,              // 最大并发下载数
        "default_quality": "lossless",    // 默认音质：standard, exhigh, lossless, hires, sky, jyeffect, jymaster
        "include_lyric": true             // 是否包含歌词文件
    },
    
    // 单曲下载配置
    "music_download": {
        "sub_dir": "",                    // 单曲下载子目录，为空则使用基础目录
        "max_concurrent": 3               // 单曲下载最大并发数
    },
    
    // 歌单下载配置
    "playlist_download": {
        "sub_dir": "",                    // 歌单下载子目录，为空则使用基础目录
        "max_concurrent": 3,              // 歌单下载最大并发数
        "default_quality": "lossless",    // 歌单下载默认音质
        "include_lyric": true             // 歌单下载是否包含歌词
    },
    
    // 歌手下载配置
    "artist_download": {
        "sub_dir": "",                    // 歌手下载子目录，为空则使用基础目录
        "max_concurrent": 3,              // 歌手下载最大并发数
        "default_quality": "lossless",    // 歌手下载默认音质
        "default_limit": 50,              // 默认下载歌曲数量限制
        "default_match_mode": "exact_single", // 默认匹配模式：exact_single, exact_multi, partial, all
        "include_lyric": true,            // 歌手下载是否包含歌词
        "search_page_size": 100,          // 搜索分页大小
        "log_file_pattern": "artist_download_{timestamp}.log" // 日志文件命名模式
    },
    
    // 数据库配置
    "database": {
        "db_path": "downloads.db",        // SQLite数据库文件路径
        "recent_downloads_limit": 50      // 最近下载记录显示数量限制
    },
    
    // Cookie配置
    "cookie": {
        "cookie_file": "cookie.txt",      // Cookie存储文件路径
        "qr_login_max_attempts": 60       // 二维码登录最大尝试次数
    },
    

}
```

### 音质选项
- `standard` - 标准音质
- `exhigh` - 极高音质  
- `lossless` - 无损音质
- `hires` - Hi-Res音质
- `sky` - 沉浸环绕声
- `dolby` - 杜比全景声

## 🐳 Docker镜像信息

**镜像名称**: `adolphicky/auto-music`

**镜像特性**:
- 基于Python 3.13-slim
- 包含Node.js 20-alpine环境
- 使用Supervisor管理进程
- 健康检查支持
- 自动构建前端

**端口映射**:
- 统一入口：5000（容器内部）

**数据卷挂载**:
- `./downloads` → `/app/downloads`（下载目录）
- `./config.json` → `/app/config.json`（配置文件）
- `./cookie.txt` → `/app/cookie.txt`（Cookie文件）
- `./logs` → `/var/log/supervisor`（日志目录）
## 🔒 安全说明

- 应用需要网易云账号登录才能下载VIP音质
- Cookie信息存储在本地文件中，请妥善保管
- 建议在生产环境中配置适当的访问控制
- 默认监听所有网络接口，可根据需要修改绑定地址

## 📝 使用说明

1. **首次使用**: 访问前端界面，点击二维码登录进行账号认证
2. **搜索音乐**: 在搜索页面输入关键词，选择音质后下载
3. **批量下载**: 使用歌单或歌手功能进行批量下载
4. **下载管理**: 下载的文件保存在`downloads`目录中
5. **任务监控**: 在任务管理页面查看下载进度和状态

## 📄 许可证

本项目基于MIT许可证开源。

## 🤝 贡献

欢迎提交Issue和Pull Request来改进本项目。

## ⚠️ 免责声明

本项目仅用于学习和研究目的，请勿用于商业用途。下载的音乐文件请遵守相关版权法律法规，支持正版音乐。
