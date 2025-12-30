"""
异步下载功能测试脚本
用于验证异步下载功能是否正常工作
"""

import asyncio
import time
from task_manager import task_manager, init_task_manager, shutdown_task_manager
from async_downloader import (
    submit_music_download_task,
    submit_playlist_download_task, 
    submit_artist_download_task
)


def test_music_download():
    """测试音乐下载任务"""
    print("🎵 测试音乐下载任务...")
    
    # 提交一个音乐下载任务
    task_id = submit_music_download_task("123456", "lossless")
    print(f"✅ 音乐下载任务已提交，任务ID: {task_id}")
    
    # 检查任务状态
    task = task_manager.get_task(task_id)
    if task:
        print(f"📊 任务状态: {task.status.value}")
        print(f"📈 任务进度: {task.progress}%")
    else:
        print("❌ 无法获取任务信息")
    
    return task_id


def test_playlist_download():
    """测试歌单下载任务"""
    print("🎵 测试歌单下载任务...")
    
    # 提交一个歌单下载任务
    task_id = submit_playlist_download_task("123456789", "lossless")
    print(f"✅ 歌单下载任务已提交，任务ID: {task_id}")
    
    # 检查任务状态
    task = task_manager.get_task(task_id)
    if task:
        print(f"📊 任务状态: {task.status.value}")
        print(f"📈 任务进度: {task.progress}%")
    else:
        print("❌ 无法获取任务信息")
    
    return task_id


def test_artist_download():
    """测试艺术家下载任务"""
    print("🎵 测试艺术家下载任务...")
    
    # 提交一个艺术家下载任务
    task_id = submit_artist_download_task("周杰伦", "lossless", limit=5)
    print(f"✅ 艺术家下载任务已提交，任务ID: {task_id}")
    
    # 检查任务状态
    task = task_manager.get_task(task_id)
    if task:
        print(f"📊 任务状态: {task.status.value}")
        print(f"📈 任务进度: {task.progress}%")
    else:
        print("❌ 无法获取任务信息")
    
    return task_id


def test_task_management():
    """测试任务管理功能"""
    print("🔄 测试任务管理功能...")
    
    # 获取所有任务
    tasks = task_manager.get_all_tasks()
    print(f"📋 当前任务数量: {len(tasks)}")
    
    # 显示任务列表
    for i, task in enumerate(tasks):
        print(f"  {i+1}. 任务ID: {task.task_id}, 类型: {task.task_type}, 状态: {task.status.value}, 进度: {task.progress}%")
    
    return len(tasks)


async def main():
    """主测试函数"""
    print("🚀 开始测试异步下载功能...")
    
    # 初始化任务管理器
    print("🔄 初始化任务管理器...")
    await init_task_manager()
    
    try:
        # 测试各种下载任务
        music_task_id = test_music_download()
        playlist_task_id = test_playlist_download()
        artist_task_id = test_artist_download()
        
        # 等待一段时间让任务开始执行
        print("⏳ 等待任务执行...")
        await asyncio.sleep(3)
        
        # 测试任务管理功能
        task_count = test_task_management()
        
        # 测试取消任务功能
        if task_count > 0:
            print("🛑 测试取消任务功能...")
            success = task_manager.cancel_task(music_task_id)
            if success:
                print("✅ 任务取消成功")
            else:
                print("❌ 任务取消失败")
        
        print("\n✅ 异步下载功能测试完成！")
        print("📋 测试总结:")
        print(f"  - 音乐下载任务: {music_task_id}")
        print(f"  - 歌单下载任务: {playlist_task_id}")
        print(f"  - 艺术家下载任务: {artist_task_id}")
        print(f"  - 总任务数: {task_count}")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
    
    finally:
        # 关闭任务管理器
        print("🔄 关闭任务管理器...")
        await shutdown_task_manager()
        print("✅ 任务管理器已关闭")


if __name__ == "__main__":
    asyncio.run(main())
