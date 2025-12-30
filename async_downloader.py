"""
异步下载任务函数
为任务管理器提供异步下载功能
"""

import asyncio
import time
from typing import Dict, List, Any
from task_manager import task_manager, TaskStatus
from music_downloader import MusicDownloader
from playlist_downloader import PlaylistDownloader
from artist_downloader import ArtistDownloader
from download_db import DownloadDatabase
import logging


logger = logging.getLogger('async_downloader')


async def async_download_music(music_id: str, quality: str = "lossless", **kwargs) -> Dict[str, Any]:
    """异步下载单首音乐
    
    Args:
        music_id: 音乐ID
        quality: 音质等级
        **kwargs: 其他参数
        
    Returns:
        下载结果
    """
    task_id = kwargs.get('task_id', 'unknown')
    
    try:
        logger.info(f"开始异步下载音乐: {music_id}, 音质: {quality}")
        
        # 创建下载器
        downloader = MusicDownloader()
        
        # 使用异步下载方法
        download_result = await downloader.download_music_file_async(music_id, quality)
        
        # 更新任务进度
        task_manager.update_task_progress(task_id, 100.0, 1, 1)
        
        result = {
            'success': download_result.success,
            'music_id': music_id,
            'file_path': download_result.file_path if download_result.success else None,
            'file_size': download_result.file_size if download_result.success else 0,
            'error_message': download_result.error_message if not download_result.success else None
        }
        
        logger.info(f"异步下载音乐完成: {music_id}, 结果: {'成功' if download_result.success else '失败'}")
        return result
        
    except Exception as e:
        logger.error(f"异步下载音乐异常: {music_id}, 错误: {e}")
        task_manager.update_task_progress(task_id, 100.0, 1, 1)
        return {
            'success': False,
            'music_id': music_id,
            'error_message': str(e)
        }


def sync_download_playlist(playlist_id: str, quality: str = "lossless", 
                          include_lyric: bool = True, max_concurrent: int = 3,
                          selected_songs: List[str] = None, **kwargs) -> Dict[str, Any]:
    """同步下载歌单（在后台线程中执行）
    
    Args:
        playlist_id: 歌单ID
        quality: 音质等级
        include_lyric: 是否包含歌词
        max_concurrent: 最大并发数
        selected_songs: 选中的歌曲ID列表
        **kwargs: 其他参数
        
    Returns:
        下载结果
    """
    task_id = kwargs.get('task_id', 'unknown')
    
    try:
        logger.info(f"开始下载歌单: {playlist_id}, 音质: {quality}")
        logger.info(f"任务ID: {task_id}")
        logger.info(f"选中的歌曲: {selected_songs}")
        
        # 检查任务是否已被取消
        task_info = task_manager.get_task(task_id)
        if task_info and task_info.status == TaskStatus.CANCELLED:
            logger.info(f"任务 {task_id} 已被取消，停止下载歌单")
            return {
                'success': False,
                'playlist_id': playlist_id,
                'error_message': '任务已被用户取消'
            }
        
        # 创建下载配置
        from playlist_downloader import PlaylistDownloadConfig
        import sys
        import os
        # 获取当前工作目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 导入配置
        sys.path.insert(0, current_dir)
        from main import config as api_config
        
        # 使用配置文件中的歌单下载路径
        playlist_sub_dir = api_config.playlist_download_config.get('sub_dir')
        download_base_dir = api_config.downloads_dir
        playlist_download_dir = os.path.join(download_base_dir, playlist_sub_dir) if playlist_sub_dir else download_base_dir
        
        config = PlaylistDownloadConfig(
            playlist_id=playlist_id,
            quality=quality,
            download_dir=playlist_download_dir,
            include_lyric=include_lyric,
            max_concurrent=max_concurrent,
            selected_songs=selected_songs
        )
        
        # 创建下载器
        downloader = PlaylistDownloader(config)
        
        # 如果有选中的歌曲，使用download_selected_songs方法
        if selected_songs and isinstance(selected_songs, list) and len(selected_songs) > 0:
            logger.info(f"下载选中的 {len(selected_songs)} 首歌曲")
            result = downloader.download_selected_songs(selected_songs, task_id)
        else:
            # 下载整个歌单
            logger.info(f"下载整个歌单")
            result = downloader.download_playlist_songs(task_id)
        
        # 检查任务是否已被取消
        task_info = task_manager.get_task(task_id)
        if task_info and task_info.status == TaskStatus.CANCELLED:
            logger.info(f"任务 {task_id} 已被取消，停止下载歌单")
            return {
                'success': False,
                'playlist_id': playlist_id,
                'error_message': '任务已被用户取消',
                'partial_result': result if result else None
            }
        
        # 只有在任务没有被取消的情况下才设置完成进度
        task_info = task_manager.get_task(task_id)
        if not task_info or task_info.status != TaskStatus.CANCELLED:
            task_manager.update_task_progress(task_id, 100.0, 
                                             result.get('success_count', 0) + result.get('skipped_count', 0),
                                             result.get('total_songs', 0))
        
        logger.info(f"歌单下载完成: {playlist_id}, 结果: {result}")
        return result
        
    except Exception as e:
        import traceback
        logger.error(f"歌单下载异常: {playlist_id}, 错误: {e}")
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        # 只有在任务没有被取消的情况下才设置完成进度
        task_info = task_manager.get_task(task_id)
        if not task_info or task_info.status != TaskStatus.CANCELLED:
            task_manager.update_task_progress(task_id, 100.0, 0, 0)
        return {
            'success': False,
            'playlist_id': playlist_id,
            'error_message': str(e)
        }


