# 网易云音乐自动下载器

**语言**: 中文 | [English](README_EN.md)

一个基于Flask + Vue.js的全栈网易云音乐下载工具，支持多种音质下载、批量下载、二维码登录等功能。

## 🎯 功能特性

### 前端Web界面功能
- **音乐搜索** - 搜索单曲并下载，支持多种音质选择
- **歌单搜索** - 搜索并批量下载歌单内容
- **歌手搜索** - 搜索并下载歌手的所有作品
- **热门歌单** - 浏览和下载网易云热门歌单
- **二维码登录** - 支持网易云账号登录获取VIP音质
- **响应式设计** - 适配桌面和移动设备

### 下载特性
- **多种音质支持**：标准音质、极高音质、无损音质、Hi-Res音质、杜比全景声等
- **批量下载**：支持歌单和歌手作品的批量下载
- **并发控制**：可配置最大并发下载数
- **歌词下载**：可选是否下载歌词文件
- **下载历史**：记录下载历史，便于管理

## 🚀 快速开始

### Docker部署（推荐）

#### 1. 创建必要目录和文件
```bash
# 创建下载目录
mkdir -p downloads
mkdir -p logs

# 复制配置文件（可选）
cp config.json.example config.json
```

#### 2. 使用docker-compose部署
```bash
# 启动服务
docker-compose up -d

# 查看服务状态
docker-compose logs -f
```

#### 3. 访问应用
- 前端界面：http://localhost:34303
- 后端API：http://localhost:5000

### 手动部署

#### 后端部署
```bash
# 安装Python依赖
pip install -r requirements.txt

# 配置环境
cp config.json.example config.json
# 编辑config.json文件配置参数

# 启动后端服务
python main.py
```

#### 前端部署
```bash
# 安装依赖
npm install

# 开发模式运行
npm run dev

# 生产构建
npm run build
```

## ⚙️ 配置说明

### 主要配置参数
配置文件：`config.json`

```json
{
  "host": "0.0.0.0",
  "port": 5000,
  "debug": false,
  "log_level": "INFO",
  
  "download": {
    "base_dir": "downloads",
    "max_concurrent": 3,
    "default_quality": "lossless",
    "include_lyric": true
  },
  
  "cookie": {
    "cookie_file": "cookie.txt",
    "qr_login_max_attempts": 60
  }
}
```

### 音质选项
- `standard` - 标准音质
- `exhigh` - 极高音质  
- `lossless` - 无损音质
- `hires` - Hi-Res音质
- `sky` - 沉浸环绕声
- `dolby` - 杜比全景声

## 📁 项目结构

```
music-auto/
├── src/                    # 前端源码
│   ├── components/         # Vue组件
│   │   ├── SearchComponent.vue          # 音乐搜索
│   │   ├── PlaylistSearchComponent.vue  # 歌单搜索
│   │   ├── ArtistDownloadComponent.vue  # 歌手下载
│   │   ├── HotPlaylistsComponent.vue    # 热门歌单
│   │   └── QRLoginComponent.vue         # 二维码登录
│   ├── services/
│   │   └── apiService.js   # API服务
│   ├── App.vue            # 主应用
│   └── main.js            # 入口文件
├── *.py                   # 后端Python文件
├── config.json.example    # 配置示例
├── docker-compose.yml     # Docker编排
├── Dockerfile            # Docker镜像构建
└── requirements.txt      # Python依赖
```

## 🔧 API接口

### 认证相关
- `GET /api/auth/qr-code` - 获取登录二维码
- `GET /api/auth/check-login` - 检查登录状态
- `POST /api/auth/save-cookie` - 保存Cookie

### 音乐相关
- `GET /api/music/search` - 搜索音乐
- `POST /api/music/download` - 下载音乐
- `GET /api/playlist/detail` - 获取歌单详情
- `POST /api/playlist/download` - 下载歌单
- `GET /api/artist/songs` - 获取歌手歌曲
- `POST /api/artist/download` - 下载歌手作品
- `GET /api/hot/playlists` - 获取热门歌单

### 系统相关
- `GET /health` - 健康检查

## 🐳 Docker镜像信息

**镜像名称**: `adolphicky/auto-music`

**镜像特性**:
- 基于Python 3.13-slim
- 包含Node.js 18环境
- 使用Supervisor管理进程
- 健康检查支持
- 自动构建前端

**端口映射**:
- 前端界面：3000 → 34303（主机）
- 后端API：5000（容器内部）

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

1. **首次使用**：访问前端界面，点击二维码登录进行账号认证
2. **搜索音乐**：在搜索页面输入关键词，选择音质后下载
3. **批量下载**：使用歌单或歌手功能进行批量下载
4. **下载管理**：下载的文件保存在`downloads`目录中

## 🛠️ 开发说明

### 后端开发
```bash
# 安装依赖
pip install -r requirements.txt

# 开发模式运行
python main.py
```

### 前端开发
```bash
# 进入前端目录
cd src

# 安装依赖
npm install

# 开发模式
npm run dev

# 构建生产版本
npm run build
```

## 📄 许可证

本项目基于MIT许可证开源。

## 🤝 贡献

欢迎提交Issue和Pull Request来改进本项目。

## ⚠️ 免责声明

本项目仅用于学习和研究目的，请勿用于商业用途。下载的音乐文件请遵守相关版权法律法规，支持正版音乐。