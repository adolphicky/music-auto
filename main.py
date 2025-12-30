"""网易云音乐API服务主程序

提供网易云音乐相关API服务，包括：
- 歌曲信息获取
- 音乐搜索
- 歌单和专辑详情
- 音乐下载
- 健康检查
"""

import json
import logging
import sys
import time
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from urllib.parse import quote
from flask import Flask, request, send_file, render_template, Response
from flask_socketio import SocketIO, emit

try:
    from music_api import (
        NeteaseAPI, APIException, QualityLevel,
        url_v1, name_v1, lyric_v1, search_music, 
        playlist_detail, album_detail,
        personalized_playlists, high_quality_playlists, playlist_categories
    )
    from cookie_manager import CookieManager, CookieException
    from music_downloader import MusicDownloader, DownloadException, AudioFormat
    from playlist_downloader import PlaylistDownloader, PlaylistDownloadConfig
    from artist_downloader import ArtistDownloader, ArtistDownloadConfig
    from hot_playlist_fetcher import HotPlaylistFetcher
    from qr_login import QRLoginClient
    from task_manager import task_manager, init_task_manager, shutdown_task_manager
    from async_downloader import (
        submit_music_download_task, 
        submit_playlist_download_task, 
        submit_artist_download_task
    )
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保所有依赖模块存在且可用")
    sys.exit(1)


def load_config(config_file: str = 'config.json') -> Dict[str, Any]:
    """从配置文件加载配置"""
    try:
        config_path = Path(config_file)
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            print(f"配置文件 {config_file} 不存在，使用默认配置")
            return {}
    except Exception as e:
        print(f"加载配置文件失败: {e}，使用默认配置")
        return {}

@dataclass
class APIConfig:
    """API配置类"""
    def __init__(self, config_file: str = 'config.json'):
        # 从配置文件加载设置
        config_data = load_config(config_file)
        
        self.host: str = config_data.get('host', '0.0.0.0')
        self.port: int = config_data.get('port', 5000)
        self.debug: bool = config_data.get('debug', False)
        
        # 从新的配置结构中读取配置
        self.download_config = config_data.get('download', {})
        self.music_download_config = config_data.get('music_download', {})
        self.playlist_download_config = config_data.get('playlist_download', {})
        self.artist_download_config = config_data.get('artist_download', {})
        self.database_config = config_data.get('database', {})
        self.cookie_config = config_data.get('cookie', {})
        self.api_config = config_data.get('api', {})
        self.debug_config = config_data.get('debug_config', {})
        
        # 设置下载目录：优先使用download.base_dir，然后是downloads_dir，最后是默认值
        self.downloads_dir: str = self.download_config.get('base_dir', 
                                 config_data.get('downloads_dir', 'downloads'))
        self.max_file_size: int = config_data.get('max_file_size', 500 * 1024 * 1024)  # 500MB
        self.request_timeout: int = config_data.get('request_timeout', 30)
        self.log_level: str = config_data.get('log_level', 'INFO')
        self.cors_origins: str = config_data.get('cors_origins', '*')


class APIResponse:
    """API响应工具类"""
    
    @staticmethod
    def success(data: Any = None, message: str = 'success', status_code: int = 200, **extra_fields) -> Tuple[Dict[str, Any], int]:
        """成功响应"""
        response = {
            'status': status_code,
            'success': True,
            'message': message
        }
        if data is not None:
            response['data'] = data
        
        # 添加额外字段
        response.update(extra_fields)
        
        return response, status_code
    
    @staticmethod
    def error(message: str, status_code: int = 400, error_code: str = None) -> Tuple[Dict[str, Any], int]:
        """错误响应"""
        response = {
            'status': status_code,
            'success': False,
            'message': message
        }
        if error_code:
            response['error_code'] = error_code
        return response, status_code


class MusicAPIService:
    """音乐API服务类"""
    
    def __init__(self, config: APIConfig):
        self.config = config
        self.logger = self._setup_logger()
        self.cookie_manager = CookieManager()
        self.netease_api = NeteaseAPI()
        self.downloader = MusicDownloader()
        
        # 创建下载目录
        self.downloads_path = Path(config.downloads_dir)
        self.downloads_path.mkdir(exist_ok=True)
        
        self.logger.info(f"音乐API服务初始化完成，下载目录: {self.downloads_path.absolute()}")
    
    def _setup_logger(self) -> logging.Logger:
        """设置日志记录器"""
        logger = logging.getLogger('music_api')
        # 强制设置为INFO级别以显示调试日志
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # 控制台处理器
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
            
            # 文件处理器
            try:
                file_handler = logging.FileHandler('music_api.log', encoding='utf-8')
                file_formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
                )
                file_handler.setFormatter(file_formatter)
                logger.addHandler(file_handler)
            except Exception as e:
                logger.warning(f"无法创建日志文件: {e}")
        
        return logger
    
    def _get_cookies(self) -> Dict[str, str]:
        """获取Cookie"""
        try:
            cookie_str = self.cookie_manager.read_cookie()
            return self.cookie_manager.parse_cookie_string(cookie_str)
        except CookieException as e:
            self.logger.warning(f"获取Cookie失败: {e}")
            return {}
        except Exception as e:
            self.logger.error(f"Cookie处理异常: {e}")
            return {}
    
    def _extract_music_id(self, id_or_url: str) -> str:
        """提取音乐ID"""
        try:
            # 首先确保id_or_url是字符串
            id_or_url = str(id_or_url).strip()
            
            # 处理短链接
            if '163cn.tv' in id_or_url:
                import requests
                response = requests.get(id_or_url, allow_redirects=False, timeout=10)
                id_or_url = response.headers.get('Location', id_or_url)
            
            # 处理网易云链接
            if 'music.163.com' in id_or_url:
                index = id_or_url.find('id=') + 3
                if index > 2:
                    return id_or_url[index:].split('&')[0]
            
            # 直接返回ID
            return id_or_url
            
        except Exception as e:
            self.logger.error(f"提取音乐ID失败: {e}")
            return str(id_or_url).strip()
    
    def _format_file_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes == 0:
            return "0B"
        
        units = ["B", "KB", "MB", "GB", "TB"]
        size = float(size_bytes)
        unit_index = 0
        
        while size >= 1024.0 and unit_index < len(units) - 1:
            size /= 1024.0
            unit_index += 1
        
        return f"{size:.2f}{units[unit_index]}"
    
    def _get_quality_display_name(self, quality: str) -> str:
        """获取音质显示名称"""
        quality_names = {
            'standard': "标准音质",
            'exhigh': "极高音质", 
            'lossless': "无损音质",
            'hires': "Hi-Res音质",
            'sky': "沉浸环绕声",
            'jyeffect': "高清环绕声",
            'jymaster': "超清母带",
            'dolby': "杜比全景声"
        }
        return quality_names.get(quality, f"未知音质({quality})")
    
    def _validate_request_params(self, required_params: Dict[str, Any]) -> Optional[Tuple[Dict[str, Any], int]]:
        """验证请求参数"""
        for param_name, param_value in required_params.items():
            if not param_value:
                return APIResponse.error(f"参数 '{param_name}' 不能为空", 400)
        return None
    
    def _safe_get_request_data(self) -> Dict[str, Any]:
        """安全获取请求数据"""
        try:
            if request.method == 'GET':
                return dict(request.args)
            else:
                # 优先使用JSON数据，然后是表单数据
                json_data = request.get_json(silent=True) or {}
                form_data = dict(request.form)
                # 合并数据，JSON优先
                return {**form_data, **json_data}
        except Exception as e:
            self.logger.error(f"获取请求数据失败: {e}")
            return {}


