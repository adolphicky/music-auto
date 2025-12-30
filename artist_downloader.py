"""歌手歌曲批量下载器

提供搜索歌手并批量下载其所有歌曲的功能，包含歌词和元数据。
"""

import os
import sys
import time
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    from music_api import NeteaseAPI, APIException, search_music, lyric_v1
    from cookie_manager import CookieManager, CookieException
    from music_downloader import MusicDownloader, DownloadException, DownloadResult
    from download_db import DownloadDatabase
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保所有依赖模块存在且可用")
    sys.exit(1)


@dataclass
class ArtistDownloadConfig:
    """歌手下载配置"""
    artist_name: str
    quality: str = None
    limit: int = None
    download_dir: str = None
    include_lyric: bool = True
    max_concurrent: int = None
    match_mode: str = None  # 匹配模式: exact_single, exact_multi, partial, all
    
    def __post_init__(self):
        """初始化后处理，从配置文件读取默认值"""
        # 从配置文件读取默认配置
        try:
            from main import config
            # 使用统一下载目录配置
            base_dir = config.download_config.get('base_dir', 'downloads')
            artist_sub_dir = config.artist_download_config.get('sub_dir')
            
            # 设置默认值
            if self.quality is None:
                self.quality = config.artist_download_config.get('default_quality', 'lossless')
            if self.limit is None:
                self.limit = config.artist_download_config.get('default_limit', 50)
            if self.download_dir is None:
                # 如果sub_dir为空，直接使用base_dir；否则组合路径
                if artist_sub_dir:
                    self.download_dir = str(Path(base_dir) / artist_sub_dir)
                else:
                    self.download_dir = base_dir
            if self.max_concurrent is None:
                self.max_concurrent = config.artist_download_config.get('max_concurrent', 3)
            if self.match_mode is None:
                self.match_mode = config.artist_download_config.get('default_match_mode', 'exact_single')
            if self.include_lyric is True:
                self.include_lyric = config.artist_download_config.get('include_lyric', True)
        except ImportError:
            # 如果无法导入config，使用默认值
            if self.quality is None:
                self.quality = "lossless"
            if self.limit is None:
                self.limit = 50
            if self.download_dir is None:
                self.download_dir = "downloads/artists"
            if self.max_concurrent is None:
                self.max_concurrent = 3
            if self.match_mode is None:
                self.match_mode = "exact_single"


@dataclass
class SongDownloadResult:
    """单曲下载结果"""
    song_id: int
    name: str
    artists: str
    album: str
    status: str  # 'success' or 'failed'
    file_path: Optional[str] = None
    file_size: int = 0
    error_message: str = ""
    lyric: str = ""


