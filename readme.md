# 网易云音乐工具箱

## 📖 项目简介

网易云音乐工具箱是一个功能强大的网易云音乐解析和下载工具，提供Web界面和命令行工具两种使用方式。支持歌曲搜索、单曲解析、歌单解析、专辑解析、音乐下载等功能，支持多种音质选择，包括无损、Hi-Res等高品质音频格式。

## ✨ 功能特性

### 🎵 核心功能
- **Web界面**：直观的网页操作界面，支持歌曲搜索、解析和下载
- **API接口**：完整的RESTful API，支持程序化调用
- **API兼容性**：自动处理API版本兼容性问题，确保功能稳定
- **歌手批量下载**：根据歌手名称批量下载所有歌曲
- **歌单批量下载**：解析歌单并批量下载所有歌曲
- **专辑解析**：批量解析专辑中的所有歌曲
- **音乐下载**：支持多种音质的音乐文件下载
- **歌词获取**：自动获取并保存歌词信息
- **元数据写入**：自动写入歌曲标题、艺术家、专辑等元数据

### 🎧 音质支持
- `standard`：标准音质 (128kbps)
- `exhigh`：极高音质 (320kbps)
- `lossless`：无损音质 (FLAC)
- `hires`：Hi-Res音质 (24bit/96kHz)
- `jyeffect`：高清环绕声
- `sky`：沉浸环绕声
- `jymaster`：超清母带

## 🚀 快速开始

### 环境要求
- Python 3.7+
- 网易云音乐黑胶会员账号（用于获取高音质资源）

### 安装步骤

1. **克隆项目**
```bash
git clone <项目地址>
cd project/tieshui/music_auto
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置Cookie（可选）**
```bash
# 运行二维码登录脚本获取Cookie
python qr_login.py
```

4. **启动Web服务**
```bash
python main.py
```

5. **访问界面**
打开浏览器访问：`http://localhost:5000`

## 🚀 一键启动脚本（Windows）

项目提供了便捷的一键启动脚本，适用于Windows系统：

### 启动服务
双击运行 `start.bat` 脚本，或使用命令行：
```cmd
start.bat
```

脚本会自动：
- ✅ 检查Python和Node.js环境
- 📦 安装必要的依赖包
- 🚀 启动后端API服务（端口：5000）
- 🌐 启动前端Web界面（端口：3000）
- 📡 显示服务访问地址

### 停止服务
双击运行 `stop.bat` 脚本，或使用命令行：
```cmd
stop.bat
```

### 服务访问地址
- **前端界面**：http://localhost:3000
- **后端API**：http://localhost:5000
- **下载目录**：downloads/

## 🐧 Linux一键启动脚本

项目也提供了Linux环境下的启停脚本：

### 启动服务
```bash
# 给脚本添加执行权限
chmod +x start.sh stop.sh

# 启动服务
./start.sh
```

### 停止服务
```bash
./stop.sh
```

### 脚本功能
- ✅ 自动检查Python 3和Node.js环境
- 📦 自动安装依赖包
- 🚀 后台启动后端和前端服务
- 📋 生成日志文件（backend.log, frontend.log）
- 🔧 保存进程PID便于管理
- 🧹 自动清理残留进程

### 服务管理
- **查看服务状态**：`ps aux | grep -E "(python.*main.py|npm.*run.*dev)"`
- **查看后端日志**：`tail -f backend.log`
- **查看前端日志**：`tail -f frontend.log`

## 🐳 Docker部署

### 使用Docker Compose

1. **修改配置**（可选）
   编辑`docker-compose.yml`文件，根据需要修改端口映射等配置

2. **启动服务**
```bash
docker-compose up -d
```

3. **查看日志**
```bash
docker-compose logs -f
```

4. **停止服务**
```bash
docker-compose down
```

## 🌐 Web界面使用

### 1. 歌曲搜索
1. 选择「歌曲搜索」功能
2. 输入搜索关键词
3. 点击「搜索」按钮
4. 在搜索结果中点击「解析」或「下载」按钮

### 2. 单曲解析
1. 选择「单曲解析」功能
2. 输入歌曲ID或网易云音乐链接
3. 选择音质等级
4. 点击「解析」按钮查看歌曲信息
5. 点击「下载」按钮下载音乐文件