# 创建Flask应用和服务实例
config = APIConfig()
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
api_service = MusicAPIService(config)
qr_login_client = QRLoginClient()


def send_task_progress_update(task_id):
    """发送任务进度更新到所有订阅的客户端"""
    try:
        api_service.logger.info(f"开始发送任务进度更新: {task_id}")
        task = task_manager.get_task(task_id)
        if task:
            task_info = {
                'task_id': task.task_id,
                'task_type': task.task_type,
                'status': task.status.value,
                'progress': task.progress,
                'total_items': task.total_items,
                'processed_items': task.processed_items,
                'error_message': task.error_message,
                'metadata': task.metadata
            }
            api_service.logger.info(f"准备发送WebSocket消息: {task_info}")
            socketio.emit('task_progress', task_info)
            api_service.logger.info(f"成功发送任务进度更新: {task_id} - {task.progress}%")
        else:
            api_service.logger.warning(f"任务不存在，无法发送进度更新: {task_id}")
    except Exception as e:
        api_service.logger.error(f"发送任务进度更新失败: {task_id}, 错误: {e}")


@app.before_request
def before_request():
    """请求前处理"""
    # 记录请求信息
    api_service.logger.info(
        f"{request.method} {request.path} - IP: {request.remote_addr} - "
        f"User-Agent: {request.headers.get('User-Agent', 'Unknown')}"
    )
    
    # 跳过健康检查和认证相关API的cookie检查
    auth_paths = ['/api/auth/qr-code', '/api/auth/check-login', '/api/auth/save-cookie']
    if request.path in ['/health'] + auth_paths:
        return None
    
    # 检查Cookie状态，如果失效则返回需要重新登录的响应
    if not api_service.cookie_manager.is_cookie_valid():
        api_service.logger.warning("Cookie已失效，需要重新登录")
        return APIResponse.error("Cookie已失效，请重新登录", 401, "COOKIE_EXPIRED")


@app.after_request
def after_request(response: Response) -> Response:
    """请求后处理 - 设置CORS头"""
    response.headers.add('Access-Control-Allow-Origin', config.cors_origins)
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    response.headers.add('Access-Control-Max-Age', '3600')
    
    # 记录响应信息
    api_service.logger.info(f"响应状态: {response.status_code}")
    return response


@app.errorhandler(400)
def handle_bad_request(e):
    """处理400错误"""
    return APIResponse.error("请求参数错误", 400)


@app.errorhandler(404)
def handle_not_found(e):
    """处理404错误"""
    return APIResponse.error("请求的资源不存在", 404)


@app.errorhandler(500)
def handle_internal_error(e):
    """处理500错误"""
    api_service.logger.error(f"服务器内部错误: {e}")
    return APIResponse.error("服务器内部错误", 500)


