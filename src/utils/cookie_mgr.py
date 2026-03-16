"""
小红书 Cookie 管理模块
负责 Cookie 的保存、加载、验证和刷新
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


class CookieManager:
    """小红书 Cookie 管理器"""
    
    def __init__(self, storage_path: str = "~/.xiaohongshu/cookies.json"):
        self.storage_path = Path(storage_path).expanduser()
        self.cookies: Dict[str, Any] = {}
        self.last_refresh: Optional[datetime] = None
        
    def save(self, cookies: Dict[str, Any]) -> bool:
        """保存 Cookie 到本地"""
        try:
            # 确保目录存在
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "cookies": cookies,
                "saved_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(days=30)).isoformat()
            }
            
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.cookies = cookies
            self.last_refresh = datetime.now()
            return True
        except Exception as e:
            print(f"❌ 保存 Cookie 失败：{e}")
            return False
    
    def load(self) -> Optional[Dict[str, Any]]:
        """从本地加载 Cookie"""
        if not self.storage_path.exists():
            return None
        
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 检查是否过期
            expires_at = datetime.fromisoformat(data.get("expires_at", ""))
            if datetime.now() > expires_at:
                print("⚠️ Cookie 已过期，需要重新登录")
                return None
            
            self.cookies = data.get("cookies", {})
            self.last_refresh = datetime.fromisoformat(data.get("saved_at", ""))
            return self.cookies
        except Exception as e:
            print(f"❌ 加载 Cookie 失败：{e}")
            return None
    
    def is_valid(self) -> bool:
        """检查 Cookie 是否有效"""
        if not self.cookies:
            return False
        
        # 检查关键 Cookie 字段
        required_keys = ["web_session", "a1"]
        for key in required_keys:
            if key not in self.cookies:
                return False
        
        return True
    
    def get_cookie_string(self) -> str:
        """获取 Cookie 字符串格式"""
        return "; ".join([f"{k}={v}" for k, v in self.cookies.items()])
    
    def clear(self) -> bool:
        """清除保存的 Cookie"""
        try:
            if self.storage_path.exists():
                self.storage_path.unlink()
            self.cookies = {}
            self.last_refresh = None
            return True
        except Exception as e:
            print(f"❌ 清除 Cookie 失败：{e}")
            return False


# 全局单例
_cookie_manager: Optional[CookieManager] = None


def get_cookie_manager(storage_path: str = "~/.xiaohongshu/cookies.json") -> CookieManager:
    """获取 Cookie 管理器单例"""
    global _cookie_manager
    if _cookie_manager is None:
        _cookie_manager = CookieManager(storage_path)
    return _cookie_manager