class ArtistDownloader:
    """歌手歌曲批量下载器"""
    
    def __init__(self, config: ArtistDownloadConfig):
        self.config = config
        
        # 直接使用配置的下载目录，让MusicDownloader统一处理歌手目录
        self.download_path = Path(config.download_dir)
        self.download_path.mkdir(exist_ok=True, parents=True)
        
        # 然后设置日志记录器
        self.logger = self._setup_logger()
        
        # 初始化依赖
        self.cookie_manager = CookieManager()
        self.api = NeteaseAPI()
        self.downloader = MusicDownloader(
            download_dir=str(self.download_path),
            max_concurrent=config.max_concurrent,
            create_artist_dir=True  # 歌手下载模式下创建歌手目录
        )
        
        # 初始化数据库
        self.db = DownloadDatabase()
        
        self.logger.info(f"歌手下载器初始化完成，下载目录: {self.download_path.absolute()}")
    
    def _sanitize_artist_name(self, artist_name: str) -> str:
        """清理歌手名，用于创建目录名"""
        import re
        # 移除或替换非法字符
        illegal_chars = r'[<>:"/\\|?*]'
        safe_name = re.sub(illegal_chars, '_', artist_name)
        # 移除前后空格和点
        safe_name = safe_name.strip(' .')
        return safe_name or "unknown_artist"
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger('artist_downloader')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # 控制台处理器
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
            
            # 文件处理器 - 保存到artist_downloads目录
            log_dir = self.download_path.parent  # artist_downloads目录
            log_dir.mkdir(exist_ok=True, parents=True)  # 确保目录存在
            
            # 从配置文件获取日志文件命名模式
            try:
                from main import config
                log_pattern = config.artist_download_config.get('log_file_pattern', 'artist_download_{timestamp}.log')
            except ImportError:
                log_pattern = 'artist_download_{timestamp}.log'
            
            # 准备占位符替换数据
            import datetime
            current_time = datetime.datetime.now()
            
            placeholder_data = {
                '{timestamp}': str(int(time.time())),
                '{date}': current_time.strftime('%Y-%m-%d'),
                '{time}': current_time.strftime('%H-%M-%S'),
                '{artist}': self._sanitize_artist_name(self.config.artist_name),
                '{mode}': self.config.match_mode
            }
            
            # 替换所有占位符
            log_filename = log_pattern
            for placeholder, value in placeholder_data.items():
                log_filename = log_filename.replace(placeholder, value)
            
            log_file = log_dir / log_filename
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    def _get_cookies(self) -> Dict[str, str]:
        """获取Cookie"""
        try:
            cookies = self.cookie_manager.get_cookie_for_request()
            if not cookies:
                self.logger.warning("未找到有效的Cookie，部分功能可能受限")
            return cookies
        except CookieException as e:
            self.logger.warning(f"获取Cookie失败: {e}")
            return {}
    
    def _format_file_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
    
    def search_artist_songs(self) -> List[Dict[str, Any]]:
        """搜索歌手的歌曲（支持分页获取所有歌曲）"""
        # 在try块外部定义match_mode，确保在异常情况下也能引用
        match_mode = self.config.match_mode
        
        try:
            self.logger.info(f"开始搜索歌手 '{self.config.artist_name}' 的歌曲...")
            self.logger.info(f"匹配模式: {match_mode}")
            
            cookies = self._get_cookies()
            all_songs = []
            offset = 0
            
            # 从配置文件获取分页大小
            try:
                from main import config
                page_size = config.artist_download_config.get('search_page_size', 100)
            except ImportError:
                page_size = 100
            
            # 分页搜索，直到获取所有歌曲
            while True:
                # 使用NeteaseAPI类的search_music方法，支持offset参数和搜索类型（1=歌曲搜索）
                search_results = self.api.search_music(self.config.artist_name, cookies, page_size, offset, 1)
                
                # 从搜索结果中提取歌曲列表
                songs_list = search_results.get('songs', [])
                
                if not songs_list or len(songs_list) == 0:
                    break
                
                # 根据匹配模式过滤歌曲
                page_songs = []
                
                for song in songs_list:
                    song_artists = song.get('artists', '')
                    song_name = song.get('name', '未知歌曲')
                    
                    if match_mode == "all":
                        # 返回所有搜索结果，不进行过滤
                        page_songs.append(song)
                        continue
                    
                    elif match_mode == "partial":
                        # 部分匹配：只要歌手名包含搜索关键词即可
                        if self.config.artist_name.lower() in song_artists.lower():
                            page_songs.append(song)
                        else:
                            self.logger.debug(f"跳过非部分匹配歌曲: {song_name} - {song_artists}")
                    
                    elif match_mode == "exact_multi":
                        # 完全匹配但允许多歌手：检查是否包含目标歌手
                        artists_list = song_artists.split('/')
                        if any(artist.strip().lower() == self.config.artist_name.lower() 
                              for artist in artists_list):
                            page_songs.append(song)
                        else:
                            self.logger.debug(f"跳过非完全匹配歌曲: {song_name} - {song_artists}")
                    
                    else:  # exact_single (默认模式)
                        # 完全匹配且单歌手
                        if (song_artists.lower() == self.config.artist_name.lower() and 
                            '/' not in song_artists):
                            page_songs.append(song)
                        else:
                            # 记录跳过原因
                            if '/' in song_artists:
                                self.logger.debug(f"跳过多歌手歌曲: {song_name} - {song_artists}")
                            else:
                                self.logger.debug(f"跳过非完全匹配歌曲: {song_name} - {song_artists}")
                
                # 将当前页的歌曲添加到总列表中
                all_songs.extend(page_songs)
                
                # 如果当前页返回的歌曲数量少于page_size，说明已经获取完所有数据
                if len(songs_list) < page_size:
                    break
                
                # 增加offset，获取下一页
                offset += page_size
                self.logger.info(f"已获取 {len(all_songs)} 首歌曲，继续获取下一页...")
            
            self.logger.info(f"找到 {len(all_songs)} 首歌手 '{self.config.artist_name}' 的歌曲 (模式: {match_mode})")
            return all_songs
            
        except Exception as e:
            self.logger.error(f"搜索歌手歌曲失败: {e}")
            return []
    
    def download_song(self, song: Dict[str, Any], task_id: str = None) -> SongDownloadResult:
        """下载单首歌曲
        
        Args:
            song: 歌曲信息
            task_id: 任务ID（用于取消检查）
            
        Returns:
            下载结果
        """
        try:
            song_id = song['id']
            song_name = song['name']
            artists = song['artists']
            album = song['album']
            
            self.logger.info(f"开始下载: {song_name} - {artists}")
            
            # 检查任务是否已被取消
            if task_id:
                from task_manager import task_manager, TaskStatus
                task_info = task_manager.get_task(task_id)
                if task_info and task_info.status == TaskStatus.CANCELLED:
                    self.logger.info(f"任务 {task_id} 已被取消，停止下载歌曲: {song_name}")
                    return SongDownloadResult(
                        song_id=song_id,
                        name=song_name,
                        artists=artists,
                        status='cancelled',
                        error_message='任务已被用户取消'
                    )
            
            # 下载歌曲文件
            download_result = self.downloader.download_music_file(song_id, self.config.quality, task_id=task_id)
            
            if download_result.success:
                # 获取歌词信息（从download_result中获取，避免重复API调用）
                lyric_text = ""
                if self.config.include_lyric and download_result.music_info:
                    lyric_text = download_result.music_info.lyric or ""
                    if download_result.music_info.tlyric:
                        if lyric_text:
                            lyric_text += "\n\n" + download_result.music_info.tlyric
                        else:
                            lyric_text = download_result.music_info.tlyric
                
                return SongDownloadResult(
                    song_id=song_id,
                    name=song_name,
                    artists=artists,
                    album=album,
                    status='success',
                    file_path=download_result.file_path,
                    file_size=download_result.file_size,
                    lyric=lyric_text
                )
            else:
                return SongDownloadResult(
                    song_id=song_id,
                    name=song_name,
                    artists=artists,
                    album=album,
                    status='failed',
                    error_message=download_result.error_message
                )
                
        except Exception as e:
            self.logger.error(f"下载歌曲异常: {song.get('name', '未知歌曲')} - {e}")
            return SongDownloadResult(
                song_id=song.get('id', 0),
                name=song.get('name', '未知歌曲'),
                artists=song.get('artists', '未知艺术家'),
                album=song.get('album', '未知专辑'),
                status='failed',
                error_message=str(e)
            )
    
    def download_artist_songs(self) -> Dict[str, Any]:
        """批量下载歌手的歌曲"""
        # 搜索歌手的歌曲
        artist_songs = self.search_artist_songs()
        
        if not artist_songs:
            return {
                'success': False,
                'error': f"未找到歌手 '{self.config.artist_name}' 的歌曲"
            }
        
        # 批量下载
        download_results = []
        total_count = len(artist_songs)
        success_count = 0
        failed_count = 0
        skipped_count = 0
        
        self.logger.info(f"开始批量下载 {total_count} 首歌曲...")
        start_time = time.time()
        
        for i, song in enumerate(artist_songs, 1):
            self.logger.info(f"进度: {i}/{total_count}")
            
            # 检查歌曲是否已下载（使用数据库检查）
            song_id = song['id']
            song_name = song['name']
            artists = song['artists']
            album = song.get('album', '未知专辑')
            
            # 使用数据库检查歌曲是否已下载
            if self.db.song_exists(song_id):
                # 从数据库获取歌曲信息
                db_song = self.db.get_song_info(song_id)
                if db_song and db_song.status == 'success':
                    skipped_count += 1
                    self.logger.info(f"⏭️  跳过已下载: {song_name} - 数据库记录存在")
                    
                    # 创建跳过结果
                    result = SongDownloadResult(
                        song_id=song_id,
                        name=song_name,
                        artists=artists,
                        album=album,
                        status='skipped',
                        file_path=db_song.file_path,
                        file_size=db_song.file_size
                    )
                    download_results.append(result)
                    continue
            
            # 歌曲未下载或下载失败，正常下载
            result = self.download_song(song)
            download_results.append(result)
            
            # 记录下载结果到数据库
            if result.status == 'success':
                success_count += 1
                self.logger.info(f"✅ 下载成功: {result.name}")
                
                # 记录成功下载到数据库
                song_info = {
                    'song_id': song_id,
                    'song_name': song_name,
                    'artists': artists,
                    'album': album,
                    'file_path': result.file_path,
                    'file_size': result.file_size,
                    'quality': self.config.quality,
                    'status': 'success'
                }
                self.db.add_song(song_info)
                
            elif result.status == 'failed':
                failed_count += 1
                self.logger.error(f"❌ 下载失败: {result.name} - {result.error_message}")
                
                # 记录失败下载到数据库
                song_info = {
                    'song_id': song_id,
                    'song_name': song_name,
                    'artists': artists,
                    'album': album,
                    'file_path': '',
                    'file_size': 0,
                    'quality': self.config.quality,
                    'status': 'failed'
                }
                self.db.add_song(song_info)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 构建结果
        result_data = {
            'success': True,
            'artist_name': self.config.artist_name,
            'total_songs': total_count,
            'success_count': success_count,
            'failed_count': failed_count,
            'total_time_seconds': round(total_time, 2),
            'average_time_per_song': round(total_time / total_count, 2) if total_count > 0 else 0,
            'download_results': [result.__dict__ for result in download_results],
            'summary': {
                'success_rate': f"{(success_count/total_count)*100:.1f}%" if total_count > 0 else "0%",
                'total_file_size': sum(r.file_size for r in download_results if r.status == 'success'),
                'total_file_size_formatted': self._format_file_size(
                    sum(r.file_size for r in download_results if r.status == 'success')
                )
            }
        }
        
        # 保存结果到JSON文件 - 保存到artist_downloads目录
        result_dir = self.download_path.parent  # artist_downloads目录
        result_dir.mkdir(exist_ok=True, parents=True)  # 确保目录存在
        result_file = result_dir / f"{self.config.artist_name}_download_result.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"批量下载完成!")
        self.logger.info(f"总计: {total_count} 首歌曲")
        self.logger.info(f"成功: {success_count} 首")
        self.logger.info(f"失败: {failed_count} 首")
        self.logger.info(f"成功率: {result_data['summary']['success_rate']}")
        self.logger.info(f"总文件大小: {result_data['summary']['total_file_size_formatted']}")
        self.logger.info(f"总耗时: {total_time:.2f} 秒")
        self.logger.info(f"结果已保存到: {result_file}")
        
        return result_data


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python artist_downloader.py <歌手名称> [音质] [数量限制] [匹配模式] [下载目录]")
        print("示例: python artist_downloader.py \"周深\" lossless 50 exact_single")
        print("示例: python artist_downloader.py \"周深\" lossless 50 exact_single my_music")
        print("支持的音质: standard, exhigh, lossless, hires, sky, jyeffect, jymaster")
        print("支持的匹配模式:")
        print("  exact_single - 完全匹配且单歌手 (默认)")
        print("  exact_multi  - 完全匹配但允许多歌手")
        print("  partial      - 部分匹配 (包含搜索关键词)")
        print("  all          - 返回所有搜索结果")
        sys.exit(1)
    
    artist_name = sys.argv[1]
    quality = sys.argv[2] if len(sys.argv) > 2 else "lossless"
    limit = int(sys.argv[3]) if len(sys.argv) > 3 else 50
    match_mode = sys.argv[4] if len(sys.argv) > 4 else "exact_single"
    download_dir = sys.argv[5] if len(sys.argv) > 5 else "artist_downloads"
    
    # 验证匹配模式
    valid_modes = ["exact_single", "exact_multi", "partial", "all"]
    if match_mode not in valid_modes:
        print(f"错误: 不支持的匹配模式 '{match_mode}'")
        print(f"支持的匹配模式: {', '.join(valid_modes)}")
        sys.exit(1)
    
    # 创建配置
    config = ArtistDownloadConfig(
        artist_name=artist_name,
        quality=quality,
        limit=limit,
        match_mode=match_mode,
        download_dir=download_dir
    )
    
    # 创建下载器并执行
    downloader = ArtistDownloader(config)
    result = downloader.download_artist_songs()
    
    if result['success']:
        print(f"\n🎉 批量下载完成!")
        print(f"歌手: {result['artist_name']}")
        print(f"总计: {result['total_songs']} 首歌曲")
        print(f"成功: {result['success_count']} 首")
        print(f"失败: {result['failed_count']} 首")
        print(f"成功率: {result['summary']['success_rate']}")
        print(f"总文件大小: {result['summary']['total_file_size_formatted']}")
        print(f"总耗时: {result['total_time_seconds']} 秒")
    else:
        print(f"❌ 下载失败: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