def sync_download_artist(artist_name: str, quality: str = "lossless", 
                        limit: int = None, match_mode: str = "exact_single",
                        include_lyric: bool = True, max_concurrent: int = 3, **kwargs) -> Dict[str, Any]:
    """同步下载艺术家歌曲（在后台线程中执行）
    
    Args:
        artist_name: 艺术家名称
        quality: 音质等级
        limit: 限制下载数量
        match_mode: 匹配模式
        include_lyric: 是否包含歌词
        max_concurrent: 最大并发数
        **kwargs: 其他参数
        
    Returns:
        下载结果
    """
    task_id = kwargs.get('task_id', 'unknown')
    
    try:
        logger.info(f"开始下载艺术家歌曲: {artist_name}, 音质: {quality}")
        
        # 检查任务是否已被取消
        task_info = task_manager.get_task(task_id)
        if task_info and task_info.status == TaskStatus.CANCELLED:
            logger.info(f"任务 {task_id} 已被取消，停止下载艺术家歌曲")
            return {
                'success': False,
                'artist_name': artist_name,
                'error_message': '任务已被用户取消'
            }
        
        # 创建下载配置
        from artist_downloader import ArtistDownloadConfig
        import sys
        import os
        # 获取当前工作目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 导入配置
        sys.path.insert(0, current_dir)
        from main import config as api_config
        
        # 使用配置文件中的艺术家下载路径
        artist_sub_dir = api_config.artist_download_config.get('sub_dir')
        download_base_dir = api_config.downloads_dir
        artist_download_dir = os.path.join(download_base_dir, artist_sub_dir) if artist_sub_dir else download_base_dir
        
        config = ArtistDownloadConfig(
            artist_name=artist_name,
            quality=quality,
            limit=limit,
            match_mode=match_mode,
            download_dir=artist_download_dir,
            include_lyric=include_lyric,
            max_concurrent=max_concurrent
        )
        
        # 创建下载器
        downloader = ArtistDownloader(config)
        
        # 搜索艺术家歌曲
        songs = downloader.search_artist_songs()
        total_songs = len(songs)
        
        if not songs:
            logger.error(f"无法找到艺术家歌曲: {artist_name}")
            return {
                'success': False,
                'artist_name': artist_name,
                'error_message': '无法找到艺术家歌曲'
            }
        
        # 如果有限制，只下载前limit首歌曲
        if limit and limit > 0 and total_songs > limit:
            songs = songs[:limit]
            total_songs = limit
        
        logger.info(f"艺术家 {artist_name} 共有 {total_songs} 首歌曲需要下载")
        
        # 批量下载
        download_results = []
        success_count = 0
        failed_count = 0
        skipped_count = 0
        
        for i, song in enumerate(songs):
            # 检查任务是否已被取消
            task_info = task_manager.get_task(task_id)
            if task_info and task_info.status == TaskStatus.CANCELLED:
                logger.info(f"任务 {task_id} 已被取消，停止下载艺术家歌曲")
                return {
                    'success': False,
                    'artist_name': artist_name,
                    'error_message': '任务已被用户取消',
                    'partial_results': download_results
                }
            
            # 更新进度
            progress = (i + 1) / total_songs * 100
            task_manager.update_task_progress(task_id, progress, i + 1, total_songs)
            
            # 下载单首歌曲
            song_result = downloader.download_song(song, task_id=task_id)
            
            if song_result.status == 'success':
                success_count += 1
            elif song_result.status == 'failed':
                failed_count += 1
            else:
                skipped_count += 1
            
            download_results.append({
                'song_id': song_result.song_id,
                'name': song_result.name,
                'artists': song_result.artists,
                'status': song_result.status,
                'file_path': song_result.file_path if hasattr(song_result, 'file_path') else None,
                'error_message': song_result.error_message if hasattr(song_result, 'error_message') else None
            })
            
            logger.info(f"艺术家下载进度: {i+1}/{total_songs}, 成功: {success_count}, 失败: {failed_count}, 跳过: {skipped_count}")
        
        # 只有在任务没有被取消的情况下才设置完成进度
        task_info = task_manager.get_task(task_id)
        if not task_info or task_info.status != TaskStatus.CANCELLED:
            task_manager.update_task_progress(task_id, 100.0, total_songs, total_songs)
        
        result = {
            'success': True,
            'artist_name': artist_name,
            'total_songs': total_songs,
            'success_count': success_count,
            'failed_count': failed_count,
            'skipped_count': skipped_count,
            'download_results': download_results
        }
        
        logger.info(f"艺术家下载完成: {artist_name}, 成功: {success_count}, 失败: {failed_count}, 跳过: {skipped_count}")
        return result
        
    except Exception as e:
        logger.error(f"艺术家下载异常: {artist_name}, 错误: {e}")
        # 只有在任务没有被取消的情况下才设置完成进度
        task_info = task_manager.get_task(task_id)
        if not task_info or task_info.status != TaskStatus.CANCELLED:
            task_manager.update_task_progress(task_id, 100.0, 0, 0)
        return {
            'success': False,
            'artist_name': artist_name,
            'error_message': str(e)
        }


