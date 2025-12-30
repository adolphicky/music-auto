"""网易云音乐API模块

提供网易云音乐相关API接口的封装，包括：
- 音乐URL获取
- 歌曲详情获取
- 歌词获取
- 搜索功能
- 歌单和专辑详情
- 二维码登录
"""

import json
import urllib.parse
import time
from random import randrange
from typing import Dict, List, Optional, Tuple, Any
from hashlib import md5
from enum import Enum

import requests
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


class QualityLevel(Enum):
    """音质等级枚举"""
    STANDARD = "standard"      # 标准音质
    EXHIGH = "exhigh"          # 极高音质
    LOSSLESS = "lossless"      # 无损音质
    HIRES = "hires"            # Hi-Res音质
    SKY = "sky"                # 沉浸环绕声
    JYEFFECT = "jyeffect"      # 高清环绕声
    JYMASTER = "jymaster"      # 超清母带
    DOLBY = "dolby"      # 杜比全景声


# 常量定义
class APIConstants:
    """API相关常量"""
    AES_KEY = b"e82ckenh8dichen8"
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Safari/537.36 Chrome/91.0.4472.164 NeteaseMusicDesktop/2.10.2.200154'
    REFERER = 'https://music.163.com/'
    
    # API URLs
    SONG_URL_V1 = "https://interface3.music.163.com/eapi/song/enhance/player/url/v1"
    SONG_DETAIL_V3 = "https://interface3.music.163.com/api/v3/song/detail"
    LYRIC_API = "https://interface3.music.163.com/api/song/lyric"
    SEARCH_API = 'https://music.163.com/api/cloudsearch/pc'
    PLAYLIST_DETAIL_API = 'https://music.163.com/api/v3/playlist/detail'
    ALBUM_DETAIL_API = 'https://music.163.com/api/v1/album/'
    QR_UNIKEY_API = 'https://interface3.music.163.com/eapi/login/qrcode/unikey'
    QR_LOGIN_API = 'https://interface3.music.163.com/eapi/login/qrcode/client/login'
    
    # 热门歌单相关API
    PERSONALIZED_PLAYLIST_API = 'https://music.163.com/api/personalized/playlist'
    PLAYLIST_CATEGORY_API = 'https://music.163.com/api/playlist/catalogue'
    HIGH_QUALITY_PLAYLIST_API = 'https://music.163.com/api/playlist/highquality/list'
    
    # 默认配置
    DEFAULT_CONFIG = {
        "os": "pc",
        "appver": "",
        "osver": "",
        "deviceId": "pyncm!"
    }
    
    DEFAULT_COOKIES = {
        "os": "pc",
        "appver": "",
        "osver": "",
        "deviceId": "pyncm!"
    }


class CryptoUtils:
    """加密工具类"""
    
    @staticmethod
    def hex_digest(data: bytes) -> str:
        """将字节数据转换为十六进制字符串"""
        return "".join([hex(d)[2:].zfill(2) for d in data])
    
    @staticmethod
    def hash_digest(text: str) -> bytes:
        """计算MD5哈希值"""
        return md5(text.encode("utf-8")).digest()
    
    @staticmethod
    def hash_hex_digest(text: str) -> str:
        """计算MD5哈希值并转换为十六进制字符串"""
        return CryptoUtils.hex_digest(CryptoUtils.hash_digest(text))
    
    @staticmethod
    def encrypt_params(url: str, payload: Dict[str, Any]) -> str:
        """加密请求参数"""
        url_path = urllib.parse.urlparse(url).path.replace("/eapi/", "/api/")
        digest = CryptoUtils.hash_hex_digest(f"nobody{url_path}use{json.dumps(payload)}md5forencrypt")
        params = f"{url_path}-36cd479b6b5-{json.dumps(payload)}-36cd479b6b5-{digest}"
        
        # AES加密
        padder = padding.PKCS7(algorithms.AES(APIConstants.AES_KEY).block_size).padder()
        padded_data = padder.update(params.encode()) + padder.finalize()
        cipher = Cipher(algorithms.AES(APIConstants.AES_KEY), modes.ECB())
        encryptor = cipher.encryptor()
        enc = encryptor.update(padded_data) + encryptor.finalize()
        
        return CryptoUtils.hex_digest(enc)


