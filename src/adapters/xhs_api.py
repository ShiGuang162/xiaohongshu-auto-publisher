"""
小红书 API 封装模块
提供发布笔记、上传媒体等功能的 API 接口
"""

import json
import time
import hashlib
import random
import string
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
import requests

from ..utils.cookie_mgr import get_cookie_manager


class XiaohongshuAPI:
    """小红书 API 客户端"""
    
    BASE_URL = "https://edith.xiaohongshu.com"
    WEB_BASE_URL = "https://www.xiaohongshu.com"
    
    def __init__(self, cookie_manager=None):
        self.cookie_manager = cookie_manager or get_cookie_manager()
        self.session = requests.Session()
        self._setup_headers()
    
    def _setup_headers(self) -> None:
        """设置请求头"""
        cookies = self.cookie_manager.load()
        if not cookies:
            raise Exception("未登录，请先扫码登录")
        
        cookie_string = self.cookie_manager.get_cookie_string()
        
        self.session.headers.update({
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
            "content-type": "application/json;charset=UTF-8",
            "cookie": cookie_string,
            "origin": self.WEB_BASE_URL,
            "referer": f"{self.WEB_BASE_URL}/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "x-s": self._generate_x_s(),
            "x-t": str(int(time.time() * 1000)),
        })
    
    def _generate_x_s(self) -> str:
        """生成 X-S 签名 (简化版)"""
        timestamp = str(int(time.time() * 1000))
        random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        data = f"Xs{timestamp}{random_str}"
        return hashlib.md5(data.encode()).hexdigest()
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict]:
        """发送 HTTP 请求"""
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ 请求失败：{e}")
            return None
    
    def upload_image(self, image_path: str) -> Optional[str]:
        """
        上传图片
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            图片 URL 或 None
        """
        path = Path(image_path)
        if not path.exists():
            print(f"❌ 文件不存在：{image_path}")
            return None
        
        # 获取上传凭证
        upload_info = self._get_upload_token("image")
        if not upload_info:
            return None
        
        # 上传图片
        try:
            with open(path, 'rb') as f:
                files = {'file': (path.name, f, 'image/jpeg')}
                response = requests.post(upload_info['upload_url'], files=files)
                response.raise_for_status()
            
            # 获取图片 URL
            image_url = upload_info.get('url', '')
            print(f"✅ 图片上传成功：{image_url}")
            return image_url
        except Exception as e:
            print(f"❌ 图片上传失败：{e}")
            return None
    
    def upload_video(self, video_path: str) -> Optional[str]:
        """
        上传视频
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            视频 URL 或 None
        """
        path = Path(video_path)
        if not path.exists():
            print(f"❌ 文件不存在：{video_path}")
            return None
        
        # 获取上传凭证
        upload_info = self._get_upload_token("video")
        if not upload_info:
            return None
        
        # 上传视频
        try:
            with open(path, 'rb') as f:
                files = {'file': (path.name, f, 'video/mp4')}
                response = requests.post(upload_info['upload_url'], files=files)
                response.raise_for_status()
            
            video_url = upload_info.get('url', '')
            print(f"✅ 视频上传成功：{video_url}")
            return video_url
        except Exception as e:
            print(f"❌ 视频上传失败：{e}")
            return None
    
    def _get_upload_token(self, media_type: str) -> Optional[Dict]:
        """获取上传凭证"""
        endpoint = "/api/sns/web/v1/upload/getToken"
        data = {
            "mediaType": media_type,
            "bucket": "xiaohongshu"
        }
        
        result = self._request("POST", endpoint, json=data)
        if result and result.get('success'):
            return result.get('data', {})
        return None
    
    def publish_note(
        self,
        title: str,
        desc: str,
        image_urls: List[str],
        topics: Optional[List[str]] = None,
        is_private: bool = False
    ) -> Tuple[bool, str]:
        """
        发布图文笔记
        
        Args:
            title: 标题
            desc: 描述
            image_urls: 图片 URL 列表
            topics: 话题标签列表
            is_private: 是否私密
            
        Returns:
            (success, note_id or error_message)
        """
        if not image_urls:
            return False, "至少需要一张图片"
        
        endpoint = "/api/sns/web/v1/note"
        
        # 构建话题
        topic_data = []
        if topics:
            for topic in topics:
                topic_data.append({
                    "id": "",
                    "name": topic,
                    "link": f"/search/topic/{topic}"
                })
        
        data = {
            "title": title,
            "desc": desc,
            "imageInfos": [
                {"url": url, "fileHash": "", "width": 1080, "height": 1080}
                for url in image_urls
            ],
            "topics": topic_data,
            "privacy": 1 if is_private else 0,
            "source": 1
        }
        
        result = self._request("POST", endpoint, json=data)
        
        if result:
            if result.get('success'):
                note_id = result.get('data', {}).get('noteId', '')
                print(f"✅ 笔记发布成功！ID: {note_id}")
                return True, note_id
            else:
                error_msg = result.get('msg', '发布失败')
                print(f"❌ 发布失败：{error_msg}")
                return False, error_msg
        
        return False, "请求失败"
    
    def get_user_info(self) -> Optional[Dict]:
        """获取用户信息"""
        endpoint = "/api/sns/web/v1/user/me"
        result = self._request("GET", endpoint)
        
        if result and result.get('success'):
            return result.get('data', {})
        return None


# 便捷函数
def get_api_client():
    """获取 API 客户端实例"""
    return XiaohongshuAPI(get_cookie_manager())