def sync_download_music(music_id: str, quality: str = "lossless", **kwargs) -> Dict[str, Any]:
    """同步下载单首音乐（在后台线程中执行）
    
    Args:
        music_id: 音乐ID
        quality: 音质等级
        **kwargs: 其他参数
        
    Returns:
        下载结果
    """
    task_id = kwargs.get('task_id', 'unknown')
    
    try:
        logger.info(f"开始同步下载音乐: {music_id}, 音质: {quality}")
        
        # 检查任务是否已被取消
        task_info = task_manager.get_task(task_id)
        if task_info and task_info.status == TaskStatus.CANCELLED:
            logger.info(f"任务 {task_id} 已被取消，停止下载音乐")
            return {
                'success': False,
                'music_id': music_id,
                'error_message': '任务已被用户取消'
            }
        
        # 创建下载器
        downloader = MusicDownloader()
        
        # 使用同步下载方法
        download_result = downloader.download_music_file(music_id, quality, task_id=task_id)
        
        # 检查任务是否已被取消
        task_info = task_manager.get_task(task_id)
        if task_info and task_info.status == TaskStatus.CANCELLED:
            logger.info(f"任务 {task_id} 已被取消，停止下载音乐")
            return {
                'success': False,
                'music_id': music_id,
                'error_message': '任务已被用户取消'
            }
        
        # 只有在任务没有被取消的情况下才设置完成进度
        task_info = task_manager.get_task(task_id)
        if not task_info or task_info.status != TaskStatus.CANCELLED:
            task_manager.update_task_progress(task_id, 100.0, 1, 1)
        
        result = {
            'success': download_result.success,
            'music_id': music_id,
            'file_path': download_result.file_path if download_result.success else None,
            'file_size': download_result.file_size if download_result.success else 0,
            'error_message': download_result.error_message if not download_result.success else None
        }
        
        logger.info(f"同步下载音乐完成: {music_id}, 结果: {'成功' if download_result.success else '失败'}")
        return result
        
    except Exception as e:
        logger.error(f"同步下载音乐异常: {music_id}, 错误: {e}")
        # 只有在任务没有被取消的情况下才设置完成进度
        task_info = task_manager.get_task(task_id)
        if not task_info or task_info.status != TaskStatus.CANCELLED:
            task_manager.update_task_progress(task_id, 100.0, 1, 1)
        return {
            'success': False,
            'music_id': music_id,
            'error_message': str(e)
        }