### 3. 歌单解析
1. 选择「歌单解析」功能
2. 输入歌单ID或歌单链接
3. 点击「解析歌单」按钮
4. 查看歌单信息和歌曲列表
5. 点击单首歌曲的「解析」或「下载」按钮

### 4. 专辑解析
1. 选择「专辑解析」功能
2. 输入专辑ID或专辑链接
3. 点击「解析专辑」按钮
4. 查看专辑信息和歌曲列表
5. 点击单首歌曲的「解析」或「下载」按钮

### 5. 链接格式支持
项目支持多种网易云音乐链接格式：
- **歌曲链接**：`https://music.163.com/song?id=123456`
- **歌单链接**：`https://music.163.com/playlist?id=123456`
- **专辑链接**：`https://music.163.com/album?id=123456`
- **直接ID**：`123456`

## 💻 命令行工具使用

### 歌手批量下载器

#### 基本用法
```bash
python artist_downloader.py "歌手名称"
```

#### 完整用法
```bash
python artist_downloader.py "歌手名称" [音质] [数量限制] [匹配模式] [下载目录]
```

#### 参数说明
| 参数 | 说明 | 默认值 | 可选值 |
|------|------|--------|--------|
| 歌手名称 | 要搜索和下载的歌手名称 | 必填 | 任意歌手名 |
| 音质 | 下载的音质等级 | lossless | standard, exhigh, lossless, hires, sky, jyeffect, jymaster |
| 数量限制 | 最多下载的歌曲数量 | 50 | 1-200（支持分页获取所有歌曲） |
| 匹配模式 | 歌曲搜索匹配方式 | exact_single | exact_single, exact_multi, partial, all |
| 下载目录 | 下载文件保存目录 | artist_downloads | 任意有效目录路径 |

#### 匹配模式说明
- `exact_single`：完全匹配且单歌手（只下载独唱歌曲）
- `exact_multi`：完全匹配但允许多歌手（下载包括合唱作品）
- `partial`：部分匹配（下载歌手名包含关键词的歌曲）
- `all`：返回所有搜索结果（不进行歌手过滤）

#### 使用示例
```bash
# 下载周深的歌曲（默认音质和数量）
python artist_downloader.py "周深"

# 下载周杰伦的Hi-Res音质歌曲，最多100首
python artist_downloader.py "周杰伦" hires 100

# 下载包含"陈"字的歌手歌曲，使用部分匹配模式
python artist_downloader.py "陈" lossless 30 partial

# 下载到自定义目录
python artist_downloader.py "林俊杰" exhigh 50 exact_single my_music
```

### 歌单批量下载器

#### 基本用法
```bash
python playlist_downloader.py "歌单ID或链接"
```

#### 完整用法
```bash
python playlist_downloader.py "歌单ID或链接" [音质] [下载目录]
```

#### 参数说明
| 参数 | 说明 | 默认值 | 可选值 |
|------|------|--------|--------|
| 歌单ID或链接 | 歌单ID或网易云音乐链接 | 必填 | 数字ID或完整URL |
| 音质 | 下载的音质等级 | lossless | standard, exhigh, lossless, hires, sky, jyeffect, jymaster |
| 下载目录 | 下载文件保存目录 | playlist_downloads | 任意有效目录路径 |

#### 目录命名规则
- 下载目录会自动创建在指定的下载目录下
- 目录名使用歌单名称（自动清理文件名中的非法字符）
- 例如：歌单"经典华语流行"会创建目录"经典华语流行"

#### 下载目录结构优化

项目采用智能目录结构管理，根据不同的下载模式自动优化文件存储：

**1. 单曲下载（Web界面）**
```
downloads/music/
├── 周深/                    # 歌手目录
│   ├── 周深 - 大鱼.flac
│   └── 周深 - 大鱼.lrc
└── 林俊杰/                  # 歌手目录
    └── 林俊杰 - 不为谁而作的歌.flac
```

**2. 歌单批量下载**
```
downloads/playlists/
└── 热门歌单/                # 歌单目录
    ├── 周深 - 歌曲1.flac    # 直接保存在歌单目录
    ├── 林俊杰 - 歌曲2.flac
    └── 邓紫棋 - 歌曲3.flac
```

**3. 歌手批量下载**
```
downloads/artists/
└── 周深/                    # 歌手目录
    ├── 周深 - 歌曲1.flac
    └── 周深 - 歌曲2.flac
```

