# NetEase Cloud Music Downloader

> [English](README.md) | [简体中文](README.zh-CN.md)

A NetEase Cloud Music download tool based on Python and Vue.js, supporting search, batch downloads, and providing a user-friendly web interface.

## 🎯 Page Features

### 1. Music Search (`/search`)
- **Function Description**: Search and download individual songs
- **Key Features**:
  - Support keyword-based music search
  - Multiple audio quality options (Standard, High Quality, Lossless, Hi-Res, etc.)
  - Real-time search results display
  - Individual and batch download options
  - Real-time download progress display

### 2. Playlist Search (`/playlist-download`)
- **Function Description**: Search and batch download playlist content
- **Key Features**:
  - Support playlist ID or keyword search
  - Playlist detail preview (including song list)
  - Batch download all songs in playlist
  - Configurable download quality and concurrency
  - Download progress tracking

### 3. Artist Search (`/artist-download`)
- **Function Description**: Search and download all works by an artist
- **Key Features**:
  - Support artist name search
  - Get all songs by the artist
  - Multiple matching modes (exact match, partial match, etc.)
  - Configurable download quantity limit
  - Batch download artist works

### 4. Hot Playlists (`/hot-playlists`)
- **Function Description**: Browse and download NetEase Cloud Music's popular playlists
- **Key Features**:
  - Recommended playlists display
  - High-quality playlist filtering
  - Category-based playlist browsing
  - Sort by play count
  - One-click download of hot playlists

### 5. Task Manager (`/task-manager`)
- **Function Description**: Manage all download tasks
- **Key Features**:
  - Real-time task status monitoring
  - Download progress visualization
  - Task cancellation functionality
  - Historical task records
  - Error information viewing

### Global Features
- **QR Code Login**: Support NetEase account login for VIP audio quality
- **Responsive Design**: Compatible with desktop and mobile devices
- **Real-time Notifications**: Download completion and error alerts

## 🚀 Deployment & Usage

### Docker Deployment (Recommended)

#### Environment Requirements
- Docker
- Docker Compose

#### Deployment Steps

1. **Prepare directories and files**
```bash
# Create necessary directories
mkdir -p downloads
mkdir -p logs

# Copy configuration file (optional)
cp config.json.example config.json
```

2. **Start services**
```bash
# Start using docker-compose
docker-compose up -d

# Check service status
docker-compose logs -f
```

3. **Access the application**
- Frontend interface: http://localhost:3000
- Backend API: http://localhost:5000

#### Docker Image Information
- **Image Name**: `adolphicky/auto-music`
- **Base Image**: Python 3.13-slim + Node.js 18
- **Process Management**: Supervisor
- **Health Check**: Automatic service status monitoring

### Manual Deployment

#### Backend Deployment

1. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

2. **Configure environment**
```bash
cp config.json.example config.json
# Edit config.json file to configure parameters
```

3. **Start backend service**
```bash
python main.py
```

#### Frontend Deployment

1. **Install dependencies**
```bash
npm install
```

2. **Development mode**
```bash
npm run dev
```

3. **Production build**
```bash
npm run build
```

## ⚙️ Configuration & Development

### Configuration File Description

Configuration file: `config.json`

```json
{
    // Server configuration
    "host": "0.0.0.0",
    "port": 5000,
    "debug": false,
    "max_file_size": 524288000,
    "request_timeout": 30,
    "log_level": "INFO",
    "cors_origins": "*",
    
    // General download configuration
    "download": {
        "base_dir": "downloads",
        "max_concurrent": 3,
        "default_quality": "lossless",
        "include_lyric": true
    },
    
    // Music download configuration
    "music_download": {
        "sub_dir": "",
        "max_concurrent": 3
    },
    
    // Playlist download configuration
    "playlist_download": {
        "sub_dir": "",
        "max_concurrent": 3,
        "default_quality": "lossless",
        "include_lyric": true
    },
    
    // Artist download configuration
    "artist_download": {
        "sub_dir": "",
        "max_concurrent": 3,
        "default_quality": "lossless",
        "default_limit": 50,
        "default_match_mode": "exact_single",
        "include_lyric": true,
        "search_page_size": 100
    },
    
    // Database configuration
    "database": {
        "db_path": "downloads.db",
        "recent_downloads_limit": 50
    },
    
    // Cookie configuration
    "cookie": {
        "cookie_file": "cookie.txt",
        "qr_login_max_attempts": 60
    }
}
```