class HTTPClient:
    """HTTP客户端类"""
    
    @staticmethod
    def post_request(url: str, params: str, cookies: Dict[str, str]) -> str:
        """发送POST请求并返回文本响应"""
        headers = {
            'User-Agent': APIConstants.USER_AGENT,
            'Referer': APIConstants.REFERER,
        }
        
        request_cookies = APIConstants.DEFAULT_COOKIES.copy()
        request_cookies.update(cookies)
        
        try:
            response = requests.post(url, headers=headers, cookies=request_cookies, 
                                   data={"params": params}, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            raise APIException(f"HTTP请求失败: {e}")
    
    @staticmethod
    def post_request_full(url: str, params: str, cookies: Dict[str, str]) -> requests.Response:
        """发送POST请求并返回完整响应对象"""
        headers = {
            'User-Agent': APIConstants.USER_AGENT,
            'Referer': APIConstants.REFERER,
        }
        
        request_cookies = APIConstants.DEFAULT_COOKIES.copy()
        request_cookies.update(cookies)
        
        try:
            response = requests.post(url, headers=headers, cookies=request_cookies, 
                                   data={"params": params}, timeout=30)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            raise APIException(f"HTTP请求失败: {e}")


class APIException(Exception):
    """API异常类"""
    pass


class NeteaseAPI:
    """网易云音乐API主类"""
    
    def __init__(self):
        self.http_client = HTTPClient()
        self.crypto_utils = CryptoUtils()
    
    def get_song_url(self, song_id: int, quality: str, cookies: Dict[str, str]) -> Dict[str, Any]:
        """获取歌曲播放URL
        
        Args:
            song_id: 歌曲ID
            quality: 音质等级 (standard, exhigh, lossless, hires, sky, jyeffect, jymaster)
            cookies: 用户cookies
            
        Returns:
            包含歌曲URL信息的字典
            
        Raises:
            APIException: API调用失败时抛出
        """
        try:
            config = APIConstants.DEFAULT_CONFIG.copy()
            config["requestId"] = str(randrange(20000000, 30000000))
            
            payload = {
                'ids': [song_id],
                'level': quality,
                'encodeType': 'flac',
                'header': json.dumps(config),
            }
            
            if quality == 'sky':
                payload['immerseType'] = 'c51'
            
            params = self.crypto_utils.encrypt_params(APIConstants.SONG_URL_V1, payload)
            response_text = self.http_client.post_request(APIConstants.SONG_URL_V1, params, cookies)
            
            result = json.loads(response_text)
            if result.get('code') != 200:
                raise APIException(f"获取歌曲URL失败: {result.get('message', '未知错误')}")
            
            return result
        except (json.JSONDecodeError, KeyError) as e:
            raise APIException(f"解析响应数据失败: {e}")
    
    def get_song_detail(self, song_id: int) -> Dict[str, Any]:
        """获取歌曲详细信息
        
        Args:
            song_id: 歌曲ID
            
        Returns:
            包含歌曲详细信息的字典
            
        Raises:
            APIException: API调用失败时抛出
        """
        try:
            data = {'c': json.dumps([{"id": song_id, "v": 0}])}
            response = requests.post(APIConstants.SONG_DETAIL_V3, data=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            if result.get('code') != 200:
                raise APIException(f"获取歌曲详情失败: {result.get('message', '未知错误')}")
            
            return result
        except requests.RequestException as e:
            raise APIException(f"获取歌曲详情请求失败: {e}")
        except json.JSONDecodeError as e:
            raise APIException(f"解析歌曲详情响应失败: {e}")
    
    def get_lyric(self, song_id: int, cookies: Dict[str, str]) -> Dict[str, Any]:
        """获取歌词信息
        
        Args:
            song_id: 歌曲ID
            cookies: 用户cookies
            
        Returns:
            包含歌词信息的字典
            
        Raises:
            APIException: API调用失败时抛出
        """
        try:
            data = {
                'id': song_id, 
                'cp': 'false', 
                'tv': '0', 
                'lv': '0', 
                'rv': '0', 
                'kv': '0', 
                'yv': '0', 
                'ytv': '0', 
                'yrv': '0'
            }
            
            headers = {
                'User-Agent': APIConstants.USER_AGENT,
                'Referer': APIConstants.REFERER
            }
            
            response = requests.post(APIConstants.LYRIC_API, data=data, 
                                   headers=headers, cookies=cookies, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            if result.get('code') != 200:
                raise APIException(f"获取歌词失败: {result.get('message', '未知错误')}")
            
            return result
        except requests.RequestException as e:
            raise APIException(f"获取歌词请求失败: {e}")
        except json.JSONDecodeError as e:
            raise APIException(f"解析歌词响应失败: {e}")
    
    def search_music(self, keywords: str, cookies: Dict[str, str], limit: int = 10, offset: int = 0, search_type: int = 1) -> Dict[str, Any]:
        """搜索音乐
        
        Args:
            keywords: 搜索关键词
            cookies: 用户cookies
            limit: 返回数量限制
            offset: 偏移量，用于分页
            search_type: 搜索类型 (1-歌曲, 10-专辑, 100-歌手, 1000-歌单)
            
        Returns:
            包含歌曲列表和总数信息的字典
            
        Raises:
            APIException: API调用失败时抛出
        """
        try:
            data = {'s': keywords, 'type': search_type, 'limit': limit, 'offset': offset}
            headers = {
                'User-Agent': APIConstants.USER_AGENT,
                'Referer': APIConstants.REFERER
            }
            
            response = requests.post(APIConstants.SEARCH_API, data=data, 
                                   headers=headers, cookies=cookies, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            if result.get('code') != 200:
                raise APIException(f"搜索失败: {result.get('message', '未知错误')}")
            
            songs = []
            total_count = 0
            
            # 根据搜索类型处理不同的返回数据结构
            if search_type == 100:  # 歌手搜索
                # 歌手搜索返回艺术家信息，需要进一步处理
                artists = result.get('result', {}).get('artists', [])
                if artists:
                    # 这里可以返回艺术家信息，或者尝试获取该歌手的歌曲
                    # 目前先返回空列表，因为歌手搜索不直接返回歌曲
                    # 移除logger引用，因为NeteaseAPI类没有logger属性
                    return {'songs': [], 'total': 0}
                else:
                    return {'songs': [], 'total': 0}
            else:  # 歌曲、专辑、歌单搜索
                # 尝试从API响应中获取总数信息
                search_result = result.get('result', {})
                
                # 处理歌单搜索的特殊情况
                if search_type == 1000:  # 歌单搜索
                    playlists = []
                    total_count = search_result.get('playlistCount', len(search_result.get('playlists', [])))
                    
                    for item in search_result.get('playlists', []):
                        playlist_info = {
                            'id': item['id'],
                            'name': item['name'],
                            'coverImgUrl': item.get('coverImgUrl', ''),
                            'picUrl': item.get('coverImgUrl', ''),
                            'creator': item.get('creator', {}).get('nickname', '未知创建者'),
                            'copywriter': item.get('copywriter', ''),
                            'playCount': item.get('playCount', 0),
                            'trackCount': item.get('trackCount', 0),
                            'tags': item.get('tags', []),
                            'description': item.get('description', '')
                        }
                        playlists.append(playlist_info)
                    
                    return {'songs': playlists, 'total': total_count}
                else:  # 歌曲、专辑搜索
                    total_count = search_result.get('songCount', len(search_result.get('songs', [])))
                    
                    for item in search_result.get('songs', []):
                        song_info = {
                            'id': item['id'],
                            'name': item['name'],
                            'artists': '/'.join(artist['name'] for artist in item['ar']),
                            'artist_string': '/'.join(artist['name'] for artist in item['ar']),
                            'ar': item.get('ar', []),  # 保留原始艺术家数组
                            'album': {
                                'name': item['al']['name'],
                                'picUrl': item['al']['picUrl']
                            },
                            'al': item.get('al', {}),  # 保留原始专辑信息
                            'picUrl': item['al']['picUrl'],
                            'duration': item.get('dt', item.get('duration', 0)),  # 添加时长字段
                            'dt': item.get('dt', 0)  # 保留原始时长字段
                        }
                        songs.append(song_info)
            
            return {'songs': songs, 'total': total_count}
        except requests.RequestException as e:
            raise APIException(f"搜索请求失败: {e}")
        except (json.JSONDecodeError, KeyError) as e:
            raise APIException(f"解析搜索响应失败: {e}")
    
    def get_playlist_detail(self, playlist_id: int, cookies: Dict[str, str]) -> Dict[str, Any]:
        """获取歌单详情
        
        Args:
            playlist_id: 歌单ID
            cookies: 用户cookies
            
        Returns:
            歌单详情信息
            
        Raises:
            APIException: API调用失败时抛出
        """
        try:
            # 使用更现代的API参数格式
            import time
            timestamp = int(time.time() * 1000)
            
            data = {
                'id': playlist_id,
                'n': 100000,  # 获取所有歌曲
                's': 0,       # 起始位置
                't': timestamp
            }
            
            headers = {
                'User-Agent': APIConstants.USER_AGENT,
                'Referer': APIConstants.REFERER,
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            response = requests.post(APIConstants.PLAYLIST_DETAIL_API, data=data, 
                                   headers=headers, cookies=cookies, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            if result.get('code') != 200:
                # 如果v3版本失败，尝试使用更兼容的版本
                fallback_api = 'https://music.163.com/api/playlist/detail'
                fallback_response = requests.post(fallback_api, data={'id': playlist_id}, 
                                                headers=headers, cookies=cookies, timeout=30)
                fallback_response.raise_for_status()
                result = fallback_response.json()
                
                if result.get('code') != 200:
                    raise APIException(f"获取歌单详情失败: {result.get('message', '未知错误')}")
            
            playlist = result.get('playlist', {})
            info = {
                'id': playlist.get('id'),
                'name': playlist.get('name'),
                'coverImgUrl': playlist.get('coverImgUrl'),
                'creator': playlist.get('creator', {}).get('nickname', ''),
                'trackCount': playlist.get('trackCount'),
                'description': playlist.get('description', ''),
                'tracks': []
            }
            
            # 获取所有trackIds并分批获取详细信息
            track_ids = [str(t['id']) for t in playlist.get('trackIds', [])]
            for i in range(0, len(track_ids), 100):
                batch_ids = track_ids[i:i+100]
                song_data = {'c': json.dumps([{'id': int(sid), 'v': 0} for sid in batch_ids])}
                
                song_resp = requests.post(APIConstants.SONG_DETAIL_V3, data=song_data, 
                                        headers=headers, cookies=cookies, timeout=30)
                song_resp.raise_for_status()
                
                song_result = song_resp.json()
                for song in song_result.get('songs', []):
                    info['tracks'].append({
                        'id': song['id'],
                        'name': song['name'],
                        'ar': song.get('ar', []),  # 歌手数组
                        'al': song.get('al', {}),  # 专辑对象
                        'dt': song.get('dt', 0),   # 时长（毫秒）
                        'picUrl': song['al']['picUrl']
                    })
            
            # 返回包含'playlist'键的字典以保持向后兼容性
            return {'playlist': info}
        except requests.RequestException as e:
            raise APIException(f"获取歌单详情请求失败: {e}")
        except (json.JSONDecodeError, KeyError) as e:
            raise APIException(f"解析歌单详情响应失败: {e}")
    
    def get_album_detail(self, album_id: int, cookies: Dict[str, str]) -> Dict[str, Any]:
        """获取专辑详情
        
        Args:
            album_id: 专辑ID
            cookies: 用户cookies
            
        Returns:
            专辑详情信息
            
        Raises:
            APIException: API调用失败时抛出
        """
        try:
            url = f'{APIConstants.ALBUM_DETAIL_API}{album_id}'
            headers = {
                'User-Agent': APIConstants.USER_AGENT,
                'Referer': APIConstants.REFERER
            }
            
            response = requests.get(url, headers=headers, cookies=cookies, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            if result.get('code') != 200:
                raise APIException(f"获取专辑详情失败: {result.get('message', '未知错误')}")
            
            album = result.get('album', {})
            info = {
                'id': album.get('id'),
                'name': album.get('name'),
                'coverImgUrl': self.get_pic_url(album.get('pic')),
                'artist': album.get('artist', {}).get('name', ''),
                'publishTime': album.get('publishTime'),
                'description': album.get('description', ''),
                'songs': []
            }
            
            for song in result.get('songs', []):
                info['songs'].append({
                    'id': song['id'],
                    'name': song['name'],
                    'artists': '/'.join(artist['name'] for artist in song['ar']),
                    'album': song['al']['name'],
                    'picUrl': self.get_pic_url(song['al'].get('pic'))
                })
            
            return info
        except requests.RequestException as e:
            raise APIException(f"获取专辑详情请求失败: {e}")
        except (json.JSONDecodeError, KeyError) as e:
            raise APIException(f"解析专辑详情响应失败: {e}")
    
    def netease_encrypt_id(self, id_str: str) -> str:
        """网易云加密图片ID算法
        
        Args:
            id_str: 图片ID字符串
            
        Returns:
            加密后的字符串
        """
        import base64
        import hashlib
        
        magic = list('3go8&$8*3*3h0k(2)2')
        song_id = list(id_str)
        
        for i in range(len(song_id)):
            song_id[i] = chr(ord(song_id[i]) ^ ord(magic[i % len(magic)]))
        
        m = ''.join(song_id)
        md5_bytes = hashlib.md5(m.encode('utf-8')).digest()
        result = base64.b64encode(md5_bytes).decode('utf-8')
        result = result.replace('/', '_').replace('+', '-')
        
        return result
    
    def get_pic_url(self, pic_id: Optional[int], size: int = 300) -> str:
        """获取网易云加密歌曲/专辑封面直链
        
        Args:
            pic_id: 封面ID
            size: 图片尺寸
            
        Returns:
            图片URL
        """
        if pic_id is None:
            return ''
        
        enc_id = self.netease_encrypt_id(str(pic_id))
        return f'https://p3.music.126.net/{enc_id}/{pic_id}.jpg?param={size}y{size}'

    def get_personalized_playlists(self, cookies: Dict[str, str], limit: int = 20) -> List[Dict[str, Any]]:
        """获取个性化推荐歌单
        
        Args:
            cookies: 用户cookies
            limit: 返回歌单数量限制，None表示获取所有数据
            
        Returns:
            推荐歌单列表
            
        Raises:
            APIException: API调用失败时抛出
        """
        try:
            headers = {
                'User-Agent': APIConstants.USER_AGENT,
                'Referer': APIConstants.REFERER
            }
            
            playlists = []
            offset = 0
            page_size = 50  # 每页获取50个歌单
            max_pages = 2  # 最大页数限制，避免无限循环
            
            for page in range(max_pages):
                # 构建参数
                params = {
                    'limit': page_size,
                    'offset': offset
                }
                
                response = requests.get(
                    APIConstants.PERSONALIZED_PLAYLIST_API, 
                    headers=headers, 
                    cookies=cookies, 
                    params=params,
                    timeout=30
                )
                response.raise_for_status()
                
                result = response.json()
                if result.get('code') != 200:
                    raise APIException(f"获取推荐歌单失败: {result.get('message', '未知错误')}")
                
                current_playlists = result.get('result', [])
                if not current_playlists:
                    break  # 没有更多数据
                

                
                for item in current_playlists:
                    playlist_info = {
                        'id': item['id'],
                        'name': item['name'],
                        'coverImgUrl': item['picUrl'],
                        'playCount': item.get('playCount', 0),
                        'trackCount': item.get('trackCount', 0),
                        'creator': item.get('copywriter', ''),
                        'description': item.get('copywriter', ''),  # 使用copywriter作为描述
                        'tags': item.get('tags', []),
                        'url': f'https://music.163.com/playlist?id={item["id"]}'
                    }
                    playlists.append(playlist_info)
                
                # 检查是否达到限制
                if limit is not None and len(playlists) >= limit:
                    playlists = playlists[:limit]  # 截断到指定数量
                    break
                
                # 检查是否还有更多数据
                # 个性化推荐歌单API通常没有total字段，所以使用简单的页数限制
                if len(current_playlists) < page_size:
                    break  # 当前页数据不足，说明没有更多数据
                
                offset += page_size
            

            return playlists
        except requests.RequestException as e:
            raise APIException(f"获取推荐歌单请求失败: {e}")
        except (json.JSONDecodeError, KeyError) as e:
            raise APIException(f"解析推荐歌单响应失败: {e}")

    def get_playlist_categories(self, cookies: Dict[str, str]) -> Dict[str, Any]:
        """获取歌单分类列表
        
        Args:
            cookies: 用户cookies
            
        Returns:
            歌单分类信息
            
        Raises:
            APIException: API调用失败时抛出
        """
        try:
            headers = {
                'User-Agent': APIConstants.USER_AGENT,
                'Referer': APIConstants.REFERER
            }
            
            response = requests.get(
                APIConstants.PLAYLIST_CATEGORY_API, 
                headers=headers, 
                cookies=cookies, 
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            if result.get('code') != 200:
                raise APIException(f"获取歌单分类失败: {result.get('message', '未知错误')}")
            
            categories = {}
            # 新的API结构：categories是字典，key是分类ID，value是分类名称
            for cat_id, cat_name in result.get('categories', {}).items():
                sub_categories = []
                
                # 从sub列表中筛选出属于当前主分类的子分类
                for sub_cat in result.get('sub', []):
                    if sub_cat.get('category') == int(cat_id):
                        sub_categories.append({
                            'id': sub_cat.get('id'),
                            'name': sub_cat.get('name'),
                            'hot': sub_cat.get('hot', False)
                        })
                
                categories[cat_name] = sub_categories
            
            return categories
        except requests.RequestException as e:
            raise APIException(f"获取歌单分类请求失败: {e}")
        except (json.JSONDecodeError, KeyError) as e:
            raise APIException(f"解析歌单分类响应失败: {e}")

    def get_category_playlists(self, cookies: Dict[str, str], category: str = '全部', limit: int = 20) -> List[Dict[str, Any]]:
        """获取分类歌单（按分类获取歌单）
        
        Args:
            cookies: 用户cookies
            category: 歌单分类 (默认: '全部')
            limit: 返回歌单数量限制，None表示获取所有数据
            
        Returns:
            分类歌单列表
            
        Raises:
            APIException: API调用失败时抛出
        """
        try:
            headers = {
                'User-Agent': APIConstants.USER_AGENT,
                'Referer': APIConstants.REFERER
            }
            
            playlists = []
            
            # 如果选择"全部"分类，使用多种方法获取更多数据
            if category == '全部':
                # 方法1：使用搜索API获取更多歌单数据
                playlists.extend(self._get_playlists_by_search(cookies, limit))
                
                # 方法2：如果搜索API获取的数据不足，尝试使用歌单发现API
                if len(playlists) < 1000:
                    print(f"搜索API获取到{len(playlists)}个歌单，尝试使用歌单发现API获取更多数据")
                    try:
                        discover_playlists = self._get_playlists_by_discover(cookies, limit)
                        playlists.extend(discover_playlists)
                        print(f"合并后总共获取到{len(playlists)}个歌单")
                    except Exception as e:
                        print(f"歌单发现API失败: {e}")
                
                # 方法3：如果仍然不足，尝试使用热门歌单API
                if len(playlists) < 1000:
                    print(f"当前获取到{len(playlists)}个歌单，尝试使用热门歌单API")
                    try:
                        hot_playlists = self._get_hot_playlists(cookies, limit)
                        playlists.extend(hot_playlists)
                        print(f"最终合并后总共获取到{len(playlists)}个歌单")
                    except Exception as e:
                        print(f"热门歌单API失败: {e}")
            else:
                # 如果选择具体分类，使用分类搜索获取歌单
                print(f"获取分类 '{category}' 的歌单...")
                playlists.extend(self._get_playlists_by_category(cookies, category, limit))
            
            # 如果指定了限制，截断到指定数量
            if limit is not None and len(playlists) > limit:
                playlists = playlists[:limit]
            
            print(f"分类 '{category}' 总共获取到{len(playlists)}个歌单")
            return playlists
        except Exception as e:
            raise APIException(f"获取分类歌单失败: {e}")
    
    def _get_playlists_by_category(self, cookies: Dict[str, str], category: str, limit: int = 20) -> List[Dict[str, Any]]:
        """按分类获取歌单"""
        playlists = []
        
        headers = {
            'User-Agent': APIConstants.USER_AGENT,
            'Referer': APIConstants.REFERER
        }
        
        # 使用搜索API按分类获取歌单
        offset = 0
        page_size = 50
        max_pages = 20
        
        for page in range(max_pages):
            try:
                search_params = {
                    's': category,  # 使用分类名称作为关键词
                    'type': 1000,   # 歌单搜索
                    'limit': page_size,
                    'offset': offset
                }
                
                search_response = requests.post(
                    APIConstants.SEARCH_API,
                    headers=headers,
                    cookies=cookies,
                    data=search_params,
                    timeout=30
                )
                search_response.raise_for_status()
                
                search_result = search_response.json()
                if search_result.get('code') != 200:
                    print(f"分类 '{category}' 搜索失败: {search_result.get('message', '未知错误')}")
                    break
                
                search_data = search_result.get('result', {})
                current_playlists = search_data.get('playlists', [])
                
                if not current_playlists:
                    break
                
                total = search_data.get('playlistCount', 0)
                print(f"分类 '{category}' 第{page+1}页获取到{len(current_playlists)}个歌单，总数: {total}")
                
                # 添加歌单（网易云接口返回的歌单都是唯一的，不需要去重）
                for item in current_playlists:
                    playlist_info = {
                        'id': item['id'],
                        'name': item['name'],
                        'coverImgUrl': item.get('coverImgUrl', ''),
                        'playCount': item.get('playCount', 0),
                        'trackCount': item.get('trackCount', 0),
                            'creator': item.get('creator', {}).get('nickname', ''),
                            'description': item.get('description', ''),
                            'tags': item.get('tags', []),
                            'url': f'https://music.163.com/playlist?id={item["id"]}'
                        }
                    playlists.append(playlist_info)
                
                print(f"分类 '{category}' 第{page+1}页新增{len(current_playlists)}个歌单，当前总数: {len(playlists)}")
                
                # 检查是否达到限制
                if limit is not None and len(playlists) >= limit:
                    playlists = playlists[:limit]
                    print(f"达到限制{limit}，停止搜索")
                    break
                
                # 检查是否还有更多数据
                if total > 0 and offset + page_size >= total:
                    print(f"分类 '{category}' 已获取完所有数据")
                    break
                
                if len(current_playlists) < page_size:
                    print(f"分类 '{category}' 当前页数据不足，说明没有更多数据")
                    break
                
                offset += page_size
                
            except Exception as e:
                print(f"分类 '{category}' 第{page+1}页失败: {e}")
                break
        
        return playlists
    
    def _get_playlists_by_discover(self, cookies: Dict[str, str], limit: int = 20) -> List[Dict[str, Any]]:
        """使用歌单发现API获取歌单"""
        playlists = []
        
        # 尝试不同的分类和排序方式
        categories = ['全部', '华语', '欧美', '韩语', '日语', '电子', '摇滚', '民谣', '轻音乐']
        orders = ['hot', 'new']  # 热度和最新
        
        headers = {
            'User-Agent': APIConstants.USER_AGENT,
            'Referer': APIConstants.REFERER
        }
        
        for category in categories:
            for order in orders:
                print(f"使用分类 '{category}' 和排序 '{order}' 获取歌单...")
                offset = 0
                page_size = 100  # 增加每页数量
                max_pages = 5    # 减少页数，避免重复
                
                for page in range(max_pages):
                    try:
                        params = {
                            'order': order,
                            'limit': page_size,
                            'offset': offset,
                            'cat': category
                        }
                        
                        response = requests.get(
                            'https://music.163.com/api/discovery/playlist',
                            headers=headers,
                            cookies=cookies,
                            params=params,
                            timeout=30
                        )
                        response.raise_for_status()
                        
                        result = response.json()
                        if result.get('code') != 200:
                            print(f"分类 '{category}' 排序 '{order}' 第{page+1}页失败: {result.get('message', '未知错误')}")
                            break
                        
                        current_playlists = result.get('playlists', [])
                        if not current_playlists:
                            break
                        
                        # 添加歌单（网易云接口返回的歌单都是唯一的，不需要去重）
                        for item in current_playlists:
                            playlist_info = {
                                'id': item['id'],
                                'name': item['name'],
                                'coverImgUrl': item.get('coverImgUrl', ''),
                                'playCount': item.get('playCount', 0),
                                'trackCount': item.get('trackCount', 0),
                                'creator': item.get('creator', {}).get('nickname', ''),
                                'description': item.get('description', ''),
                                'tags': item.get('tags', []),
                                'url': f'https://music.163.com/playlist?id={item["id"]}'
                            }
                            playlists.append(playlist_info)
                        
                        print(f"分类 '{category}' 排序 '{order}' 第{page+1}页获取到{len(current_playlists)}个歌单，当前总数: {len(playlists)}")
                        
                        # 检查是否达到限制
                        if limit is not None and len(playlists) >= limit:
                            playlists = playlists[:limit]
                            print(f"达到限制{limit}，停止获取")
                            return playlists
                        
                        offset += page_size
                        
                    except Exception as e:
                        print(f"分类 '{category}' 排序 '{order}' 第{page+1}页失败: {e}")
                        break
                
                # 如果已经获取到足够数据，提前结束
                if limit is not None and len(playlists) >= limit:
                    break
            # 如果已经获取到足够数据，提前结束
            if limit is not None and len(playlists) >= limit:
                break
        
        print(f"歌单发现API总共获取到{len(playlists)}个歌单")
        return playlists
    
    def _get_hot_playlists(self, cookies: Dict[str, str], limit: int = 20) -> List[Dict[str, Any]]:
        """使用热门歌单API获取歌单"""
        playlists = []
        
        # 尝试不同的分类
        categories = ['全部', '华语', '欧美', '韩语', '日语', '电子', '摇滚', '民谣', '轻音乐']
        
        headers = {
            'User-Agent': APIConstants.USER_AGENT,
            'Referer': APIConstants.REFERER
        }
        
        for category in categories:
            print(f"使用分类 '{category}' 获取热门歌单...")
            offset = 0
            page_size = 100  # 增加每页数量
            max_pages = 5    # 减少页数，避免重复
            
            for page in range(max_pages):
                try:
                    # 使用热门歌单API，添加分类参数
                    params = {
                        'limit': page_size,
                        'offset': offset,
                        'cat': category  # 添加分类参数
                    }
                    
                    response = requests.get(
                        'https://music.163.com/api/top/playlist',
                        headers=headers,
                        cookies=cookies,
                        params=params,
                        timeout=30
                    )
                    response.raise_for_status()
                    
                    result = response.json()
                    if result.get('code') != 200:
                        print(f"分类 '{category}' 第{page+1}页失败: {result.get('message', '未知错误')}")
                        break
                    
                    current_playlists = result.get('playlists', [])
                    if not current_playlists:
                        break
                    
                    # 添加歌单（网易云接口返回的歌单都是唯一的，不需要去重）
                    for item in current_playlists:
                        playlist_info = {
                            'id': item['id'],
                            'name': item['name'],
                            'coverImgUrl': item.get('coverImgUrl', ''),
                            'playCount': item.get('playCount', 0),
                            'trackCount': item.get('trackCount', 0),
                            'creator': item.get('creator', {}).get('nickname', ''),
                            'description': item.get('description', ''),
                            'tags': item.get('tags', []),
                            'url': f'https://music.163.com/playlist?id={item["id"]}'
                        }
                        playlists.append(playlist_info)
                    
                    # 检查是否达到限制
                    if limit is not None and len(playlists) >= limit:
                        playlists = playlists[:limit]
                        return playlists
                    
                    offset += page_size
                    
                except Exception as e:
                    print(f"分类 '{category}' 第{page+1}页失败: {e}")
                    break
            
            # 如果已经获取到足够数据，提前结束
            if limit is not None and len(playlists) >= limit:
                break
        
        print(f"热门歌单API总共获取到{len(playlists)}个歌单")
        return playlists
    
    def _get_playlists_by_search(self, cookies: Dict[str, str], limit: int = 20) -> List[Dict[str, Any]]:
        """使用搜索API获取歌单（备用方案）"""
        try:
            headers = {
                'User-Agent': APIConstants.USER_AGENT,
                'Referer': APIConstants.REFERER
            }
            
            playlists = []
            
            # 尝试不同的搜索关键词来获取更多歌单
            search_keywords = [
                '',  # 空关键词
                '热门', '流行', '经典', '新歌', '华语', '欧美', '日韩',
                '电子', '摇滚', '民谣', '轻音乐', '影视原声', 'ACG'
            ]
            
            for keyword in search_keywords:
                print(f"使用关键词 '{keyword}' 搜索歌单...")
                offset = 0
                page_size = 100  # 增加每页数量
                max_pages = 10   # 减少页数，避免重复
                
                for page in range(max_pages):
                    search_params = {
                        's': keyword,  # 使用关键词
                        'type': 1000,  # 歌单搜索
                        'limit': page_size,
                        'offset': offset
                    }
                    
                    search_response = requests.post(
                        APIConstants.SEARCH_API,
                        headers=headers,
                        cookies=cookies,
                        data=search_params,
                        timeout=30
                    )
                    search_response.raise_for_status()
                    
                    search_result = search_response.json()
                    if search_result.get('code') != 200:
                        print(f"搜索关键词 '{keyword}' 失败: {search_result.get('message', '未知错误')}")
                        break
                    
                    search_data = search_result.get('result', {})
                    current_playlists = search_data.get('playlists', [])
                    
                    if not current_playlists:
                        break
                    
                    total = search_data.get('playlistCount', 0)
                    print(f"关键词 '{keyword}' 第{page+1}页获取到{len(current_playlists)}个歌单，总数: {total}")
                    
                    # 去重添加歌单
                    existing_ids = {p['id'] for p in playlists}
                    new_playlists_count = 0
                    
                    for item in current_playlists:
                        if item['id'] not in existing_ids:
                            playlist_info = {
                                'id': item['id'],
                                'name': item['name'],
                                'coverImgUrl': item.get('coverImgUrl', ''),
                                'playCount': item.get('playCount', 0),
                                'trackCount': item.get('trackCount', 0),
                                'creator': item.get('creator', {}).get('nickname', ''),
                                'description': item.get('description', ''),
                                'tags': item.get('tags', []),
                                'url': f'https://music.163.com/playlist?id={item["id"]}'
                            }
                            playlists.append(playlist_info)
                            existing_ids.add(item['id'])
                            new_playlists_count += 1
                    
                    print(f"关键词 '{keyword}' 第{page+1}页新增{new_playlists_count}个歌单，当前总数: {len(playlists)}")
                    
                    # 检查是否达到限制
                    if limit is not None and len(playlists) >= limit:
                        playlists = playlists[:limit]
                        print(f"达到限制{limit}，停止搜索")
                        return playlists
                    
                    # 检查是否还有更多数据
                    if total > 0 and offset + page_size >= total:
                        print(f"关键词 '{keyword}' 已获取完所有数据")
                        break
                    
                    if len(current_playlists) < page_size:
                        print(f"关键词 '{keyword}' 当前页数据不足，说明没有更多数据")
                        break
                    
                    offset += page_size
                
                # 如果已经获取到足够数据，提前结束
                if limit is not None and len(playlists) >= limit:
                    break
            
            print(f"搜索API总共获取到{len(playlists)}个歌单")
            return playlists
        except Exception as e:
            raise APIException(f"搜索歌单失败: {e}")

    def get_high_quality_playlists(self, cookies: Dict[str, str], cat: str = '全部', limit: int = 20) -> List[Dict[str, Any]]:
        """获取精品歌单
        
        Args:
            cookies: 用户cookies
            cat: 歌单分类 (默认: '全部')
            limit: 返回歌单数量限制，None表示获取所有数据
            
        Returns:
            精品歌单列表
            
        Raises:
            APIException: API调用失败时抛出
        """
        try:
            headers = {
                'User-Agent': APIConstants.USER_AGENT,
                'Referer': APIConstants.REFERER
            }
            
            playlists = []
            offset = 0
            page_size = 50  # 每页获取50个歌单
            max_pages = 20  # 最大页数限制，避免无限循环
            
            for page in range(max_pages):
                # 构建参数 - 尝试使用不同的参数组合
                params = {
                    'cat': cat,
                    'limit': page_size,
                    'offset': offset,
                    'order': 'hot',  # 按热度排序
                    'before': 0,     # 时间戳参数
                }
                
                response = requests.get(
                    APIConstants.HIGH_QUALITY_PLAYLIST_API, 
                    headers=headers, 
                    cookies=cookies, 
                    params=params,
                    timeout=30
                )
                response.raise_for_status()
                
                result = response.json()
                if result.get('code') != 200:
                    raise APIException(f"获取精品歌单失败: {result.get('message', '未知错误')}")
                
                current_playlists = result.get('playlists', [])
                if not current_playlists:
                    break  # 没有更多数据
                
                # 调试信息：打印当前页获取的歌单数量和总数信息
                total = result.get('total', 0)
                print(f"精品歌单第{page+1}页获取到{len(current_playlists)}个歌单，分类: {cat}，总数: {total}")
                
                for item in current_playlists:
                    playlist_info = {
                        'id': item['id'],
                        'name': item['name'],
                        'coverImgUrl': item['coverImgUrl'],
                        'playCount': item.get('playCount', 0),
                        'trackCount': item.get('trackCount', 0),
                        'creator': item.get('creator', {}).get('nickname', ''),
                        'description': item.get('description', ''),
                        'tags': item.get('tags', []),
                        'url': f'https://music.163.com/playlist?id={item["id"]}'
                    }
                    playlists.append(playlist_info)
                
                # 检查是否达到限制
                if limit is not None and len(playlists) >= limit:
                    playlists = playlists[:limit]  # 截断到指定数量
                    break
                
                # 检查是否还有更多数据
                if total > 0 and offset + page_size >= total:
                    print(f"已获取完所有数据，总数: {total}")
                    break  # 有总数信息且已获取完所有数据
                
                # 如果没有总数信息，检查当前页数据是否不足
                if len(current_playlists) < page_size:
                    print("当前页数据不足，说明没有更多数据")
                    break  # 当前页数据不足，说明没有更多数据
                
                offset += page_size
            
            print(f"总共获取到{len(playlists)}个精品歌单，分类: {cat}")
            return playlists
        except requests.RequestException as e:
            raise APIException(f"获取精品歌单请求失败: {e}")
        except (json.JSONDecodeError, KeyError) as e:
            raise APIException(f"解析精品歌单响应失败: {e}")


class QRLoginManager:
    """二维码登录管理器"""
    
    def __init__(self):
        self.http_client = HTTPClient()
        self.crypto_utils = CryptoUtils()
    
    def generate_qr_key(self) -> Optional[str]:
        """生成二维码的key
        
        Returns:
            成功返回unikey，失败返回None
            
        Raises:
            APIException: API调用失败时抛出
        """
        try:
            config = APIConstants.DEFAULT_CONFIG.copy()
            config["requestId"] = str(randrange(20000000, 30000000))
            
            payload = {
                'type': 1,
                'header': json.dumps(config)
            }
            
            params = self.crypto_utils.encrypt_params(APIConstants.QR_UNIKEY_API, payload)
            response = self.http_client.post_request_full(APIConstants.QR_UNIKEY_API, params, {})
            
            result = json.loads(response.text)
            if result.get('code') == 200:
                return result.get('unikey')
            else:
                raise APIException(f"生成二维码key失败: {result.get('message', '未知错误')}")
        except (json.JSONDecodeError, KeyError) as e:
            raise APIException(f"解析二维码key响应失败: {e}")
    
    def create_qr_login(self) -> Dict[str, Any]:
        """创建登录二维码并返回二维码信息
        
        Returns:
            包含二维码信息的字典，格式: {'success': True, 'qr_key': unikey, 'qr_url': base64_image, 'expire_time': 180}
        """
        try:
            import qrcode
            import io
            import base64
            
            unikey = self.generate_qr_key()
            if not unikey:
                return {'success': False, 'message': '生成二维码key失败'}
            
            # 创建二维码
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(f'https://music.163.com/login?codekey={unikey}')
            qr.make(fit=True)
            
            # 生成二维码图片
            img = qr.make_image(fill_color="black", back_color="white")
            
            # 将图片转换为base64
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            img_str = base64.b64encode(buffer.getvalue()).decode()
            qr_url = f"data:image/png;base64,{img_str}"
            
            # 在控制台显示二维码（可选）- 移除TTY依赖
            # qr.print_ascii(tty=True)  # 在Docker环境中会导致"Not a tty"错误
            # print("\n请使用网易云音乐APP扫描上方二维码登录")
            
            return {
                'success': True,
                'qr_key': unikey,
                'qr_url': qr_url,
                'expire_time': 180
            }
        except ImportError:
            return {'success': False, 'message': '请安装qrcode库: pip install qrcode'}
        except Exception as e:
            return {'success': False, 'message': f'创建二维码失败: {e}'}
    
    def check_qr_login(self, unikey: str) -> Tuple[int, Dict[str, str]]:
        """检查二维码登录状态
        
        Args:
            unikey: 二维码key
            
        Returns:
            (登录状态码, cookie字典)
            
        Raises:
            APIException: API调用失败时抛出
        """
        try:
            config = APIConstants.DEFAULT_CONFIG.copy()
            config["requestId"] = str(randrange(20000000, 30000000))
            
            payload = {
                'key': unikey,
                'type': 1,
                'header': json.dumps(config)
            }
            
            params = self.crypto_utils.encrypt_params(APIConstants.QR_LOGIN_API, payload)
            response = self.http_client.post_request_full(APIConstants.QR_LOGIN_API, params, {})
            
            result = json.loads(response.text)
            cookie_dict = {}
            
            if result.get('code') == 803:
                # 登录成功，提取cookie
                all_cookies = response.headers.get('Set-Cookie', '').split(', ')
                for cookie_str in all_cookies:
                    if 'MUSIC_U=' in cookie_str:
                        cookie_dict['MUSIC_U'] = cookie_str.split('MUSIC_U=')[1].split(';')[0]
            
            return result.get('code', -1), cookie_dict
        except (json.JSONDecodeError, KeyError) as e:
            raise APIException(f"解析登录状态响应失败: {e}")
    
    def qr_login(self) -> Optional[str]:
        """完整的二维码登录流程
        
        Returns:
            成功返回cookie字符串，失败返回None
        """
        try:
            qr_result = self.create_qr_login()
            if not qr_result or not qr_result.get('success'):
                return None
            
            unikey = qr_result.get('qr_key')
            if not unikey:
                return None
            
            while True:
                code, cookies = self.check_qr_login(unikey)
                
                if code == 803:
                    print("\n登录成功！")
                    return f"MUSIC_U={cookies['MUSIC_U']};os=pc;appver=8.9.70;"
                elif code == 801:
                    print("\r等待扫码...", end='')
                elif code == 802:
                    print("\r扫码成功，请在手机上确认登录...", end='')
                else:
                    print(f"\n登录失败，错误码：{code}")
                    return None
                
                time.sleep(2)
        except KeyboardInterrupt:
            print("\n用户取消登录")
            return None
        except Exception as e:
            print(f"\n登录过程中发生错误: {e}")
            return None


# 向后兼容的函数接口
def url_v1(song_id: int, level: str, cookies: Dict[str, str]) -> Dict[str, Any]:
    """获取歌曲URL（向后兼容）"""
    api = NeteaseAPI()
    return api.get_song_url(song_id, level, cookies)


def name_v1(song_id: int) -> Dict[str, Any]:
    """获取歌曲详情（向后兼容）"""
    api = NeteaseAPI()
    return api.get_song_detail(song_id)


def lyric_v1(song_id: int, cookies: Dict[str, str]) -> Dict[str, Any]:
    """获取歌词（向后兼容）"""
    api = NeteaseAPI()
    return api.get_lyric(song_id, cookies)


def search_music(keywords: str, cookies: Dict[str, str], limit: int = 10) -> List[Dict[str, Any]]:
    """搜索音乐（向后兼容）"""
    api = NeteaseAPI()
    return api.search_music(keywords, cookies, limit)


def playlist_detail(playlist_id: int, cookies: Dict[str, str]) -> Dict[str, Any]:
    """获取歌单详情（向后兼容）"""
    api = NeteaseAPI()
    return api.get_playlist_detail(playlist_id, cookies)


def album_detail(album_id: int, cookies: Dict[str, str]) -> Dict[str, Any]:
    """获取专辑详情（向后兼容）"""
    api = NeteaseAPI()
    return api.get_album_detail(album_id, cookies)


def get_pic_url(pic_id: Optional[int], size: int = 300) -> str:
    """获取图片URL（向后兼容）"""
    api = NeteaseAPI()
    return api.get_pic_url(pic_id, size)


def qr_login() -> Optional[str]:
    """二维码登录（向后兼容）"""
    manager = QRLoginManager()
    return manager.qr_login()


def personalized_playlists(cookies: Dict[str, str], limit: int = 20) -> List[Dict[str, Any]]:
    """获取个性化推荐歌单（向后兼容）"""
    api = NeteaseAPI()
    return api.get_personalized_playlists(cookies, limit)


def playlist_categories(cookies: Dict[str, str]) -> Dict[str, Any]:
    """获取歌单分类（向后兼容）"""
    api = NeteaseAPI()
    return api.get_playlist_categories(cookies)


def high_quality_playlists(cookies: Dict[str, str], cat: str = '全部', limit: int = 20) -> List[Dict[str, Any]]:
    """获取精品歌单（向后兼容）"""
    api = NeteaseAPI()
    return api.get_high_quality_playlists(cookies, cat, limit)

def category_playlists(cookies: Dict[str, str], limit: int = 20) -> List[Dict[str, Any]]:
    """获取分类歌单（向后兼容）"""
    api = NeteaseAPI()
    return api.get_category_playlists(cookies, limit)


if __name__ == "__main__":
    # 测试代码
    print("网易云音乐API模块")
    print("支持的功能:")
    print("- 歌曲URL获取")
    print("- 歌曲详情获取")
    print("- 歌词获取")
    print("- 音乐搜索")
    print("- 歌单详情")
    print("- 专辑详情")
    print("- 二维码登录")
    print("- 个性化推荐歌单")
    print("- 歌单分类")
    print("- 精品歌单")