**4. 多歌手歌曲处理**
- 多歌手歌曲使用第一个歌手名创建目录
- 例如："周深/林俊杰 - 不为谁而作的歌.flac"保存在"周深"目录下

**5. 智能目录控制**
- 歌单下载：不重复创建歌手目录（避免`歌单名/歌手名/歌手名/`问题）
- 歌手下载：正常创建歌手目录
- 单曲下载：自动按歌手分类存储

#### 使用示例
```bash
# 使用歌单ID下载
python playlist_downloader.py "123456789"

# 使用歌单链接下载Hi-Res音质
python playlist_downloader.py "https://music.163.com/playlist?id=123456789" hires

# 下载到自定义目录
python playlist_downloader.py "987654321" lossless my_playlists

### 热门歌单URL获取器

#### 功能说明
获取网易云音乐的热门歌单信息，包括个性化推荐歌单、精品歌单和歌单分类，并显示歌单的详细信息及URL。

#### 基本用法
```bash
# 获取个性化推荐歌单
python hot_playlist_fetcher.py --personalized

# 获取精品歌单
python hot_playlist_fetcher.py --high-quality

# 获取歌单分类
python hot_playlist_fetcher.py --categories
```

#### 完整用法
```bash
python hot_playlist_fetcher.py [选项] [参数]
```

#### 参数说明
| 参数 | 说明 | 默认值 | 可选值 |
|------|------|--------|--------|
| --personalized | 获取个性化推荐歌单 | - | - |
| --high-quality | 获取精品歌单 | - | - |
| --categories | 获取歌单分类 | - | - |
| --category | 精品歌单分类 | 全部 | 华语、欧美、日语、韩语等 |
| --limit | 返回歌单数量限制 | 20 | 1-100 |
| --save | 保存结果到JSON文件 | - | 任意文件名 |

#### 使用示例
```bash
# 获取10个个性化推荐歌单
python hot_playlist_fetcher.py --personalized --limit 10

# 获取华语分类的精品歌单，最多15个
python hot_playlist_fetcher.py --high-quality --category "华语" --limit 15

# 获取歌单分类并保存到文件
python hot_playlist_fetcher.py --categories --save categories.json

# 获取推荐歌单并保存结果
python hot_playlist_fetcher.py --personalized --save playlists.json

# 组合使用多个功能
python hot_playlist_fetcher.py --personalized --high-quality --categories
```

#### 输出信息
每个歌单包含以下信息：
- **歌单ID**：网易云音乐歌单的唯一标识符
- **名称**：歌单标题
- **URL**：歌单的网易云音乐网页链接
- **播放量**：歌单的播放次数（格式化显示）
- **歌曲数量**：歌单包含的歌曲数量
- **创建者**：歌单创建者信息
- **描述**：歌单描述（截断显示）
- **标签**：歌单标签列表

#### 测试功能
```bash
# 运行测试脚本验证热门歌单功能
python test_hot_playlist.py
```
```

## 🔌 API接口文档

### 基础信息
- **服务地址**：`http://localhost:5000`
- **请求方式**：POST（部分接口支持GET）
- **响应格式**：JSON

### 接口列表

#### 1. 健康检查
```http
GET /health
```

**响应示例**：
```json
{
    "code": 200,
    "message": "服务运行正常",
    "data": {
        "status": "healthy",
        "timestamp": "2024-01-01T12:00:00Z"
    }
}
```

#### 2. 歌曲搜索
```http
POST /search
```

**请求参数**：
```json
{
    "keyword": "周深",
    "limit": 10,
    "offset": 0
}
```

**参数说明**：
- `keyword`：搜索关键词（必填）
- `limit`：返回结果数量限制，默认10，最大100
- `offset`：分页偏移量，默认0

**响应示例**：
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "songs": [
            {
                "id": 123456,
                "name": "大鱼",
                "artists": "周深",
                "album": "大鱼",
                "duration": 245000
            }
        ],
        "total": 100
    }
}
```

#### 3. 单曲解析
```http
POST /song
```

**请求参数**：
```json
{
    "id": "123456",
    "quality": "lossless"
}
```

**响应示例**：
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "song": {
            "id": 123456,
            "name": "大鱼",
            "artists": "周深",
            "album": "大鱼",
            "duration": 245000,
            "download_url": "http://example.com/song.flac",
            "file_size": 25467890
        }
    }
}
```

