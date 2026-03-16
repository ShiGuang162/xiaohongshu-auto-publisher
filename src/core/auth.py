"""
小红书用户认证模块
支持扫码登录、二维码获取、登录状态检查
"""

import time
import asyncio
from typing import Optional, Tuple, Callable
from playwright.async_api import async_playwright, Browser, Page, BrowserContext

from ..utils.cookie_mgr import CookieManager, get_cookie_manager


class XiaohongshuAuth:
    """小红书认证类"""
    
    BASE_URL = "https://www.xiaohongshu.com"
    LOGIN_URL = "https://www.xiaohongshu.com/login"
    
    def __init__(self, cookie_manager: Optional[CookieManager] = None):
        self.cookie_manager = cookie_manager or get_cookie_manager()
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
    
    async def init_browser(self, headless: bool = False) -> None:
        """初始化浏览器"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=headless,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
            ]
        )
    
    async def close(self) -> None:
        """关闭浏览器"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
    
    async def check_login_status(self) -> bool:
        """检查登录状态"""
        cookies = self.cookie_manager.load()
        if not cookies or not self.cookie_manager.is_valid():
            return False
        
        try:
            if not self.browser:
                await self.init_browser(headless=True)
            
            self.context = await self.browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            # 过滤掉空值或无效 Cookie
            valid_cookies = []
            for k, v in cookies.items():
                if k and v and isinstance(v, str) and v.strip():
                    valid_cookies.append({
                        "name": k,
                        "value": v,
                        "domain": "xiaohongshu.com",
                        "path": "/"
                    })
            await self.context.add_cookies(valid_cookies)
            
            self.page = await self.context.new_page()
            await self.page.goto(self.BASE_URL, wait_until="networkidle", timeout=30000)
            
            # 检查是否跳转到首页（已登录）
            current_url = self.page.url
            is_logged_in = "login" not in current_url
            
            await self.close()
            return is_logged_in
        except Exception as e:
            print(f"❌ 检查登录状态失败：{e}")
            return False
    
    async def login_with_qr(
        self, 
        qr_callback: Optional[Callable[[str], None]] = None
    ) -> Tuple[bool, str]:
        """
        扫码登录
        
        Args:
            qr_callback: 二维码图片路径的回调函数
            
        Returns:
            (success, message)
        """
        try:
            if not self.browser:
                await self.init_browser(headless=False)  # 扫码需要可见浏览器
            
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()
            
            print("📱 打开小红书登录页面...")
            await self.page.goto(self.LOGIN_URL, wait_until="networkidle")
            
            # 等待二维码出现
            print("⏳ 等待二维码加载...")
            try:
                await self.page.wait_for_selector('canvas, img[src*="qr"]', timeout=15000)
            except:
                # 尝试点击扫码登录选项
                qr_tab = await self.page.query_selector('text=扫码登录')
                if qr_tab:
                    await qr_tab.click()
                    await self.page.wait_for_selector('canvas, img[src*="qr"]', timeout=10000)
            
            # 保存二维码截图
            qr_path = "/tmp/xhs_qr_code.png"
            qr_element = await self.page.query_selector('canvas')
            if qr_element:
                await qr_element.screenshot(path=qr_path)
            else:
                await self.page.screenshot(path=qr_path, clip={"x": 400, "y": 200, "width": 200, "height": 200})
            
            print(f"✅ 二维码已保存：{qr_path}")
            if qr_callback:
                qr_callback(qr_path)
            
            # 等待登录完成
            print("⏳ 等待扫码登录... (最多 60 秒)")
            for i in range(60):
                await asyncio.sleep(1)
                
                # 检查是否登录成功
                current_url = self.page.url
                if "login" not in current_url and self.BASE_URL in current_url:
                    print("✅ 登录成功！")
                    break
                
                # 检查是否有登录成功的提示
                try:
                    user_avatar = await self.page.query_selector('img[alt*="avatar"], .user-avatar')
                    if user_avatar:
                        print("✅ 检测到用户头像，登录成功！")
                        break
                except:
                    pass
                
                if i % 10 == 0 and i > 0:
                    print(f"⏳ 已等待 {i} 秒...")
            
            # 获取并保存 Cookie
            cookies = await self.context.cookies()
            cookie_dict = {c["name"]: c["value"] for c in cookies if c.get("name")}
            
            if self.cookie_manager.save(cookie_dict):
                print("✅ Cookie 已保存")
                await self.close()
                return True, "登录成功"
            else:
                await self.close()
                return False, "保存 Cookie 失败"
                
        except Exception as e:
            print(f"❌ 登录失败：{e}")
            await self.close()
            return False, str(e)
    
    async def ensure_logged_in(self) -> bool:
        """确保已登录，否则引导扫码登录"""
        # 先检查已有 Cookie
        if await self.check_login_status():
            print("✅ 已有有效登录状态")
            return True
        
        # 需要重新登录
        print("📱 需要扫码登录...")
        success, msg = await self.login_with_qr()
        return success


# 便捷函数
async def login(qr_callback: Optional[Callable[[str], None]] = None) -> bool:
    """便捷登录函数"""
    auth = XiaohongshuAuth()
    return await auth.ensure_logged_in()


async def check_status() -> bool:
    """便捷检查登录状态"""
    auth = XiaohongshuAuth()
    return await auth.check_login_status()
