"""下载数据库管理模块

使用SQLite数据库记录已下载的歌曲信息，用于验证是否已下载过歌曲。
"""

import sqlite3
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class DownloadedSong:
    """已下载歌曲信息"""
    song_id: int
    song_name: str
    artists: str
    album: str
    file_path: str
    file_size: int
    download_time: float
    quality: str
    status: str  # 'success', 'failed', 'skipped'


class DownloadDatabase:
    """下载数据库管理类"""
    
    def __init__(self, db_path: str = "downloads.db"):
        """
        初始化数据库
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建下载记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS downloaded_songs (
                song_id INTEGER PRIMARY KEY,
                song_name TEXT NOT NULL,
                artists TEXT NOT NULL,
                album TEXT,
                file_path TEXT NOT NULL,
                file_size INTEGER DEFAULT 0,
                download_time REAL NOT NULL,
                quality TEXT NOT NULL,
                status TEXT NOT NULL,
                created_time REAL DEFAULT (strftime('%s', 'now')),
                updated_time REAL DEFAULT (strftime('%s', 'now'))
            )
        ''')
        
        # 创建索引以提高查询性能
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_song_id ON downloaded_songs(song_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_artists ON downloaded_songs(artists)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_path ON downloaded_songs(file_path)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_download_time ON downloaded_songs(download_time)')
        
        conn.commit()
        conn.close()
    
    def song_exists(self, song_id: int) -> bool:
        """
        检查歌曲是否已下载
        
        Args:
            song_id: 歌曲ID
            
        Returns:
            bool: 歌曲是否已存在
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT 1 FROM downloaded_songs WHERE song_id = ?', (song_id,))
        exists = cursor.fetchone() is not None
        
        conn.close()
        return exists
    
    def get_song_info(self, song_id: int) -> Optional[DownloadedSong]:
        """
        获取歌曲下载信息
        
        Args:
            song_id: 歌曲ID
            
        Returns:
            DownloadedSong: 歌曲信息，如果不存在则返回None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT song_id, song_name, artists, album, file_path, file_size, 
                   download_time, quality, status 
            FROM downloaded_songs 
            WHERE song_id = ?
        ''', (song_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return DownloadedSong(
                song_id=row[0],
                song_name=row[1],
                artists=row[2],
                album=row[3],
                file_path=row[4],
                file_size=row[5],
                download_time=row[6],
                quality=row[7],
                status=row[8]
            )
        return None
    
    def add_song(self, song_info: Dict[str, Any]) -> bool:
        """
        添加歌曲下载记录
        
        Args:
            song_info: 歌曲信息字典，包含以下字段：
                - song_id: 歌曲ID
                - song_name: 歌曲名称
                - artists: 歌手
                - album: 专辑
                - file_path: 文件路径
                - file_size: 文件大小
                - quality: 音质
                - status: 状态 ('success', 'failed', 'skipped')
                
        Returns:
            bool: 是否添加成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO downloaded_songs 
                (song_id, song_name, artists, album, file_path, file_size, 
                 download_time, quality, status, updated_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                song_info['song_id'],
                song_info['song_name'],
                song_info['artists'],
                song_info.get('album', ''),
                song_info['file_path'],
                song_info.get('file_size', 0),
                time.time(),
                song_info['quality'],
                song_info['status'],
                time.time()
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"添加歌曲记录失败: {e}")
            return False
    
    def update_song_status(self, song_id: int, status: str, file_size: int = 0) -> bool:
        """
        更新歌曲状态
        
        Args:
            song_id: 歌曲ID
            status: 新状态
            file_size: 文件大小
            
        Returns:
            bool: 是否更新成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE downloaded_songs 
                SET status = ?, file_size = ?, updated_time = ?
                WHERE song_id = ?
            ''', (status, file_size, time.time(), song_id))
            
            conn.commit()
            conn.close()
            return cursor.rowcount > 0
            
        except Exception as e:
            print(f"更新歌曲状态失败: {e}")
            return False
    
    def get_songs_by_artist(self, artist: str) -> List[DownloadedSong]:
        """
        获取指定歌手的所有已下载歌曲
        
        Args:
            artist: 歌手名称
            
        Returns:
            List[DownloadedSong]: 歌曲列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT song_id, song_name, artists, album, file_path, file_size, 
                   download_time, quality, status 
            FROM downloaded_songs 
            WHERE artists LIKE ? 
            ORDER BY download_time DESC
        ''', (f'%{artist}%',))
        
        songs = []
        for row in cursor.fetchall():
            songs.append(DownloadedSong(
                song_id=row[0],
                song_name=row[1],
                artists=row[2],
                album=row[3],
                file_path=row[4],
                file_size=row[5],
                download_time=row[6],
                quality=row[7],
                status=row[8]
            ))
        
        conn.close()
        return songs
    
    def get_recent_downloads(self, limit: int = 50) -> List[DownloadedSong]:
        """
        获取最近下载的歌曲
        
        Args:
            limit: 返回数量限制
            
        Returns:
            List[DownloadedSong]: 歌曲列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT song_id, song_name, artists, album, file_path, file_size, 
                   download_time, quality, status 
            FROM downloaded_songs 
            ORDER BY download_time DESC 
            LIMIT ?
        ''', (limit,))
        
        songs = []
        for row in cursor.fetchall():
            songs.append(DownloadedSong(
                song_id=row[0],
                song_name=row[1],
                artists=row[2],
                album=row[3],
                file_path=row[4],
                file_size=row[5],
                download_time=row[6],
                quality=row[7],
                status=row[8]
            ))
        
        conn.close()
        return songs
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取下载统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 总歌曲数
        cursor.execute('SELECT COUNT(*) FROM downloaded_songs')
        total_songs = cursor.fetchone()[0]
        
        # 成功下载数
        cursor.execute('SELECT COUNT(*) FROM downloaded_songs WHERE status = "success"')
        success_songs = cursor.fetchone()[0]
        
        # 失败下载数
        cursor.execute('SELECT COUNT(*) FROM downloaded_songs WHERE status = "failed"')
        failed_songs = cursor.fetchone()[0]
        
        # 跳过下载数
        cursor.execute('SELECT COUNT(*) FROM downloaded_songs WHERE status = "skipped"')
        skipped_songs = cursor.fetchone()[0]
        
        # 总文件大小
        cursor.execute('SELECT SUM(file_size) FROM downloaded_songs WHERE status = "success"')
        total_size = cursor.fetchone()[0] or 0
        
        # 歌手数量
        cursor.execute('SELECT COUNT(DISTINCT artists) FROM downloaded_songs')
        artist_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_songs': total_songs,
            'success_songs': success_songs,
            'failed_songs': failed_songs,
            'skipped_songs': skipped_songs,
            'total_size': total_size,
            'artist_count': artist_count,
            'success_rate': (success_songs / total_songs * 100) if total_songs > 0 else 0
        }
    
    def cleanup_orphaned_records(self) -> int:
        """
        清理文件已不存在但数据库记录仍然存在的记录
        
        Returns:
            int: 清理的记录数
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取所有记录
        cursor.execute('SELECT song_id, file_path FROM downloaded_songs')
        records = cursor.fetchall()
        
        deleted_count = 0
        for song_id, file_path in records:
            if not Path(file_path).exists():
                cursor.execute('DELETE FROM downloaded_songs WHERE song_id = ?', (song_id,))
                deleted_count += 1
        
        conn.commit()
        conn.close()
        return deleted_count


# 全局数据库实例
download_db = DownloadDatabase()


if __name__ == "__main__":
    # 测试代码
    db = DownloadDatabase()
    
    # 测试添加记录
    test_song = {
        'song_id': 123456,
        'song_name': '测试歌曲',
        'artists': '测试歌手',
        'album': '测试专辑',
        'file_path': '/path/to/song.flac',
        'file_size': 1024000,
        'quality': 'lossless',
        'status': 'success'
    }
    
    if db.add_song(test_song):
        print("✅ 添加记录成功")
    else:
        print("❌ 添加记录失败")
    
    # 测试查询
    if db.song_exists(123456):
        print("✅ 歌曲存在检查成功")
    
    song_info = db.get_song_info(123456)
    if song_info:
        print(f"✅ 获取歌曲信息成功: {song_info.song_name}")
    
    # 测试统计
    stats = db.get_statistics()
    print(f"📊 统计信息: {stats}")