#### 4. 歌单解析
```http
POST /playlist
```

**请求参数**：
```json
{
    "id": "123456789"
}
```

**响应示例**：
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "playlist": {
            "id": "123456789",
            "name": "经典华语流行",
            "creator": "网易云音乐",
            "song_count": 50,
            "songs": [
                {
                    "id": 123456,
                    "name": "大鱼",
                    "artists": "周深",
                    "album": "大鱼"
                }
            ]
        }
    }
}
```

#### 5. 专辑解析
```http
POST /album
```

**请求参数**：
```json
{
    "id": "123456"
}
```

**响应示例**：
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "album": {
            "id": "123456",
            "name": "大鱼",
            "artist": "周深",
            "song_count": 10,
            "songs": [
                {
                    "id": 123456,
                    "name": "大鱼",
                    "artists": "周深"
                }
            ]
        }
    }
}
```

#### 6. 音乐下载
```http
POST /download
```

**请求参数**：
```json
{
    "id": "123456",
    "quality": "lossless"
}
```

**响应**：返回音频文件流，支持直接下载

## 🔧 故障排除

### 常见问题

#### 1. 导入模块失败
**问题**：运行脚本时出现`ImportError`
**解决**：确保所有依赖已安装，检查Python路径设置

#### 2. Cookie失效
**问题**：无法获取高音质资源
**解决**：重新运行`python qr_login.py`更新Cookie

#### 3. 下载失败
**问题**：歌曲下载失败或文件损坏
**解决**：
- 检查网络连接
- 确认账号有相应音质的下载权限
- 尝试更换音质等级

#### 4. 端口占用
**问题**：Web服务启动失败，端口被占用
**解决**：修改`main.py`中的端口配置或停止占用端口的程序

#### 5. 歌单解析失败
**问题**：无法获取歌单详情，提示"无法获取歌单详情"错误
**解决**：
- 项目已修复API兼容性问题，确保歌单解析功能正常工作
- 如果仍然失败，请确保Cookie有效
- 检查网络连接是否正常
- 确认歌单ID或链接格式正确
- 项目会自动处理API版本兼容性问题

### 日志查看
项目会生成详细的日志文件，位于程序运行目录的`logs`文件夹中，可用于排查问题。

## 📁 项目结构

```
project/tieshui/music_auto/
├── main.py                 # Web服务主程序
├── music_api.py           # 网易云音乐API封装
├── music_downloader.py    # 音乐下载器
├── artist_downloader.py   # 歌手批量下载器
├── playlist_downloader.py # 歌单批量下载器
├── cookie_manager.py      # Cookie管理
├── qr_login.py           # 二维码登录
├── download_db.py        # 下载记录数据库
├── requirements.txt      # Python依赖
├── readme.md            # 项目文档
├── templates/           # Web模板文件
│   └── index.html
├── artist_downloads/    # 歌手下载文件目录
├── playlist_downloads/  # 歌单下载文件目录
└── downloads/          # 普通下载文件目录
```

## ⚙️ 配置文件说明

项目使用 `config.json` 文件进行配置管理，支持灵活的配置选项。

### 配置文件结构
```json
{
    "host": "0.0.0.0",
    "port": 5000,
    "debug": false,
    "max_file_size": 524288000,
    "request_timeout": 30,
    "log_level": "INFO",
    "cors_origins": "*",
    
    "download": {
        "base_dir": "downloads",
        "max_concurrent": 3,
        "default_quality": "lossless",
        "include_lyric": true
    },
    
    "music_download": {
        "sub_dir": "",
        "max_concurrent": 3,
        "default_quality": "lossless"
    },
    
    "playlist_download": {
        "sub_dir": "",
        "max_concurrent": 3,
        "default_quality": "lossless",
        "include_lyric": true
    },
    
    "artist_download": {
        "sub_dir": "",
        "max_concurrent": 3,
        "default_quality": "lossless",
        "default_limit": 50,
        "default_match_mode": "exact_single",
        "include_lyric": true,
        "search_page_size": 100,
        "log_file_pattern": "artist_download_{timestamp}.log"
    },
    
    "database": {
        "db_path": "downloads.db",
        "recent_downloads_limit": 50
    },
    
    "cookie": {
        "cookie_file": "cookie.txt",
        "qr_login_max_attempts": 60
    },
    
    "api": {
        "search_limit": 1000,
        "playlist_limit": 1000,
        "pic_size": 300
    },
    
    "debug_config": {
        "search_limit": 5
    }
}
```

