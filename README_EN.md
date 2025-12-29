# NetEase Cloud Music Auto Downloader

**Language**: [中文](README.md) | English

A full-stack NetEase Cloud Music download tool based on Flask + Vue.js, supporting multiple audio quality downloads, batch downloads, QR code login, and more.

## 🎯 Features

### Frontend Web Interface Features
- **Music Search** - Search and download individual songs with multiple audio quality options
- **Playlist Search** - Search and batch download playlist content
- **Artist Search** - Search and download all works by an artist
- **Hot Playlists** - Browse and download NetEase Cloud Music's popular playlists
- **QR Code Login** - Support NetEase account login for VIP audio quality
- **Responsive Design** - Compatible with desktop and mobile devices

### Download Features
- **Multiple Audio Quality Support**: Standard, High Quality, Lossless, Hi-Res, Dolby Atmos, etc.
- **Batch Download**: Support for playlist and artist works batch downloads
- **Concurrency Control**: Configurable maximum concurrent downloads
- **Lyrics Download**: Optional lyrics file download
- **Download History**: Record download history for easy management

## 🚀 Quick Start

### Docker Deployment (Recommended)

#### 1. Create necessary directories and files
```bash
# Create download directory
mkdir -p downloads
mkdir -p logs

# Copy configuration file (optional)
cp config.json.example config.json
```

#### 2. Deploy using docker-compose
```bash
# Start services
docker-compose up -d

# Check service status
docker-compose logs -f
```

#### 3. Access the application
- Frontend interface: http://localhost:34303
- Backend API: http://localhost:5000

### Manual Deployment

#### Backend Deployment
```bash
# Install Python dependencies
pip install -r requirements.txt

# Configure environment
cp config.json.example config.json
# Edit config.json file to configure parameters

# Start backend service
python main.py
```

#### Frontend Deployment
```bash
# Install dependencies
npm install

# Development mode
npm run dev

# Production build
npm run build
```

## ⚙️ Configuration

### Main Configuration Parameters
Configuration file: `config.json`

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

### Audio Quality Options
- `standard` - Standard Quality
- `exhigh` - High Quality  
- `lossless` - Lossless Quality
- `hires` - Hi-Res Quality
- `sky` - Immersive Surround Sound
- `dolby` - Dolby Atmos

## 📁 Project Structure

```
music-auto/
├── src/                    # Frontend source code
│   ├── components/         # Vue components
│   │   ├── SearchComponent.vue          # Music search
│   │   ├── PlaylistSearchComponent.vue  # Playlist search
│   │   ├── ArtistDownloadComponent.vue  # Artist download
│   │   ├── HotPlaylistsComponent.vue    # Hot playlists
│   │   └── QRLoginComponent.vue         # QR code login
│   ├── services/
│   │   └── apiService.js   # API service
│   ├── App.vue            # Main application
│   └── main.js            # Entry file
├── *.py                   # Backend Python files
├── config.json.example    # Configuration example
├── docker-compose.yml     # Docker orchestration
├── Dockerfile            # Docker image build
└── requirements.txt      # Python dependencies
```

## 🔧 API Endpoints

### Authentication
- `GET /api/auth/qr-code` - Get login QR code
- `GET /api/auth/check-login` - Check login status
- `POST /api/auth/save-cookie` - Save Cookie

### Music
- `GET /api/music/search` - Search music
- `POST /api/music/download` - Download music
- `GET /api/playlist/detail` - Get playlist details
- `POST /api/playlist/download` - Download playlist
- `GET /api/artist/songs` - Get artist songs
- `POST /api/artist/download` - Download artist works
- `GET /api/hot/playlists` - Get hot playlists

### System
- `GET /health` - Health check

## 🐳 Docker Image Information

**Image Name**: `adolphicky/auto-music`

**Image Features**:
- Based on Python 3.13-slim
- Includes Node.js 18 environment
- Uses Supervisor for process management
- Health check support
- Automatic frontend build

**Port Mapping**:
- Frontend interface: 3000 → 34303 (host)
- Backend API: 5000 (container internal)

**Volume Mounts**:
- `./downloads` → `/app/downloads` (download directory)
- `./config.json` → `/app/config.json` (configuration file)
- `./cookie.txt` → `/app/cookie.txt` (Cookie file)
- `./logs` → `/var/log/supervisor` (log directory)

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

## 🛠️ Development

### Backend Development
```bash
# Install dependencies
pip install -r requirements.txt

# Development mode
python main.py
```

### Frontend Development
```bash
# Enter frontend directory
cd src

# Install dependencies
npm install

# Development mode
npm run dev

# Production build
npm run build
```

## 📄 License

This project is open source under the MIT License.

## 🤝 Contributing

Welcome to submit Issues and Pull Requests to improve this project.

## ⚠️ Disclaimer

This project is for learning and research purposes only. Please do not use it for commercial purposes. Downloaded music files should comply with relevant copyright laws and regulations. Support genuine music.