"""歌单歌曲批量下载器

提供解析歌单并批量下载其中所有歌曲的功能，包含歌词和元数据。
"""

import os
import sys
import time
import json
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    from music_api import NeteaseAPI, APIException, playlist_detail, lyric_v1
    from cookie_manager import CookieManager, CookieException
    from music_downloader import MusicDownloader, DownloadException, DownloadResult
    from download_db import DownloadDatabase
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保所有依赖模块存在且可用")
    sys.exit(1)


@dataclass
class PlaylistDownloadConfig:
    """歌单下载配置"""
    playlist_id: str
    quality: str = None
    download_dir: str = None
    include_lyric: bool = True
    max_concurrent: int = None
    selected_songs: list = None  # 选中的歌曲ID列表
    
    def __post_init__(self):
        """初始化后处理，从配置文件读取默认值"""
        # 从配置文件读取默认配置
        try:
            from main import config
            # 使用统一下载目录配置
            base_dir = config.download_config.get('base_dir', 'downloads')
            playlist_sub_dir = config.playlist_download_config.get('sub_dir')
            
            # 设置默认值
            if self.quality is None:
                self.quality = config.playlist_download_config.get('default_quality', 'lossless')
            if self.download_dir is None:
                # 如果sub_dir为空，直接使用base_dir；否则组合路径
                if playlist_sub_dir:
                    self.download_dir = str(Path(base_dir) / playlist_sub_dir)
                else:
                    self.download_dir = base_dir
            if self.max_concurrent is None:
                self.max_concurrent = config.playlist_download_config.get('max_concurrent', 3)
            if self.include_lyric is True:
                self.include_lyric = config.playlist_download_config.get('include_lyric', True)
            if self.selected_songs is None:
                self.selected_songs = []  # 默认空列表
        except ImportError:
            # 如果无法导入config，使用默认值
            if self.quality is None:
                self.quality = "lossless"
            if self.download_dir is None:
                self.download_dir = "downloads/playlists"
            if self.max_concurrent is None:
                self.max_concurrent = 3
            if self.selected_songs is None:
                self.selected_songs = []  # 默认空列表


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