@app.route('/')
def index() -> Response:
    """首页路由 - 重定向到前端服务器"""
    return Response(
        '<html><body><h1>音乐下载器API服务</h1><p>前端界面请访问: <a href="http://localhost:3000">http://localhost:3000</a></p></body></html>',
        content_type='text/html'
    )


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查API"""
    try:
        # 检查Cookie状态
        cookie_status = api_service.cookie_manager.is_cookie_valid()
        
        health_info = {
            'service': 'running',
            'timestamp': int(time.time()) if 'time' in sys.modules else None,
            'cookie_status': 'valid' if cookie_status else 'invalid',
            'downloads_dir': str(api_service.downloads_path.absolute()),
            'version': '2.0.0'
        }
        
        return APIResponse.success(health_info, "API服务运行正常")
        
    except Exception as e:
        api_service.logger.error(f"健康检查失败: {e}")
        return APIResponse.error(f"健康检查失败: {str(e)}", 500)


@app.route('/api/auth/qr-code', methods=['GET'])
def get_qr_code():
    """获取登录二维码API"""
    try:
        # 记录详细的请求信息
        api_service.logger.info(
            f"二维码生成请求 - 客户端IP: {request.remote_addr}, "
            f"User-Agent: {request.headers.get('User-Agent', 'Unknown')}, "
            f"请求时间: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        api_service.logger.info("开始生成登录二维码...")
        
        # 生成二维码信息
        qr_result = qr_login_client.qr_manager.create_qr_login()
        
        # 记录二维码生成结果
        if qr_result and qr_result.get('success'):
            qr_key = qr_result.get('data', {}).get('qr_key', '未知')
            qr_url = qr_result.get('data', {}).get('qr_url', '未知')
            api_service.logger.info(
                f"二维码生成成功 - QR Key: {qr_key}, "
                f"二维码URL: {qr_url}, "
                f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            # 直接返回create_qr_login的结果
            return APIResponse.success(qr_result, "二维码生成成功")
        else:
            error_msg = qr_result.get('message', '二维码生成失败') if qr_result else '二维码生成失败'
            api_service.logger.error(
                f"二维码生成失败 - 错误信息: {error_msg}, "
                f"失败时间: {time.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            return APIResponse.error(error_msg, 500)
            
    except Exception as e:
        api_service.logger.error(
            f"生成二维码异常 - 异常信息: {e}, "
            f"异常时间: {time.strftime('%Y-%m-%d %H:%M:%S')}, "
            f"堆栈跟踪: {traceback.format_exc()}"
        )
        return APIResponse.error(f"生成二维码异常: {str(e)}", 500)


@app.route('/api/auth/check-login', methods=['POST'])
def check_login_status():
    """检查登录状态API"""
    try:
        data = api_service._safe_get_request_data()
        qr_key = data.get('qr_key')
        
        if not qr_key:
            return APIResponse.error("缺少qr_key参数", 400)
        
        # 检查登录状态
        code, cookies = qr_login_client.qr_manager.check_qr_login(qr_key)
        
        # 转换为前端期望的格式
        response_data = {}
        
        if code == 803:
            # 登录成功
            response_data = {
                'status': 'success',
                'cookie': f"MUSIC_U={cookies.get('MUSIC_U', '')};os=pc;appver=8.9.70;"
            }
        elif code == 801:
            # 等待扫码
            response_data = {'status': 'waiting'}
        elif code == 802:
            # 扫码成功，等待确认
            response_data = {'status': 'confirming'}
        else:
            # 二维码过期或其他错误
            response_data = {'status': 'expired'}
        
        return APIResponse.success(response_data, "登录状态检查完成")
            
    except Exception as e:
        api_service.logger.error(f"检查登录状态异常: {e}\n{traceback.format_exc()}")
        return APIResponse.error(f"检查登录状态异常: {str(e)}", 500)


@app.route('/api/auth/save-cookie', methods=['POST'])
def save_cookie():
    """保存Cookie API"""
    try:
        data = api_service._safe_get_request_data()
        cookie_data = data.get('cookie')
        
        if not cookie_data:
            return APIResponse.error("缺少cookie参数", 400)
        
        # 保存Cookie到文件
        success = api_service.cookie_manager.write_cookie(cookie_data)
        
        if success:
            api_service.logger.info("Cookie保存成功")
            return APIResponse.success({'cookie_status': 'valid'}, "Cookie保存成功")
        else:
            api_service.logger.error("Cookie保存失败")
            return APIResponse.error("Cookie保存失败", 500)
            
    except Exception as e:
        api_service.logger.error(f"保存Cookie异常: {e}\n{traceback.format_exc()}")
        return APIResponse.error(f"保存Cookie异常: {str(e)}", 500)


@app.route('/api/song', methods=['GET', 'POST'])
@app.route('/api/Song_V1', methods=['GET', 'POST'])  # 向后兼容
def get_song_info():
    """获取歌曲信息API"""
    try:
        # 获取请求参数
        data = api_service._safe_get_request_data()
        song_ids = data.get('ids') or data.get('id')
        url = data.get('url')
        level = data.get('level', 'lossless')
        info_type = data.get('type', 'url')
        
        # 参数验证
        if not song_ids and not url:
            return APIResponse.error("必须提供 'ids'、'id' 或 'url' 参数")
        
        # 提取音乐ID
        music_id = api_service._extract_music_id(song_ids or url)
        
        # 验证音质参数
        valid_levels = ['standard', 'exhigh', 'lossless', 'hires', 'sky', 'jyeffect', 'jymaster']
        if level not in valid_levels:
            return APIResponse.error(f"无效的音质参数，支持: {', '.join(valid_levels)}")
        
        # 验证类型参数
        valid_types = ['url', 'name', 'lyric', 'json']
        if info_type not in valid_types:
            return APIResponse.error(f"无效的类型参数，支持: {', '.join(valid_types)}")
        
        cookies = api_service._get_cookies()
        
        # 根据类型获取不同信息
        if info_type == 'url':
            result = url_v1(music_id, level, cookies)
            if result and result.get('data') and len(result['data']) > 0:
                song_data = result['data'][0]
                response_data = {
                    'id': song_data.get('id'),
                    'url': song_data.get('url'),
                    'level': song_data.get('level'),
                    'quality_name': api_service._get_quality_display_name(song_data.get('level', level)),
                    'size': song_data.get('size'),
                    'size_formatted': api_service._format_file_size(song_data.get('size', 0)),
                    'type': song_data.get('type'),
                    'bitrate': song_data.get('br')
                }
                return APIResponse.success(response_data, "获取歌曲URL成功")
            else:
                return APIResponse.error("获取音乐URL失败，可能是版权限制或音质不支持", 404)
        
        elif info_type == 'name':
            result = name_v1(music_id)
            return APIResponse.success(result, "获取歌曲信息成功")
        
        elif info_type == 'lyric':
            result = lyric_v1(music_id, cookies)
            return APIResponse.success(result, "获取歌词成功")
        
        elif info_type == 'json':
            # 获取完整的歌曲信息（用于前端解析）
            song_info = name_v1(music_id)
            url_info = url_v1(music_id, level, cookies)
            lyric_info = lyric_v1(music_id, cookies)
            
            if not song_info or 'songs' not in song_info or not song_info['songs']:
                return APIResponse.error("未找到歌曲信息", 404)
            
            song_data = song_info['songs'][0]
            
            # 构建前端期望的响应格式
            response_data = {
                'id': music_id,
                'name': song_data.get('name', ''),
                'ar_name': ', '.join(artist['name'] for artist in song_data.get('ar', [])),
                'al_name': song_data.get('al', {}).get('name', ''),
                'pic': song_data.get('al', {}).get('picUrl', ''),
                'level': level,
                'lyric': lyric_info.get('lrc', {}).get('lyric', '') if lyric_info else '',
                'tlyric': lyric_info.get('tlyric', {}).get('lyric', '') if lyric_info else ''
            }
            
            # 添加URL和大小信息
            if url_info and url_info.get('data') and len(url_info['data']) > 0:
                url_data = url_info['data'][0]
                response_data.update({
                    'url': url_data.get('url', ''),
                    'size': api_service._format_file_size(url_data.get('size', 0)),
                    'level': url_data.get('level', level)
                })
            else:
                response_data.update({
                    'url': '',
                    'size': '获取失败'
                })
            
            return APIResponse.success(response_data, "获取歌曲信息成功")
        
    except APIException as e:
        api_service.logger.error(f"API调用失败: {e}")
        return APIResponse.error(f"API调用失败: {str(e)}", 500)
    except Exception as e:
        api_service.logger.error(f"获取歌曲信息异常: {e}\n{traceback.format_exc()}")
        return APIResponse.error(f"服务器错误: {str(e)}", 500)


@app.route('/api/search', methods=['GET', 'POST'])
@app.route('/api/Search', methods=['GET', 'POST'])  # 向后兼容
def search_music_api():
    """搜索音乐API"""
    try:
        # 获取请求参数
        data = api_service._safe_get_request_data()
        keyword = data.get('keyword') or data.get('keywords') or data.get('q')
        
        # 安全处理limit参数 - 取消限制，获取所有数据
        limit_param = data.get('limit')
        limit = int(limit_param) if limit_param is not None else 9999  # 设置非常大的默认值获取所有数据
        
        # 安全处理offset参数
        offset_param = data.get('offset')
        offset = int(offset_param) if offset_param is not None else 0
        
        search_type = data.get('type', '1')  # 1-歌曲, 10-专辑, 100-歌手, 1000-歌单
        
        # 参数验证
        validation_error = api_service._validate_request_params({'keyword': keyword})
        if validation_error:
            return validation_error
        
        cookies = api_service._get_cookies()
        search_result = api_service.netease_api.search_music(keyword, cookies, limit, offset, int(search_type))
        
        # 根据搜索类型处理返回数据
        if search_type == '1000':  # 歌单搜索
            # 歌单搜索返回的是歌单列表，但数据结构在'songs'字段中
            playlists = search_result.get('songs', [])
            total_count = search_result.get('total', 0)
            
            # 保存原始数据用于比对
            original_playlists = None
            if playlists and isinstance(playlists, list):
                original_playlists = playlists.copy()
            elif playlists and isinstance(playlists, dict) and 'songs' in playlists:
                original_playlists = playlists['songs'].copy() if isinstance(playlists['songs'], list) else None
            
            # 按播放量从大到小排序
            if playlists and isinstance(playlists, list):
                playlists.sort(key=lambda x: x.get('playCount', 0), reverse=True)
            elif playlists and isinstance(playlists, dict):
                # 如果是字典，尝试提取歌单列表
                api_service.logger.warning("歌单搜索返回的是字典，尝试提取songs字段")
                if 'songs' in playlists:
                    playlists = playlists['songs']
                    if isinstance(playlists, list):
                        playlists.sort(key=lambda x: x.get('playCount', 0), reverse=True)
            
            
            # 返回歌单列表
            return APIResponse.success(playlists, "歌单搜索完成", total=total_count)
            return APIResponse.success(playlists, "歌单搜索完成", total=total_count)
        else:
            # 其他搜索类型（歌曲、专辑、歌手等）
            songs = search_result.get('songs', [])
            total_count = search_result.get('total', 0)
            
            # 添加艺术家字符串（如果需要）
            if songs:
                for song in songs:
                    if 'artists' in song:
                        song['artist_string'] = song['artists']
            
            # 返回歌曲列表
            return APIResponse.success(songs, "搜索完成", total=total_count)
        
    except ValueError as e:
        return APIResponse.error(f"参数格式错误: {str(e)}")
    except Exception as e:
        api_service.logger.error(f"搜索音乐异常: {e}\n{traceback.format_exc()}")
        return APIResponse.error(f"搜索失败: {str(e)}", 500)


@app.route('/api/playlist', methods=['GET', 'POST'])
@app.route('/api/Playlist', methods=['GET', 'POST'])  # 向后兼容
def get_playlist():
    """获取歌单详情API"""
    try:
        # 获取请求参数
        data = api_service._safe_get_request_data()
        playlist_id = data.get('id')
        
        # 参数验证
        validation_error = api_service._validate_request_params({'playlist_id': playlist_id})
        if validation_error:
            return validation_error
        
        cookies = api_service._get_cookies()
        result = playlist_detail(playlist_id, cookies)
        
        # 适配前端期望的响应格式
        # result已经是{'playlist': info}格式，直接返回result
        return APIResponse.success(result, "获取歌单详情成功")
        
    except Exception as e:
        api_service.logger.error(f"获取歌单异常: {e}\n{traceback.format_exc()}")
        return APIResponse.error(f"获取歌单失败: {str(e)}", 500)


@app.route('/api/album', methods=['GET', 'POST'])
@app.route('/api/Album', methods=['GET', 'POST'])  # 向后兼容
def get_album():
    """获取专辑详情API"""
    try:
        # 获取请求参数
        data = api_service._safe_get_request_data()
        album_id = data.get('id')
        
        # 参数验证
        validation_error = api_service._validate_request_params({'album_id': album_id})
        if validation_error:
            return validation_error
        
        cookies = api_service._get_cookies()
        result = album_detail(album_id, cookies)
        
        # 适配前端期望的响应格式
        response_data = {
            'status': 200,
            'album': result
        }
        
        return APIResponse.success(response_data, "获取专辑详情成功")
        
    except Exception as e:
        api_service.logger.error(f"获取专辑异常: {e}\n{traceback.format_exc()}")
        return APIResponse.error(f"获取专辑失败: {str(e)}", 500)


@app.route('/api/download', methods=['GET', 'POST'])
@app.route('/api/Download', methods=['GET', 'POST'])  # 向后兼容
def download_music_api():
    """下载音乐API - 支持同步和异步下载"""
    try:
        # 获取请求参数
        data = api_service._safe_get_request_data()
        music_id = data.get('id')
        quality = data.get('quality', 'lossless')
        return_format = data.get('format', 'file')  # file 或 json
        # 处理async参数，支持布尔值和字符串值
        async_param = data.get('async', 'false')
        if isinstance(async_param, bool):
            async_mode = async_param
        else:
            async_mode = str(async_param).lower() == 'true'  # 是否异步下载
        
        # 参数验证
        validation_error = api_service._validate_request_params({'music_id': music_id})
        if validation_error:
            return validation_error
        
        # 验证音质参数
        valid_qualities = ['standard', 'exhigh', 'lossless', 'hires', 'sky', 'jyeffect', 'jymaster']
        if quality not in valid_qualities:
            return APIResponse.error(f"无效的音质参数，支持: {', '.join(valid_qualities)}")
        
        # 验证返回格式
        if return_format not in ['file', 'json']:
            return APIResponse.error("返回格式只支持 'file' 或 'json'")
        
        music_id = api_service._extract_music_id(music_id)
        
        # 如果是异步模式，提交任务并返回任务ID
        if async_mode:
            task_id = submit_music_download_task(music_id, quality)
            return APIResponse.success(
                {'task_id': task_id, 'async': True}, 
                "异步下载任务已提交，请使用任务ID查询进度"
            )
        
        # 同步下载模式（保持原有逻辑）
        cookies = api_service._get_cookies()
        
        # 获取音乐基本信息
        song_info = name_v1(music_id)
        if not song_info or 'songs' not in song_info or not song_info['songs']:
            return APIResponse.error("未找到音乐信息", 404)
        
        # 获取音乐下载链接
        url_info = url_v1(music_id, quality, cookies)
        if not url_info or 'data' not in url_info or not url_info['data'] or not url_info['data'][0].get('url'):
            return APIResponse.error("无法获取音乐下载链接，可能是版权限制或音质不支持", 404)
        
        # 构建音乐信息
        song_data = song_info['songs'][0]
        url_data = url_info['data'][0]
        
        music_info = {
            'id': music_id,
            'name': song_data['name'],
            'artist_string': ', '.join(artist['name'] for artist in song_data['ar']),
            'album': song_data['al']['name'],
            'pic_url': song_data['al']['picUrl'],
            'file_type': url_data['type'],
            'file_size': url_data['size'],
            'duration': song_data.get('dt', 0),
            'download_url': url_data['url']
        }
        
        # 提取歌手名称并清理用于目录名
        artist_names = [artist['name'] for artist in song_data['ar']]
        primary_artist = artist_names[0] if artist_names else 'Unknown'
        safe_artist_name = ''.join(c for c in primary_artist if c not in r'<>:"/\|?*').strip(' .') or 'Unknown'
        
        # 创建专用的下载器，使用正确的目录结构
        from music_downloader import MusicDownloader
        music_sub_dir = api_service.config.music_download_config.get('sub_dir')
        music_download_dir = api_service.downloads_path / music_sub_dir if music_sub_dir else api_service.downloads_path
        
        # 创建下载器，设置create_artist_dir=True以创建歌手目录
        downloader = MusicDownloader(
            download_dir=str(music_download_dir),
            create_artist_dir=True
        )
        
        # 使用专用下载器下载
        try:
            download_result = downloader.download_music_file(music_id, quality)
            
            if not download_result.success:
                return APIResponse.error(f"下载失败: {download_result.error_message}", 500)
            
            file_path = Path(download_result.file_path)
            filename = file_path.name  # 从文件路径获取文件名
            api_service.logger.info(f"下载完成: {filename}")
            
        except DownloadException as e:
            api_service.logger.error(f"下载异常: {e}")
            return APIResponse.error(f"下载失败: {str(e)}", 500)
        
        # 根据返回格式返回结果
        if return_format == 'json':
            response_data = {
                'music_id': music_id,
                'name': music_info['name'],
                'artist': music_info['artist_string'],
                'album': music_info['album'],
                'quality': quality,
                'quality_name': api_service._get_quality_display_name(quality),
                'file_type': music_info['file_type'],
                'file_size': music_info['file_size'],
                'file_size_formatted': api_service._format_file_size(music_info['file_size']),
                'file_path': str(file_path.absolute()),
                'filename': filename,
                'duration': music_info['duration']
            }
            return APIResponse.success(response_data, "下载完成")
        else:
            # 返回文件下载
            if not file_path.exists():
                return APIResponse.error("文件不存在", 404)
            
            try:
                response = send_file(
                    str(file_path),
                    as_attachment=True,
                    download_name=filename,
                    mimetype=f"audio/{music_info['file_type']}"
                )
                response.headers['X-Download-Message'] = 'Download completed successfully'
                response.headers['X-Download-Filename'] = quote(filename, safe='')
                return response
            except Exception as e:
                api_service.logger.error(f"发送文件失败: {e}")
                return APIResponse.error(f"文件发送失败: {str(e)}", 500)
            
    except Exception as e:
        api_service.logger.error(f"下载音乐异常: {e}\n{traceback.format_exc()}")
        return APIResponse.error(f"下载异常: {str(e)}", 500)


@app.route('/api/playlist/download', methods=['POST'])
def download_playlist():
    """歌单批量下载API - 支持同步和异步下载"""
    try:
        # 获取请求参数
        data = api_service._safe_get_request_data()
        playlist_id = data.get('playlist_id')
        quality = data.get('quality', 'lossless')
        # 处理include_lyric参数，支持字符串和布尔值
        include_lyric_param = data.get('include_lyric', 'true')
        if isinstance(include_lyric_param, bool):
            include_lyric = include_lyric_param
        elif isinstance(include_lyric_param, str):
            include_lyric = include_lyric_param.lower() == 'true'
        else:
            include_lyric = True
        max_concurrent = int(data.get('max_concurrent', 3))
        selected_songs = data.get('selected_songs')  # 选中的歌曲ID列表
        # 处理async参数，支持布尔值和字符串值
        async_param = data.get('async', 'false')
        if isinstance(async_param, bool):
            async_mode = async_param
        else:
            async_mode = str(async_param).lower() == 'true'  # 是否异步下载
        
        # 参数验证
        validation_error = api_service._validate_request_params({'playlist_id': playlist_id})
        if validation_error:
            return validation_error
        
        # 验证音质参数
        valid_qualities = ['standard', 'exhigh', 'lossless', 'hires', 'sky', 'jyeffect', 'jymaster']
        if quality not in valid_qualities:
            return APIResponse.error(f"无效的音质参数，支持: {', '.join(valid_qualities)}")
        
        # 如果是异步模式，提交任务并返回任务ID
        if async_mode:
            task_id = submit_playlist_download_task(
                playlist_id=playlist_id,
                quality=quality,
                include_lyric=include_lyric,
                max_concurrent=max_concurrent,
                selected_songs=selected_songs
            )
            return APIResponse.success(
                {'task_id': task_id, 'async': True}, 
                "异步歌单下载任务已提交，请使用任务ID查询进度"
            )
        
        # 同步下载模式（保持原有逻辑）
        # 创建下载配置
        playlist_sub_dir = api_service.config.playlist_download_config.get('sub_dir')
        if playlist_sub_dir:
            playlist_download_dir = api_service.downloads_path / playlist_sub_dir
        else:
            playlist_download_dir = api_service.downloads_path
        playlist_download_dir.mkdir(exist_ok=True, parents=True)
        
        config = PlaylistDownloadConfig(
            playlist_id=playlist_id,
            quality=quality,
            download_dir=str(playlist_download_dir),
            include_lyric=include_lyric,
            max_concurrent=max_concurrent,
            selected_songs=selected_songs  # 添加选中的歌曲ID列表
        )
        
        # 创建下载器并执行
        downloader = PlaylistDownloader(config)
        
        # 根据是否有选中的歌曲决定下载方式
        if selected_songs and isinstance(selected_songs, list) and len(selected_songs) > 0:
            result = downloader.download_selected_songs(selected_songs)
        else:
            result = downloader.download_playlist_songs()
        
        return APIResponse.success(result, "歌单批量下载完成")
        
    except Exception as e:
        api_service.logger.error(f"歌单批量下载异常: {e}\n{traceback.format_exc()}")
        return APIResponse.error(f"歌单批量下载失败: {str(e)}", 500)


@app.route('/api/artist/download', methods=['POST'])
def download_artist_songs():
    """歌手歌曲批量下载API - 支持同步和异步下载"""
    try:
        # 获取请求参数
        data = api_service._safe_get_request_data()
        artist_name = data.get('artist_name')
        quality = data.get('quality', 'lossless')
        # 取消默认限制，设置为None让下载器自动获取所有歌曲
        limit_param = data.get('limit')
        limit = int(limit_param) if limit_param is not None else None
        match_mode = data.get('match_mode', 'exact_single')
        
        # 处理include_lyric参数，支持字符串和布尔值
        include_lyric_param = data.get('include_lyric', 'true')
        if isinstance(include_lyric_param, bool):
            include_lyric = include_lyric_param
        elif isinstance(include_lyric_param, str):
            include_lyric = include_lyric_param.lower() == 'true'
        else:
            include_lyric = True
            
        max_concurrent = int(data.get('max_concurrent', 3))
        # 处理async参数，支持布尔值和字符串值
        async_param = data.get('async', 'false')
        if isinstance(async_param, bool):
            async_mode = async_param
        else:
            async_mode = str(async_param).lower() == 'true'  # 是否异步下载
        
        # 参数验证
        validation_error = api_service._validate_request_params({'artist_name': artist_name})
        if validation_error:
            return validation_error
        
        # 验证音质参数
        valid_qualities = ['standard', 'exhigh', 'lossless', 'hires', 'sky', 'jyeffect', 'jymaster']
        if quality not in valid_qualities:
            return APIResponse.error(f"无效的音质参数，支持: {', '.join(valid_qualities)}")
        
        # 验证匹配模式
        valid_modes = ['exact_single', 'exact_multi', 'partial', 'all']
        if match_mode not in valid_modes:
            return APIResponse.error(f"无效的匹配模式，支持: {', '.join(valid_modes)}")
        
        # 如果是异步模式，提交任务并返回任务ID
        if async_mode:
            task_id = submit_artist_download_task(
                artist_name=artist_name,
                quality=quality,
                limit=limit,
                match_mode=match_mode,
                include_lyric=include_lyric,
                max_concurrent=max_concurrent
            )
            return APIResponse.success(
                {'task_id': task_id, 'async': True}, 
                "异步艺术家下载任务已提交，请使用任务ID查询进度"
            )
        
        # 同步下载模式（保持原有逻辑）
        # 创建下载配置
        artist_sub_dir = api_service.config.artist_download_config.get('sub_dir')
        if artist_sub_dir:
            artist_download_dir = api_service.downloads_path / artist_sub_dir
        else:
            artist_download_dir = api_service.downloads_path
        artist_download_dir.mkdir(exist_ok=True, parents=True)
        
        config = ArtistDownloadConfig(
            artist_name=artist_name,
            quality=quality,
            limit=limit,  # 设置为None时，下载器会自动获取所有歌曲
            match_mode=match_mode,
            download_dir=str(artist_download_dir),
            include_lyric=include_lyric,
            max_concurrent=max_concurrent
        )
        
        # 创建下载器并执行
        downloader = ArtistDownloader(config)
        result = downloader.download_artist_songs()
        
        return APIResponse.success(result, "歌手歌曲批量下载完成")
        
    except Exception as e:
        api_service.logger.error(f"歌手歌曲批量下载异常: {e}\n{traceback.format_exc()}")
        return APIResponse.error(f"歌手歌曲批量下载失败: {str(e)}", 500)


@app.route('/api/hot/playlists', methods=['GET', 'POST'])
def get_hot_playlists():
    """获取热门歌单API"""
    try:
        # 获取请求参数
        data = api_service._safe_get_request_data()
        playlist_type = data.get('type', 'personalized')  # personalized, high_quality, categories
        category = data.get('category', '全部')
        limit_param = data.get('limit')
        # 设置limit默认值为9999，获取更多歌单数据
        limit = int(limit_param) if limit_param is not None else 9999
        
        # 验证类型参数
        valid_types = ['personalized', 'high_quality', 'categories']
        if playlist_type not in valid_types:
            return APIResponse.error(f"无效的类型参数，支持: {', '.join(valid_types)}")
        
        # 创建获取器
        fetcher = HotPlaylistFetcher()
        
        # 根据类型获取数据
        if playlist_type == 'personalized':
            playlists = fetcher.get_personalized_playlists(limit)
        elif playlist_type == 'high_quality':
            playlists = fetcher.get_high_quality_playlists(category, limit)
        else:  # categories
            # 使用新的分类歌单API，支持按分类获取歌单
            playlists = fetcher.get_category_playlists(category, limit)
        
        # 按播放量从大到小排序（对网易云API原始数据进行排序）
        if playlists and isinstance(playlists, list):
            playlists.sort(key=lambda x: x.get('playCount', 0), reverse=True)
        elif playlists and isinstance(playlists, dict):
            # 如果是字典，尝试提取歌单列表
            if 'playlists' in playlists:
                playlists = playlists['playlists']
                if isinstance(playlists, list):
                    playlists.sort(key=lambda x: x.get('playCount', 0), reverse=True)
        
        # 歌单去重逻辑（基于歌单ID）
        if playlists and isinstance(playlists, list):
            seen_ids = set()
            unique_playlists = []
            for playlist in playlists:
                playlist_id = playlist.get('id')
                if playlist_id and playlist_id not in seen_ids:
                    seen_ids.add(playlist_id)
                    unique_playlists.append(playlist)
            playlists = unique_playlists
        
        return APIResponse.success(playlists, "获取热门歌单成功")
        
    except Exception as e:
        api_service.logger.error(f"获取热门歌单异常: {e}\n{traceback.format_exc()}")
        return APIResponse.error(f"获取热门歌单失败: {str(e)}", 500)


@app.route('/api/tasks', methods=['GET'])
def get_all_tasks():
    """获取所有任务信息API"""
    try:
        tasks = task_manager.get_all_tasks()
        
        # 转换为前端友好的格式
        task_list = []
        for task in tasks:
            task_list.append({
                'task_id': task.task_id,
                'task_type': task.task_type,
                'status': task.status.value,
                'created_at': task.created_at,
                'started_at': task.started_at,
                'completed_at': task.completed_at,
                'progress': task.progress,
                'total_items': task.total_items,
                'processed_items': task.processed_items,
                'error_message': task.error_message,
                'metadata': task.metadata
            })
        
        return APIResponse.success({'tasks': task_list}, "获取任务列表成功")
        
    except Exception as e:
        api_service.logger.error(f"获取任务列表异常: {e}")
        return APIResponse.error(f"获取任务列表失败: {str(e)}", 500)


@app.route('/api/tasks/<task_id>', methods=['GET'])
def get_task_info(task_id):
    """获取单个任务信息API"""
    try:
        task = task_manager.get_task(task_id)
        
        if not task:
            return APIResponse.error("任务不存在", 404)
        
        task_info = {
            'task_id': task.task_id,
            'task_type': task.task_type,
            'status': task.status.value,
            'created_at': task.created_at,
            'started_at': task.started_at,
            'completed_at': task.completed_at,
            'progress': task.progress,
            'total_items': task.total_items,
            'processed_items': task.processed_items,
            'error_message': task.error_message,
            'result': task.result,
            'metadata': task.metadata
        }
        
        return APIResponse.success(task_info, "获取任务信息成功")
        
    except Exception as e:
        api_service.logger.error(f"获取任务信息异常: {e}")
        return APIResponse.error(f"获取任务信息失败: {str(e)}", 500)


@app.route('/api/tasks/<task_id>/cancel', methods=['POST'])
def cancel_task(task_id):
    """取消任务API"""
    try:
        success = task_manager.cancel_task(task_id)
        
        if success:
            return APIResponse.success({'cancelled': True}, "任务取消成功")
        else:
            return APIResponse.error("无法取消任务，任务可能已完成或不存在", 400)
        
    except Exception as e:
        api_service.logger.error(f"取消任务异常: {e}")
        return APIResponse.error(f"取消任务失败: {str(e)}", 500)

@app.route('/api/tasks/clear-cancelled', methods=['POST'])
def clear_cancelled_tasks():
    """清理已取消的任务API"""
    try:
        result = task_manager.clear_cancelled_tasks()
        
        if result['success']:
            return APIResponse.success(
                result, 
                f"已成功清理 {result['cleared_count']} 个已取消的任务"
            )
        else:
            return APIResponse.error(
                f"清理已取消任务失败: {result.get('error_message', '未知错误')}", 
                500
            )
        
    except Exception as e:
        api_service.logger.error(f"清理已取消任务异常: {e}")
        return APIResponse.error(f"清理已取消任务失败: {str(e)}", 500)


@app.route('/api/info', methods=['GET'])
def api_info():
    """API信息接口"""
    try:
        info = {
            'name': '网易云音乐API服务',
            'version': '2.0.0',
            'description': '提供网易云音乐相关API服务',
            'endpoints': {
                '/health': 'GET - 健康检查',
                '/song': 'GET/POST - 获取歌曲信息',
                '/search': 'GET/POST - 搜索音乐',
                '/playlist': 'GET/POST - 获取歌单详情',
                '/album': 'GET/POST - 获取专辑详情',
                '/download': 'GET/POST - 下载音乐',
                '/playlist/download': 'POST - 歌单批量下载',
                '/artist/download': 'POST - 歌手歌曲批量下载',
                '/hot/playlists': 'GET/POST - 热门歌单发现',
                '/api/tasks': 'GET - 获取任务列表',
                '/api/tasks/<task_id>': 'GET - 获取任务详情',
                '/api/tasks/<task_id>/cancel': 'POST - 取消任务',
                '/api/info': 'GET - API信息'
            },
            'supported_qualities': [
                'standard', 'exhigh', 'lossless', 
                'hires', 'sky', 'jyeffect', 'jymaster'
            ],
            'config': {
                'downloads_dir': str(api_service.downloads_path.absolute()),
                'max_file_size': f"{config.max_file_size // (1024*1024)}MB",
                'request_timeout': f"{config.request_timeout}s"
            },
            'async_support': True,
            'websocket_support': True
        }
        
        return APIResponse.success(info, "API信息获取成功")
        
    except Exception as e:
        api_service.logger.error(f"获取API信息异常: {e}")
        return APIResponse.error(f"获取API信息失败: {str(e)}", 500)


@socketio.on('connect')
def handle_connect():
    """WebSocket连接事件"""
    api_service.logger.info(f"WebSocket客户端已连接: {request.sid}")
    emit('connected', {'message': 'WebSocket连接成功', 'timestamp': time.time()})


@socketio.on('disconnect')
def handle_disconnect():
    """WebSocket断开连接事件"""
    api_service.logger.info(f"WebSocket客户端已断开: {request.sid}")


@socketio.on('subscribe_task')
def handle_subscribe_task(data):
    """订阅任务进度更新"""
    task_id = data.get('task_id')
    if task_id:
        api_service.logger.info(f"客户端订阅任务进度: {task_id}")
        # 立即发送当前任务状态
        task = task_manager.get_task(task_id)
        if task:
            task_info = {
                'task_id': task.task_id,
                'task_type': task.task_type,
                'status': task.status.value,
                'progress': task.progress,
                'total_items': task.total_items,
                'processed_items': task.processed_items,
                'error_message': task.error_message,
                'metadata': task.metadata
            }
            emit('task_progress', task_info, room=request.sid)
        else:
            emit('task_error', {'message': f'任务 {task_id} 不存在'}, room=request.sid)





async def start_api_server_async():
    """异步启动API服务器"""
    try:
        print("🚀 网易云音乐API服务启动中...")
        print(f"📡 服务地址: http://{config.host}:{config.port}")
        print(f"📁 下载目录: {api_service.downloads_path.absolute()}")
        print(f"📋 日志级别: {config.log_level}")
        print(f"⏰ 启动时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 初始化任务管理器
        print("🔄 初始化任务管理器...")
        await init_task_manager()
        
        # 注册WebSocket推送回调函数
        from task_manager import task_manager
        task_manager.set_progress_callback(send_task_progress_update)
        print("✅ 任务管理器初始化完成，WebSocket回调已注册")
        
        print("🌟 服务已就绪，等待请求...\n")
        
        # 启动SocketIO服务器（支持WebSocket）
        print(f"🚀 启动SocketIO服务器...")
        # 在后台线程中运行SocketIO服务器，避免阻塞事件循环
        import threading
        import asyncio
        def run_socketio():
            socketio.run(
                app,
                host=config.host,
                port=config.port,
                debug=config.debug,
                allow_unsafe_werkzeug=True,
                use_reloader=False
            )
        
        socketio_thread = threading.Thread(target=run_socketio, daemon=True)
        socketio_thread.start()
        
        # 保持主线程运行，让任务管理器继续工作
        while True:
            await asyncio.sleep(1)
        
    except KeyboardInterrupt:
        print("\n👋 服务停止中...")
        # 关闭任务管理器
        await shutdown_task_manager()
        print("✅ 任务管理器已关闭")
        print("👋 服务已停止")
    except Exception as e:
        api_service.logger.error(f"启动服务失败: {e}")
        print(f"❌ 启动失败: {e}")
        # 关闭任务管理器
        await shutdown_task_manager()
        sys.exit(1)

def start_api_server():
    """启动API服务器（兼容性包装）"""
    import asyncio
    asyncio.run(start_api_server_async())


if __name__ == '__main__':
    start_api_server()
