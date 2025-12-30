# NetEase Cloud Music Downloader

> [English](README.md) | [Simplified Chinese](README.zh-CN.md)

A NetEase Cloud Music downloader based on Python and Vue.js, supporting searching and batch downloading of music, and providing a user-friendly web interface.

## 🎯 Page Functions

### 1. Music Search (`/search`)

- **Function Description**: Search for and download individual songs

- **Key Features**:

- Supports keyword search for music

- Multiple audio quality options (Standard, Ultra High, Lossless, Hi-Res, etc.)

- Real-time search results display

- Single song download and batch download

- Real-time download progress display

### 2. Playlist Search (`/playlist-download`)

- **Function Description**: Search for and batch download playlist content

- **Key Features**:

- Supports playlist ID or keyword search

- Playlist details preview (including song list)

- Batch download of all songs in a playlist

- Configurable download audio quality and concurrency

- Download progress tracking

### 3. Artist Search (`/artist-download`)

- **Function Description**: Search for and download all works by an artist

- **Key Features**:

- Supports artist name search

- Get an artist's complete song list

- Multiple matching modes (exact match, partial match, etc.)

- Set download quantity limits

- Batch download artist's works

### 4. Hot Playlists (`/hot-playlists`)

- **Function Description**: Browse and download NetEase Cloud Music's hot playlists

- **Main Features**:

- Recommended playlist display

- High-quality playlist filtering

- Categorized playlist browsing

- Sort by play count

- One-click download of hot playlists

### 5. Task Management (`/task-manager`)

- **Function Description**: Manage all download tasks

- **Main Features**:

- Real-time task status monitoring

- Download progress visualization

- Task cancellation function

- Historical task records

- Error message viewing

### Global Functions

- **QR code login**: Supports NetEase Cloud Music account QR code login and cookie update

- **Responsive design**: Adapts to desktop and mobile devices

- **Real-time notifications**: Download complete and error message

### Configuration file description

Configuration file: `config.json`

```json

{
// ============================================

/ // Example of NetEase Cloud Music Toolbox configuration file

/ // ===========================================

/ // Copy this file to config.json and modify the configuration as needed

/ // =============================================

/ // Server configuration

"host": "0.0.0.0", // Server listening address, 0.0.0.0 indicates listening on all network interfaces

"port": 5000, // Server port number

"debug": false, // Debug mode, recommended to set to false in production environment

"max_file_size": 524288000, // Maximum file size limit (bytes), default 500MB

"request_timeout": 30, // Request timeout (seconds)

"log_level": "INFO", // Log level: DEBUG, INFO, WARNING, ERROR

"cors_origins": "*", // CORS allowed origins, * indicates all domains are allowed

/ // General download configuration

"download": {

"base_dir": "downloads", // Base download directory

"max_concurrent": 3, // Maximum concurrent downloads

"default_quality": "lossless", // Default audio quality: standard, exhigh, lossless, hires, sky, jyeffect, jymaster

"include_lyric": true // Whether to include lyrics files

},

/ // Single track download configuration

"music_download": {

"sub_dir": "", // // Single song download subdirectory; if empty, the base directory will be used.

"max_concurrent": 3 // Maximum concurrent downloads for a single song

},

/ // Playlist download configuration

"playlist_download": {

"sub_dir": "", // Playlist download subdirectory; if empty, the base directory will be used.

"max_concurrent": 3, // Maximum concurrent downloads for a playlist.

"default_quality": "lossless", // Default audio quality for playlist downloads.

"include_lyric": true // Whether to include lyrics in playlist downloads.

},

/ // Artist download configuration

"artist_download": {

"sub_dir": "", // Artist download subdirectory; if empty, the base directory will be used.

"max_concurrent": 3, // Maximum concurrent downloads for an artist.

"default_quality": "lossless", // Default audio quality for artist downloads.

"default_limit": 50, // Default limit on the number of songs downloaded.

"default_match_mode": "exact_single", // Default matching modes: exact_single, exact_multi, partial, all

"include_lyric": true, // Whether the artist download includes lyrics

"search_page_size": 100, // Search page size

"log_file_pattern": "artist_download_{timestamp}.log" // Log file naming pattern

},

// Database configuration

"database": {

"db_path": "downloads.db", // SQLite database file path

"recent_downloads_limit": 50 // Limit on the number of recent download records displayed

},

// Cookie configuration

"cookie": {

"cookie_file": "cookie.txt", // Cookie storage file path

"qr_login_max_attempts": 60 // Maximum number of QR code login attempts

  },

}
```

### Audio Quality Options

- `standard` - Standard audio quality

- `exhigh` - Extremely high audio quality

- `lossless` - Lossless Audio Quality

- `hires` - Hi-Res audio quality

- `sky` - Immersive surround sound

- `dolby` - Dolby Atmos

## 🐳 Docker Image Information

**Image Name**: `adolphicky/auto-music`

**Image Features**:

- Based on Python 3.13-slim

- Includes Node.js 20-alpine environment

- Process management using Supervisor

- Health check support

- Automatic frontend build

**Port Mapping**:

- Unified entry point: 5000 (inside the container)

**Data Volume Mounting**:

- `./downloads` → `/app/downloads` (download directory)

- `./config.json` → `/app/config.json` (configuration file)

- `./cookie.txt` → `/app/cookie.txt` (cookie file)

- `./logs` → `/var/log/supervisor` (log directory)
## 🔒 Security Notice

- This application requires a NetEase Cloud Music account to download VIP audio quality.

- Cookie information is stored in a local file; please keep it safe.

- It is recommended to configure appropriate access control in a production environment.

- By default, it listens on all network interfaces; you can modify the binding address as needed.

## 📝 Instructions for Use

1. **First-time Use**: Access the front-end interface and scan the QR code to log in and authenticate your account.

2. **Search Music**: Enter keywords on the search page, select the audio quality, and download.

3. **Batch Download**: Use the playlist or artist function to download in batches.

4. **Download Management**: Downloaded files are saved in the `downloads` directory.

5. **Task Monitoring**: View download progress and status on the task management page.

## 📄 License

This project is open source under the MIT License.

## 🤝 Contributions

You are welcome to submit Issues and Pull Requests to improve this project.

## ⚠️ Disclaimer

This project is for learning and research purposes only and should not be used for commercial purposes. Please comply with relevant copyright laws and regulations when downloading music files and support genuine music.