class PlaylistDownloader:
    """歌单歌曲批量下载器"""
    
    def __init__(self, config: PlaylistDownloadConfig):
        self.config = config
        
        # 先设置日志记录器
        self.logger = self._setup_logger()
        
        # 初始化依赖（必须在_get_playlist_name之前初始化cookie_manager）
        self.cookie_manager = CookieManager()
        self.api = NeteaseAPI()
        
        # 然后获取歌单信息以获取歌单名称
        self.playlist_name = self._get_playlist_name()
        
        # 清理歌单名称，移除文件名中的非法字符
        sanitized_name = self._sanitize_filename(self.playlist_name)
        
        # 初始化下载目录（按歌单名创建子目录）
        self.download_path = Path(config.download_dir) / sanitized_name
        self.download_path.mkdir(exist_ok=True, parents=True)
        
        # 初始化其他依赖
        self.downloader = MusicDownloader(
            download_dir=str(self.download_path),
            max_concurrent=config.max_concurrent,
            create_artist_dir=False  # 歌单下载模式下不创建歌手目录
        )
        
        # 初始化数据库
        self.db = DownloadDatabase()
        
        self.logger.info(f"歌单下载器初始化完成，歌单名称: {self.playlist_name}")
        self.logger.info(f"下载目录: {self.download_path.absolute()}")
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger('playlist_downloader')
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
            
            # 文件处理器 - 保存到程序根目录
            current_dir = Path(__file__).parent
            log_file = current_dir / f"playlist_download_{int(time.time())}.log"
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
    
    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名，移除非法字符和URL链接字符串"""
        # 首先检查是否是URL链接，如果是则提取歌单ID并获取真实名称
        if 'music.163.com' in filename or 'playlist?id=' in filename:
            # 尝试从URL中提取歌单ID
            playlist_id = self._extract_playlist_id(filename)
            if playlist_id != filename:  # 如果成功提取到ID
                # 获取真实的歌单名称
                try:
                    cookies = self._get_cookies()
                    playlist_detail_result = playlist_detail(int(playlist_id), cookies)
                    if playlist_detail_result and 'playlist' in playlist_detail_result:
                        playlist_info = playlist_detail_result['playlist']
                        real_name = playlist_info.get('name', '未知歌单')
                        filename = real_name
                except Exception:
                    # 如果获取真实名称失败，使用通用名称
                    filename = "未知歌单"
        
        # 移除Windows和Linux文件名中的非法字符
        illegal_chars = r'[<>:"/\\|?*\x00-\x1f]'
        sanitized = re.sub(illegal_chars, '_', filename)
        
        # 移除开头和结尾的空格和点
        sanitized = sanitized.strip().strip('.')
        
        # 如果清理后为空，使用默认名称
        if not sanitized:
            sanitized = "歌单下载"
        
        # 限制文件名长度
        if len(sanitized) > 100:
            sanitized = sanitized[:100]
        
        return sanitized
    
    def _get_playlist_name(self) -> str:
        """获取歌单名称"""
        try:
            playlist_id = self._extract_playlist_id(self.config.playlist_id)
            cookies = self._get_cookies()
            playlist_detail_result = playlist_detail(int(playlist_id), cookies)
            
            if playlist_detail_result and 'playlist' in playlist_detail_result:
                playlist_info = playlist_detail_result['playlist']
                playlist_name = playlist_info.get('name', '未知歌单')
                return playlist_name
            else:
                return '未知歌单'
        except Exception as e:
            self.logger.warning(f"获取歌单名称失败: {e}")
            return '未知歌单'
    
    def _extract_playlist_id(self, playlist_input) -> str:
        """从输入中提取歌单ID"""
        # 确保输入是字符串
        playlist_input = str(playlist_input)
        
        # 如果是纯数字，直接返回
        if playlist_input.isdigit():
            return playlist_input
        
        # 尝试从URL中提取歌单ID
        patterns = [
            r'playlist\?id=(\d+)',
            r'playlist/(\d+)',
            r'playlist/(\d+)/',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, playlist_input)
            if match:
                return match.group(1)
        
        # 如果无法提取，返回原始输入
        self.logger.warning(f"无法从输入中提取歌单ID，使用原始输入: {playlist_input}")
        return playlist_input
    
    def get_playlist_songs(self) -> List[Dict[str, Any]]:
        """获取歌单中的所有歌曲"""
        try:
            playlist_id = self._extract_playlist_id(self.config.playlist_id)
            self.logger.info(f"开始解析歌单 ID: {playlist_id}")
            
            cookies = self._get_cookies()
            self.logger.info(f"使用Cookie: {cookies}")
            
            playlist_detail_result = playlist_detail(int(playlist_id), cookies)
            
            if not playlist_detail_result or 'playlist' not in playlist_detail_result:
                self.logger.error(f"无法获取歌单详情，请检查歌单ID是否正确")
                self.logger.error(f"API响应: {playlist_detail_result}")
                return []
            
            playlist_info = playlist_detail_result['playlist']
            playlist_name = playlist_info.get('name', '未知歌单')
            track_count = playlist_info.get('trackCount', 0)
            tracks = playlist_info.get('tracks', [])
            
            self.logger.info(f"歌单名称: {playlist_name}")
            self.logger.info(f"歌曲数量: {track_count}")
            self.logger.info(f"实际获取到: {len(tracks)} 首歌曲")
            
            # 格式化歌曲信息
            songs = []
            for track in tracks:
                song_info = {
                    'id': track['id'],
                    'name': track['name'],
                    'artists': '/'.join([artist['name'] for artist in track.get('ar', [])]),
                    'album': track.get('al', {}).get('name', '未知专辑'),
                    'duration': track.get('dt', 0),
                    'album_pic': track.get('al', {}).get('picUrl', '')
                }
                songs.append(song_info)
            
            return songs
            
        except Exception as e:
            import traceback
            self.logger.error(f"获取歌单歌曲失败: {e}")
            self.logger.error(f"详细错误信息: {traceback.format_exc()}")
            return []
    
    def download_song(self, song: Dict[str, Any], task_id: str = None) -> SongDownloadResult:
        """下载单首歌曲
        
        Args:
            song: 歌曲信息
            task_id: 任务ID（用于取消检查）
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
                        album=album,
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
    
    def download_playlist_songs(self, task_id: str = None) -> Dict[str, Any]:
        """批量下载歌单中的歌曲
        
        Args:
            task_id: 任务ID，用于进度更新
        """
        # 导入任务管理器
        from task_manager import task_manager
        
        # 获取歌单歌曲
        playlist_songs = self.get_playlist_songs()
        
        if not playlist_songs:
            return {
                'success': False,
                'error': f"无法获取歌单 {self.config.playlist_id} 的歌曲"
            }
        
        # 批量下载
        download_results = []
        total_count = len(playlist_songs)
        success_count = 0
        failed_count = 0
        skipped_count = 0
        
        self.logger.info(f"开始批量下载 {total_count} 首歌曲...")
        start_time = time.time()
        
        for i, song in enumerate(playlist_songs, 1):
            self.logger.info(f"进度: {i}/{total_count}")
            
            # 更新任务进度
            if task_id:
                progress = (i / total_count) * 100
                task_manager.update_task_progress(task_id, progress, i, total_count)
            
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
                    # 检查文件是否在正确的歌单目录下
                    db_file_path = Path(db_song.file_path)
                    expected_dir = self.download_path
                    
                    # 如果文件不在当前歌单目录下，重新下载到正确目录
                    if db_file_path.parent != expected_dir:
                        self.logger.info(f"文件不在歌单目录下，重新下载: {song_name}")
                        # 继续正常下载流程
                    else:
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
            result = self.download_song(song, task_id=task_id)
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
            'playlist_id': self.config.playlist_id,
            'total_songs': total_count,
            'success_count': success_count,
            'failed_count': failed_count,
            'skipped_count': skipped_count,
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
        
        # 保存结果到JSON文件 - 保存到程序根目录
        current_dir = Path(__file__).parent
        sanitized_name = self._sanitize_filename(self.playlist_name)
        result_file = current_dir / f"{sanitized_name}_selected_download_result.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"选中歌曲下载完成!")
        self.logger.info(f"歌单名称: {self.playlist_name}")
        self.logger.info(f"选中歌曲: {total_count} 首")
        self.logger.info(f"成功: {success_count} 首")
        self.logger.info(f"失败: {failed_count} 首")
        self.logger.info(f"跳过: {skipped_count} 首")
        self.logger.info(f"成功率: {result_data['summary']['success_rate']}")
        self.logger.info(f"总文件大小: {result_data['summary']['total_file_size_formatted']}")
        self.logger.info(f"总耗时: {total_time:.2f} 秒")
        self.logger.info(f"结果已保存到: {result_file}")
        
        return result_data

    def download_selected_songs(self, selected_song_ids: List[int], task_id: str = None) -> Dict[str, Any]:
        """下载选中的歌曲
        
        Args:
            selected_song_ids: 选中的歌曲ID列表
            task_id: 任务ID，用于进度更新
        """
        # 导入任务管理器
        from task_manager import task_manager
        
        # 获取歌单中的所有歌曲
        playlist_songs = self.get_playlist_songs()
        
        if not playlist_songs:
            return {
                'success': False,
                'error': f"无法获取歌单 {self.config.playlist_id} 的歌曲"
            }
        
        # 过滤出选中的歌曲
        selected_songs = []
        for song in playlist_songs:
            if song['id'] in selected_song_ids:
                selected_songs.append(song)
        
        if not selected_songs:
            return {
                'success': False,
                'error': f"未找到选中的歌曲，请检查歌曲ID是否正确"
            }
        
        # 批量下载选中的歌曲
        download_results = []
        total_count = len(selected_songs)
        success_count = 0
        failed_count = 0
        skipped_count = 0
        
        self.logger.info(f"开始批量下载选中的 {total_count} 首歌曲...")
        start_time = time.time()
        
        for i, song in enumerate(selected_songs, 1):
            self.logger.info(f"进度: {i}/{total_count}")
            
            # 更新任务进度
            if task_id:
                progress = (i / total_count) * 100
                task_manager.update_task_progress(task_id, progress, i, total_count)
            
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
                    # 检查文件是否在正确的歌单目录下
                    db_file_path = Path(db_song.file_path)
                    expected_dir = self.download_path
                    
                    # 如果文件不在当前歌单目录下，重新下载到正确目录
                    if db_file_path.parent != expected_dir:
                        self.logger.info(f"文件不在歌单目录下，重新下载: {song_name}")
                        # 继续正常下载流程
                    else:
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
            result = self.download_song(song, task_id=task_id)
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
            'playlist_id': self.config.playlist_id,
            'total_songs': total_count,
            'success_count': success_count,
            'failed_count': failed_count,
            'skipped_count': skipped_count,
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
        
        # 保存结果到JSON文件 - 保存到程序根目录
        current_dir = Path(__file__).parent
        sanitized_name = self._sanitize_filename(self.playlist_name)
        result_file = current_dir / f"{sanitized_name}_selected_download_result.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"选中歌曲下载完成!")
        self.logger.info(f"歌单名称: {self.playlist_name}")
        self.logger.info(f"选中歌曲: {total_count} 首")
        self.logger.info(f"成功: {success_count} 首")
        self.logger.info(f"失败: {failed_count} 首")
        self.logger.info(f"跳过: {skipped_count} 首")
        self.logger.info(f"成功率: {result_data['summary']['success_rate']}")
        self.logger.info(f"总文件大小: {result_data['summary']['total_file_size_formatted']}")
        self.logger.info(f"总耗时: {total_time:.2f} 秒")
        self.logger.info(f"结果已保存到: {result_file}")
        
        return result_data

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python playlist_downloader.py <歌单ID或链接> [音质] [下载目录]")
        print("示例: python playlist_downloader.py \"123456789\" lossless")
        print("示例: python playlist_downloader.py \"https://music.163.com/playlist?id=123456789\" hires my_playlists")
        print("支持的音质: standard, exhigh, lossless, hires, sky, jyeffect, jymaster")
        sys.exit(1)
    
    playlist_input = sys.argv[1]
    quality = sys.argv[2] if len(sys.argv) > 2 else "lossless"
    download_dir = sys.argv[3] if len(sys.argv) > 3 else "playlist_downloads"
    
    # 创建配置
    config = PlaylistDownloadConfig(
        playlist_id=playlist_input,
        quality=quality,
        download_dir=download_dir
    )
    
    # 创建下载器并执行
    downloader = PlaylistDownloader(config)
    result = downloader.download_playlist_songs()
    
    if result['success']:
        print(f"\n🎉 歌单下载完成!")
        print(f"歌单ID: {result['playlist_id']}")
        print(f"总计: {result['total_songs']} 首歌曲")
        print(f"成功: {result['success_count']} 首")
        print(f"失败: {result['failed_count']} 首")
        print(f"跳过: {result['skipped_count']} 首")
        print(f"成功率: {result['summary']['success_rate']}")
        print(f"总文件大小: {result['summary']['total_file_size_formatted']}")
        print(f"总耗时: {result['total_time_seconds']} 秒")
    else:
        print(f"❌ 下载失败: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()