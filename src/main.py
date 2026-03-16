"""
小红书全自动发布工具 - 主入口
"""

import asyncio
import argparse
from pathlib import Path
from typing import List, Optional

from .core.auth import XiaohongshuAuth, check_status, login
from .core.publisher import NotePublisher, ScheduledPublisher
from .core.web_publisher import WebNotePublisher, publish_via_web
from .utils.cookie_mgr import get_cookie_manager
from .utils.media import ImageProcessor, VideoProcessor


def cmd_login(args):
    """扫码登录命令"""
    async def _login():
        auth = XiaohongshuAuth()
        
        def on_qr_saved(qr_path: str):
            print(f"\n📱 请使用小红书 APP 扫码:\n   {qr_path}\n")
        
        success = await auth.ensure_logged_in()
        if success:
            print("✅ 登录成功！")
        else:
            print("❌ 登录失败")
    
    asyncio.run(_login())


def cmd_check(args):
    """检查登录状态"""
    async def _check():
        auth = XiaohongshuAuth()
        logged_in = await auth.check_login_status()
        
        if logged_in:
            print("✅ 已登录")
            # 获取用户信息
            from .adapters.xhs_api import XiaohongshuAPI
            api = XiaohongshuAPI()
            user_info = api.get_user_info()
            if user_info:
                nickname = user_info.get('nickname', 'Unknown')
                print(f"   用户：{nickname}")
        else:
            print("❌ 未登录，请先执行登录")
    
    asyncio.run(_check())


def cmd_publish(args):
    """发布笔记命令"""
    # 检查登录
    async def _check_login():
        auth = XiaohongshuAuth()
        return await auth.check_login_status()
    
    logged_in = asyncio.run(_check_login())
    if not logged_in:
        print("❌ 未登录，请先执行：python -m src.main login")
        return
    
    # 处理图片
    images = []
    for img_path in args.images:
        processed = ImageProcessor.compress(img_path)
        if processed:
            images.append(processed)
    
    if not images:
        print("❌ 没有有效的图片")
        return
    
    # 发布
    publisher = NotePublisher()
    result = publisher.publish_image_note(
        title=args.title,
        desc=args.desc,
        images=images,
        topics=args.topics.split(',') if args.topics else None,
        is_private=args.private
    )
    
    if result["success"]:
        print(f"\n🎉 发布成功！")
        print(f"   笔记 ID: {result['note_id']}")
    else:
        print(f"\n❌ 发布失败：{result['error']}")


def cmd_compress(args):
    """压缩图片命令"""
    for img_path in args.images:
        ImageProcessor.compress(
            img_path,
            max_width=args.max_width,
            max_height=args.max_height,
            quality=args.quality
        )


def cmd_web_publish(args):
    """网页版发布命令"""
    # 检查登录
    async def _check_login():
        auth = XiaohongshuAuth()
        return await auth.check_login_status()
    
    logged_in = asyncio.run(_check_login())
    if not logged_in:
        print("❌ 未登录，请先执行：python -m src.main login")
        return
    
    # 处理图片
    images = []
    for img_path in args.images:
        processed = ImageProcessor.compress(img_path)
        if processed:
            images.append(processed)
    
    if not images:
        print("❌ 没有有效的图片")
        return
    
    # 网页版发布
    async def _publish():
        publisher = WebNotePublisher()
        result = await publisher.publish_note(
            title=args.title,
            desc=args.desc,
            images=images,
            topics=args.topics.split(',') if args.topics else None
        )
        
        if result["success"]:
            print(f"\n🎉 发布成功！")
            if result.get('note_id'):
                print(f"   笔记：{result['note_id']}")
        else:
            print(f"\n❌ 发布失败：{result['error']}")
    
    asyncio.run(_publish())


def main():
    parser = argparse.ArgumentParser(
        description="小红书全自动发布工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 扫码登录
  python -m src.main login
  
  # 检查登录状态
  python -m src.main check
  
  # 发布图文笔记 (API 版)
  python -m src.main publish -t "标题" -d "描述" -i img1.jpg img2.jpg
  
  # 发布图文笔记 (网页版 - 推荐)
  python -m src.main web-publish -t "标题" -d "描述" -i img1.jpg img2.jpg
  
  # 压缩图片
  python -m src.main compress -i img1.jpg img2.jpg
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # login 命令
    login_parser = subparsers.add_parser('login', help='扫码登录')
    login_parser.set_defaults(func=cmd_login)
    
    # check 命令
    check_parser = subparsers.add_parser('check', help='检查登录状态')
    check_parser.set_defaults(func=cmd_check)
    
    # publish 命令
    publish_parser = subparsers.add_parser('publish', help='发布笔记')
    publish_parser.add_argument('-t', '--title', required=True, help='笔记标题')
    publish_parser.add_argument('-d', '--desc', required=True, help='笔记描述')
    publish_parser.add_argument('-i', '--images', nargs='+', required=True, help='图片文件列表')
    publish_parser.add_argument('--topics', help='话题标签 (逗号分隔)')
    publish_parser.add_argument('--private', action='store_true', help='私密笔记')
    publish_parser.set_defaults(func=cmd_publish)
    
    # compress 命令
    compress_parser = subparsers.add_parser('compress', help='压缩图片')
    compress_parser.add_argument('-i', '--images', nargs='+', required=True, help='图片文件列表')
    compress_parser.add_argument('--max-width', type=int, default=1080, help='最大宽度')
    compress_parser.add_argument('--max-height', type=int, default=1920, help='最大高度')
    compress_parser.add_argument('--quality', type=int, default=90, help='JPEG 质量')
    compress_parser.set_defaults(func=cmd_compress)
    
    # web-publish 命令
    web_publish_parser = subparsers.add_parser('web-publish', help='网页版发布笔记')
    web_publish_parser.add_argument('-t', '--title', required=True, help='笔记标题')
    web_publish_parser.add_argument('-d', '--desc', required=True, help='笔记描述')
    web_publish_parser.add_argument('-i', '--images', nargs='+', required=True, help='图片文件列表')
    web_publish_parser.add_argument('--topics', help='话题标签 (逗号分隔)')
    web_publish_parser.set_defaults(func=cmd_web_publish)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return
    
    args.func(args)


if __name__ == '__main__':
    main()