### 配置项说明

#### 服务器配置
- `host`: 服务器监听地址，默认 `0.0.0.0`
- `port`: 服务器端口，默认 `5000`
- `debug`: 调试模式，默认 `false`
- `max_file_size`: 最大文件大小限制，默认 `500MB`
- `request_timeout`: 请求超时时间，默认 `30秒`
- `log_level`: 日志级别，默认 `INFO`
- `cors_origins`: CORS允许的源，默认 `*`

#### 下载配置
- `base_dir`: 基础下载目录，默认 `downloads`
- `max_concurrent`: 最大并发下载数，默认 `3`
- `default_quality`: 默认音质，默认 `lossless`
- `include_lyric`: 是否包含歌词，默认 `true`

#### 模块特定配置
- **音乐下载**: 子目录、并发数、默认音质
- **歌单下载**: 子目录、并发数、默认音质、歌词包含
- **歌手下载**: 子目录、并发数、默认音质、数量限制、匹配模式、搜索分页大小

#### 数据库配置
- `db_path`: 数据库文件路径，默认 `downloads.db`
- `recent_downloads_limit`: 最近下载记录限制，默认 `50`

#### Cookie配置
- `cookie_file`: Cookie文件路径，默认 `cookie.txt`
- `qr_login_max_attempts`: 二维码登录最大尝试次数，默认 `60`

#### API配置
- `search_limit`: 搜索限制，默认 `1000`
- `playlist_limit`: 歌单限制，默认 `1000`
- `pic_size`: 图片大小，默认 `300`

## 📁 项目结构详解

```
project/tieshui/music_auto/
├── main.py                 # Web服务主程序
├── music_api.py           # 网易云音乐API封装
├── music_downloader.py    # 音乐下载器（支持同步/异步下载）
├── artist_downloader.py   # 歌手批量下载器
├── playlist_downloader.py # 歌单批量下载器
├── hot_playlist_fetcher.py # 热门歌单获取器
├── cookie_manager.py      # Cookie管理
├── qr_login.py           # 二维码登录
├── download_db.py        # 下载记录数据库（SQLite）
├── config.json          # 配置文件
├── requirements.txt     # Python依赖
├── readme.md           # 项目文档
├── templates/          # Web模板文件
│   └── index.html
├── downloads/          # 下载文件目录
│   ├── music/         # 单曲下载目录
│   ├── playlists/     # 歌单下载目录
│   └── artists/       # 歌手下载目录
└── logs/              # 日志文件目录
```

## 🔧 高级配置

### 自定义下载目录结构
通过修改配置文件中的 `sub_dir` 参数，可以自定义各个模块的下载目录结构：

```json
{
    "music_download": {
        "sub_dir": "my_music"
    },
    "playlist_download": {
        "sub_dir": "my_playlists"
    },
    "artist_download": {
        "sub_dir": "my_artists"
    }
}
```

### 性能调优
- 调整 `max_concurrent` 控制并发下载数
- 修改 `search_page_size` 优化搜索性能
- 配置 `request_timeout` 调整网络请求超时

### 日志配置
- 修改 `log_level` 控制日志详细程度
- 自定义 `log_file_pattern` 设置日志文件命名

## 📄 许可证

本项目仅供学习和研究使用，请遵守相关法律法规，尊重版权。

## 🤝 贡献

欢迎提交Issue和Pull Request来改进本项目。

## ⚠️ 免责声明

本工具仅用于技术学习和研究目的，请勿用于商业用途。下载的音乐文件请在24小时内删除，支持正版音乐。

## 📋 更新日志

### 2025-12-27
- **优化**：修复目录重复问题，实现智能目录结构管理
- **文档**：全面更新readme，添加详细配置说明
- **功能**：支持分页搜索获取所有歌曲

### 2025-12-25
- **修复**：修复`get_playlist_detail`方法返回结构，确保与歌单下载器兼容
- **修复**：更新歌单解析API端点，从`api/v6/playlist/detail`升级到`api/v3/playlist/detail`
- **优化**：改进歌单详情请求参数格式，添加时间戳和完整歌曲获取参数
- **增强**：添加API调用失败时的回退机制，自动尝试兼容版本
- **文档**：添加歌单解析问题的故障排除说明
