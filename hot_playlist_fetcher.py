#!/usr/bin/env python3
"""
网易云音乐热门歌单URL获取脚本

功能：
- 获取个性化推荐歌单
- 获取精品歌单
- 获取歌单分类
- 显示歌单详细信息，包括URL
"""

import os
import sys
import json
import argparse
from typing import List, Dict, Any
from pathlib import Path

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

try:
    from music_api import (
        personalized_playlists, 
        high_quality_playlists, 
        playlist_categories,
        category_playlists,
        qr_login
    )
    from cookie_manager import CookieManager, CookieException
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保所有依赖模块存在且可用")
    sys.exit(1)


class HotPlaylistFetcher:
    """热门歌单获取器"""
    
    def __init__(self):
        self.cookie_manager = CookieManager()
        self.api_functions = {
            'personalized': personalized_playlists,
            'high_quality': high_quality_playlists,
            'categories': playlist_categories
        }
    
    def check_and_get_cookies(self) -> Dict[str, str]:
        """检查并获取有效的cookies"""
        try:
            # 直接解析cookies，不进行严格验证（与其他脚本保持一致）
            cookies = self.cookie_manager.parse_cookies()
            
            if cookies:
                print("✓ 成功从cookie.txt文件中读取cookies")
                return cookies
            else:
                print("✗ cookie.txt文件为空或解析失败")
                return self._try_qr_login()
            
        except Exception as e:
            print(f"✗ 获取cookies时发生错误: {e}")
            return self._try_qr_login()
    
    def _try_qr_login(self) -> Dict[str, str]:
        """尝试二维码登录"""
        print("正在启动二维码登录...")
        
        try:
            cookie_string = qr_login()
            if cookie_string:
                # 保存新的cookies到文件
                self.cookie_manager.write_cookie(cookie_string)
                print("✓ 登录成功，cookies已保存到cookie.txt")
                # 使用cookie_manager的方法获取cookie字典
                return self.cookie_manager.get_cookie_for_request()
            else:
                print("✗ 登录失败，请检查网络连接或稍后重试")
                return {}
        except Exception as e:
            print(f"✗ 二维码登录失败: {e}")
            return {}
    
    def get_personalized_playlists(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取个性化推荐歌单"""
        cookies = self.check_and_get_cookies()
        if not cookies:
            print("✗ 无法获取有效的cookies")
            return []
        
        try:
            print(f"正在获取个性化推荐歌单 (数量: {limit})...")
            playlists = personalized_playlists(cookies, limit)
            print(f"✓ 成功获取 {len(playlists)} 个推荐歌单")
            return playlists
        except Exception as e:
            print(f"✗ 获取推荐歌单失败: {e}")
            return []
    
    def get_high_quality_playlists(self, category: str = '全部', limit: int = 20) -> List[Dict[str, Any]]:
        """获取精品歌单"""
        cookies = self.check_and_get_cookies()
        if not cookies:
            print("✗ 无法获取有效的cookies")
            return []
        
        try:
            print(f"正在获取精品歌单 (分类: {category}, 数量: {limit})...")
            playlists = high_quality_playlists(cookies, category, limit)
            print(f"✓ 成功获取 {len(playlists)} 个精品歌单")
            return playlists
        except Exception as e:
            print(f"✗ 获取精品歌单失败: {e}")
            return []
    
    def get_playlist_categories(self) -> Dict[str, Any]:
        """获取歌单分类"""
        cookies = self.check_and_get_cookies()
        if not cookies:
            print("✗ 无法获取有效的cookies")
            return {}
        
        try:
            print("正在获取歌单分类...")
            categories = playlist_categories(cookies)
            print(f"✓ 成功获取歌单分类")
            return categories
        except Exception as e:
            print(f"✗ 获取歌单分类失败: {e}")
            return {}
    
    def get_category_playlists(self, category: str = '全部', limit: int = 20) -> List[Dict[str, Any]]:
        """获取分类歌单（支持按分类获取）"""
        cookies = self.check_and_get_cookies()
        if not cookies:
            print("✗ 无法获取有效的cookies")
            return []
        
        try:
            print(f"正在获取分类歌单 (分类: {category}, 数量: {limit})...")
            # 使用新的分类歌单API，支持按分类获取
            from music_api import NeteaseAPI
            api = NeteaseAPI()
            playlists = api.get_category_playlists(cookies, category, limit)
            print(f"✓ 成功获取 {len(playlists)} 个分类歌单")
            return playlists
        except Exception as e:
            print(f"✗ 获取分类歌单失败: {e}")
            return []
    
    def category_playlists(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取分类歌单（所有分类下的歌单）- 向后兼容"""
        return self.get_category_playlists('全部', limit)
    
    def format_playlist_info(self, playlist: Dict[str, Any]) -> str:
        """格式化歌单信息"""
        info = []
        info.append(f"歌单ID: {playlist['id']}")
        info.append(f"名称: {playlist['name']}")
        info.append(f"URL: {playlist['url']}")
        info.append(f"播放量: {self.format_number(playlist.get('playCount', 0))}")
        info.append(f"歌曲数量: {playlist.get('trackCount', 0)}")
        
        if 'creator' in playlist and playlist['creator']:
            info.append(f"创建者: {playlist['creator']}")
        
        if 'description' in playlist and playlist['description']:
            desc = playlist['description'][:100] + "..." if len(playlist['description']) > 100 else playlist['description']
            info.append(f"描述: {desc}")
        
        if 'tags' in playlist and playlist['tags']:
            info.append(f"标签: {', '.join(playlist['tags'])}")
        
        return "\n".join(info)
    
    def format_number(self, num: int) -> str:
        """格式化数字显示"""
        if num >= 100000000:
            return f"{num/100000000:.1f}亿"
        elif num >= 10000:
            return f"{num/10000:.1f}万"
        else:
            return str(num)
    
    def display_playlists(self, playlists: List[Dict[str, Any]], title: str):
        """显示歌单列表"""
        if not playlists:
            print(f"未找到{title}")
            return
        
        print(f"\n{'='*60}")
        print(f"🎵 {title} (共{len(playlists)}个)")
        print(f"{'='*60}")
        
        for i, playlist in enumerate(playlists, 1):
            print(f"\n📁 歌单 {i}:")
            print(self.format_playlist_info(playlist))
            print("-" * 40)
    
    def display_categories(self, categories: Dict[str, Any]):
        """显示歌单分类"""
        if not categories:
            print("未找到歌单分类")
            return
        
        print(f"\n{'='*60}")
        print("🎵 歌单分类")
        print(f"{'='*60}")
        
        for category_name, sub_categories in categories.items():
            print(f"\n📂 {category_name}:")
            for sub_cat in sub_categories:
                hot_indicator = "🔥 " if sub_cat.get('hot', False) else ""
                print(f"  • {hot_indicator}{sub_cat['name']} (ID: {sub_cat['id']})")
    
    def save_to_file(self, data: Any, filename: str):
        """保存数据到文件"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                if isinstance(data, list):
                    json.dump(data, f, ensure_ascii=False, indent=2)
                else:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"✓ 数据已保存到: {filename}")
        except Exception as e:
            print(f"✗ 保存文件失败: {e}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='网易云音乐热门歌单URL获取工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 获取个性化推荐歌单
  python hot_playlist_fetcher.py --personalized --limit 10
  
  # 获取精品歌单
  python hot_playlist_fetcher.py --high-quality --category "华语" --limit 15
  
  # 获取歌单分类
  python hot_playlist_fetcher.py --categories
  
  # 保存结果到文件
  python hot_playlist_fetcher.py --personalized --save result.json
        """
    )
    
    parser.add_argument('--personalized', action='store_true', 
                       help='获取个性化推荐歌单')
    parser.add_argument('--high-quality', action='store_true', 
                       help='获取精品歌单')
    parser.add_argument('--categories', action='store_true', 
                       help='获取歌单分类')
    parser.add_argument('--category-playlists', action='store_true',
                       help='获取分类歌单（所有分类下的歌单）')
    parser.add_argument('--category', type=str, default='全部',
                       help='精品歌单分类 (默认: 全部)')
    parser.add_argument('--limit', type=int, default=20,
                       help='返回歌单数量限制 (默认: 20)')
    parser.add_argument('--save', type=str,
                       help='保存结果到指定文件')
    
    args = parser.parse_args()
    
    # 如果没有指定任何操作，显示帮助信息
    if not any([args.personalized, args.high_quality, args.categories, args.category_playlists]):
        parser.print_help()
        return
    
    fetcher = HotPlaylistFetcher()
    
    # 执行请求的操作
    results = None
    
    if args.personalized:
        results = fetcher.get_personalized_playlists(args.limit)
        fetcher.display_playlists(results, "个性化推荐歌单")
    
    if args.high_quality:
        results = fetcher.get_high_quality_playlists(args.category, args.limit)
        fetcher.display_playlists(results, f"精品歌单 - {args.category}")
    
    if args.categories:
        results = fetcher.get_playlist_categories()
        fetcher.display_categories(results)
    
    if args.category_playlists:
        results = fetcher.category_playlists(args.limit)
        fetcher.display_playlists(results, "分类歌单")
    
    # 保存结果到文件
    if args.save and results:
        fetcher.save_to_file(results, args.save)


if __name__ == "__main__":
    main()
