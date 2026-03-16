"""
小红书内容发布模块
支持图文笔记、视频笔记发布
"""

import asyncio
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..adapters.xhs_api import XiaohongshuAPI
from ..utils.cookie_mgr import get_cookie_manager
from ..utils.media import ImageProcessor, VideoProcessor


class NotePublisher:
    """笔记发布器"""
    
    def __init__(self):
        self.cookie_manager = get_cookie_manager()
        self.api = XiaohongshuAPI(self.cookie_manager)
    
    def publish_image_note(
        self,
        title: str,
        desc: str,
        images: List[str],
        topics: Optional[List[str]] = None,
        is_private: bool = False
    ) -> Dict[str, Any]:
        """
        发布图文笔记
        
        Args:
            title: 标题
            desc: 描述/正文
            images: 图片文件路径列表
            topics: 话题标签
            is_private: 是否私密
            
        Returns:
            发布结果字典
        """
        result = {
            "success": False,
            "note_id": None,
            "error": None,
            "uploaded_images": [],
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # 1. 上传图片
            print(f"📸 开始上传 {len(images)} 张图片...")
            image_urls = []
            
            for i, img_path in enumerate(images, 1):
                print(f"  上传第 {i}/{len(images)} 张：{img_path}")
                url = self.api.upload_image(img_path)
                if url:
                    image_urls.append(url)
                    result["uploaded_images"].append(url)
                else:
                    result["error"] = f"图片上传失败：{img_path}"
                    return result
            
            if not image_urls:
                result["error"] = "没有图片上传成功"
                return result
            
            print(f"✅ {len(image_urls)} 张图片上传完成")
            
            # 2. 发布笔记
            print("📝 发布笔记...")
            success, note_id_or_error = self.api.publish_note(
                title=title,
                desc=desc,
                image_urls=image_urls,
                topics=topics,
                is_private=is_private
            )
            
            if success:
                result["success"] = True
                result["note_id"] = note_id_or_error
                print(f"🎉 笔记发布成功！ID: {note_id_or_error}")
            else:
                result["error"] = note_id_or_error
                
        except Exception as e:
            result["error"] = str(e)
            print(f"❌ 发布失败：{e}")
        
        return result
    
    def publish_video_note(
        self,
        title: str,
        desc: str,
        video_path: str,
        cover_image: Optional[str] = None,
        topics: Optional[List[str]] = None,
        is_private: bool = False
    ) -> Dict[str, Any]:
        """
        发布视频笔记
        
        Args:
            title: 标题
            desc: 描述
            video_path: 视频文件路径
            cover_image: 封面图片路径
            topics: 话题标签
            is_private: 是否私密
            
        Returns:
            发布结果字典
        """
        result = {
            "success": False,
            "note_id": None,
            "error": None,
            "video_url": None,
            "cover_url": None,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # 1. 上传视频
            print(f"🎬 上传视频：{video_path}")
            video_url = self.api.upload_video(video_path)
            if not video_url:
                result["error"] = "视频上传失败"
                return result
            result["video_url"] = video_url
            
            # 2. 上传封面
            cover_url = None
            if cover_image:
                print(f"📸 上传封面：{cover_image}")
                cover_url = self.api.upload_image(cover_image)
                result["cover_url"] = cover_url
            
            # 3. 发布视频笔记 (TODO: 需要实现视频发布 API)
            print("⚠️ 视频笔记发布功能开发中...")
            result["error"] = "视频笔记发布功能尚未实现"
            
        except Exception as e:
            result["error"] = str(e)
            print(f"❌ 发布失败：{e}")
        
        return result


class ScheduledPublisher:
    """定时发布器"""
    
    def __init__(self):
        self.publisher = NotePublisher()
        self.scheduled_tasks: List[Dict] = []
    
    def schedule_note(
        self,
        publish_time: datetime,
        title: str,
        desc: str,
        images: List[str],
        topics: Optional[List[str]] = None
    ) -> int:
        """
        定时发布笔记
        
        Args:
            publish_time: 发布时间
            title: 标题
            desc: 描述
            images: 图片列表
            topics: 话题
            
        Returns:
            任务 ID
        """
        task_id = len(self.scheduled_tasks) + 1
        
        task = {
            "id": task_id,
            "publish_time": publish_time,
            "title": title,
            "desc": desc,
            "images": images,
            "topics": topics,
            "status": "pending"
        }
        
        self.scheduled_tasks.append(task)
        print(f"✅ 定时任务已创建：ID={task_id}, 时间={publish_time}")
        
        return task_id
    
    async def run_scheduler(self) -> None:
        """运行定时任务调度器"""
        print("⏰ 定时任务调度器启动...")
        
        while True:
            now = datetime.now()
            
            for task in self.scheduled_tasks:
                if task["status"] == "pending" and task["publish_time"] <= now:
                    print(f"🚀 执行定时任务：{task['id']}")
                    
                    result = self.publisher.publish_image_note(
                        title=task["title"],
                        desc=task["desc"],
                        images=task["images"],
                        topics=task["topics"]
                    )
                    
                    task["status"] = "completed" if result["success"] else "failed"
                    task["result"] = result
            
            # 每分钟检查一次
            await asyncio.sleep(60)


# 便捷函数
def publish(title: str, desc: str, images: List[str], topics: Optional[List[str]] = None) -> Dict:
    """快速发布图文笔记"""
    publisher = NotePublisher()
    return publisher.publish_image_note(title, desc, images, topics)