def submit_music_download_task(music_id: str, quality: str = "lossless") -> str:
    """提交音乐下载任务
    
    Args:
        music_id: 音乐ID
        quality: 音质等级
        
    Returns:
        任务ID
    """
    # 获取歌曲名称
    try:
        from music_api import name_v1
        song_info = name_v1(music_id)
        if song_info and 'songs' in song_info and song_info['songs']:
            song_name = song_info['songs'][0].get('name', f'歌曲_{music_id}')
            artist_names = ', '.join([artist['name'] for artist in song_info['songs'][0].get('ar', [])])
            content_name = f"{song_name} - {artist_names}"
        else:
            content_name = f"歌曲_{music_id}"
    except Exception as e:
        logger.warning(f"获取歌曲信息失败: {e}")
        content_name = f"歌曲_{music_id}"
    
    return task_manager.create_task(
        task_type="music_download",
        task_func=sync_download_music,
        music_id=music_id,
        quality=quality,
        content_name=content_name
    )


def submit_playlist_download_task(playlist_id: str, quality: str = "lossless", 
                                 include_lyric: bool = True, max_concurrent: int = 3,
                                 selected_songs: List[str] = None) -> str:
    """提交歌单下载任务
    
    Args:
        playlist_id: 歌单ID
        quality: 音质等级
        include_lyric: 是否包含歌词
        max_concurrent: 最大并发数
        selected_songs: 选中的歌曲ID列表
        
    Returns:
        任务ID
    """
    # 获取歌单名称
    try:
        from music_api import playlist_detail
        playlist_info = playlist_detail(playlist_id, {})
        if playlist_info and 'playlist' in playlist_info:
            playlist_name = playlist_info['playlist'].get('name', f'歌单_{playlist_id}')
            content_name = f"歌单: {playlist_name}"
        else:
            content_name = f"歌单_{playlist_id}"
    except Exception as e:
        logger.warning(f"获取歌单信息失败: {e}")
        content_name = f"歌单_{playlist_id}"
    
    return task_manager.create_task(
        task_type="playlist_download",
        task_func=sync_download_playlist,
        playlist_id=playlist_id,
        quality=quality,
        include_lyric=include_lyric,
        max_concurrent=max_concurrent,
        selected_songs=selected_songs,
        content_name=content_name
    )


def submit_artist_download_task(artist_name: str, quality: str = "lossless", 
                               limit: int = None, match_mode: str = "exact_single",
                               include_lyric: bool = True, max_concurrent: int = 3) -> str:
    """提交艺术家下载任务
    
    Args:
        artist_name: 艺术家名称
        quality: 音质等级
        limit: 限制下载数量
        match_mode: 匹配模式
        include_lyric: 是否包含歌词
        max_concurrent: 最大并发数
        
    Returns:
        任务ID
    """
    # 使用艺术家名称作为内容名称
    content_name = f"艺术家: {artist_name}"
    
    return task_manager.create_task(
        task_type="artist_download",
        task_func=sync_download_artist,
        artist_name=artist_name,
        quality=quality,
        limit=limit,
        match_mode=match_mode,
        include_lyric=include_lyric,
        max_concurrent=max_concurrent,
        content_name=content_name
    )