### Audio Quality Options
- `standard` - Standard Quality
- `exhigh` - High Quality  
- `lossless` - Lossless Quality
- `hires` - Hi-Res Quality
- `sky` - Immersive Surround Sound
- `dolby` - Dolby Atmos

### Development Environment Setup

#### Backend Development
```bash
# Install dependencies
pip install -r requirements.txt

# Development mode
python main.py

# Debug mode (enable detailed logs)
python main.py --debug
```

#### Frontend Development
```bash
# Install dependencies
npm install

# Development mode
npm run dev

# Production build
npm run build

# Preview build results
npm run preview
```

### Project Structure
```
music-auto/
├── src/                    # Frontend source code
│   ├── components/         # Vue components
│   │   ├── SearchComponent.vue          # Music search
│   │   ├── PlaylistSearchComponent.vue  # Playlist search
│   │   ├── ArtistDownloadComponent.vue  # Artist download
│   │   ├── HotPlaylistsComponent.vue    # Hot playlists
│   │   ├── TaskManagerComponent.vue     # Task management
│   │   └── QRLoginComponent.vue         # QR code login
│   ├── services/
│   │   └── apiService.js   # API service
│   ├── router/
│   │   └── index.js        # Router configuration
│   ├── App.vue            # Main application
│   └── main.js            # Entry file
├── *.py                   # Backend Python files
├── config.json.example    # Configuration example
├── docker-compose.yml     # Docker orchestration
├── Dockerfile            # Docker image build
├── requirements.txt      # Python dependencies
└── package.json         # Frontend dependencies
```

### API Documentation

#### Authentication
- `GET /api/auth/qr-code` - Get login QR code
- `GET /api/auth/check-login` - Check login status
- `POST /api/auth/save-cookie` - Save Cookie

#### Music
- `GET /api/music/search` - Search music
- `POST /api/music/download` - Download music
- `GET /api/playlist/detail` - Get playlist details
- `POST /api/playlist/download` - Download playlist
- `GET /api/artist/songs` - Get artist songs
- `POST /api/artist/download` - Download artist works
- `GET /api/hot/playlists` - Get hot playlists

#### Task Management
- `GET /api/tasks` - Get all tasks
- `GET /api/tasks/<task_id>` - Get task details
- `POST /api/tasks/<task_id>/cancel` - Cancel task
- `POST /api/tasks/clear-cancelled` - Clear cancelled tasks

#### System
- `GET /health` - Health check
- `GET /api/info` - API information

## 🐳 Docker Image Information

**Image Name**: `adolphicky/auto-music`

**Image Features**:
- Based on Python 3.13-slim
- Includes Node.js 18 environment
- Uses Supervisor for process management
- Health check support
- Automatic frontend build

**Port Mapping**:
- Frontend interface: 3000 → 3000 (host)
- Backend API: 5000 (container internal)

**Volume Mounts**:
- `./downloads` → `/app/downloads` (download directory)
- `./config.json` → `/app/config.json` (configuration file)
- `./cookie.txt` → `/app/cookie.txt` (Cookie file)
- `./logs` → `/var/log` (log directory)

## 🔒 Security Notes

- Application requires NetEase account login for VIP audio quality
- Cookie information is stored in local files, please keep it secure
- Recommended to configure appropriate access control in production environments
- Default listens on all network interfaces, can be modified as needed

## 📝 Usage Instructions

1. **First Use**: Access the frontend interface, click QR code login for account authentication
2. **Search Music**: Enter keywords on the search page, select audio quality and download
3. **Batch Download**: Use playlist or artist functions for batch downloads
4. **Download Management**: Downloaded files are saved in the `downloads` directory
5. **Task Monitoring**: Check download progress and status in the task management page

## 📄 License

This project is open source under the MIT License.

## 🤝 Contributing

Welcome to submit Issues and Pull Requests to improve this project.

## ⚠️ Disclaimer

This project is for learning and research purposes only. Please do not use it for commercial purposes. Downloaded music files should comply with relevant copyright laws and regulations. Support genuine music.
