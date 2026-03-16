"""
小红书网页版发布模块
使用 Playwright 直接模拟网页操作发布笔记
绕过 API 签名问题
"""

import asyncio
import time
from pathlib import Path
from typing import List, Optional, Dict, Any
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from .auth import XiaohongshuAuth
from ..utils.cookie_mgr import get_cookie_manager
from ..utils.media import ImageProcessor


class WebNotePublisher:
    """网页版笔记发布器"""
    
    BASE_URL = "https://www.xiaohongshu.com"
    # 尝试多个发布页面 URL
    PUBLISH_URLS = [
        "https://www.xiaohongshu.com/publish",
        "https://creator.xiaohongshu.com/publish/publish",
        "https://www.xiaohongshu.com/note/create"
    ]
    
    def __init__(self):
        self.cookie_manager = get_cookie_manager()
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
    
    async def init(self, headless: bool = True) -> None:
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
        
        # 加载 Cookie
        cookies = self.cookie_manager.load()
        if not cookies:
            raise Exception("未登录，请先扫码登录")
        
        self.context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        # 设置 Cookie
        valid_cookies = []
        for k, v in cookies.items():
            if k and v and isinstance(v, str) and v.strip():
                # 创作者平台需要正确的域
                valid_cookies.append({
                    "name": k,
                    "value": v,
                    "domain": ".xiaohongshu.com",
                    "path": "/"
                })
                # 同时添加到 creator 域
                if "creator" in self.PUBLISH_URLS[1]:
                    valid_cookies.append({
                        "name": k,
                        "value": v,
                        "domain": "creator.xiaohongshu.com",
                        "path": "/"
                    })
        await self.context.add_cookies(valid_cookies)
        
        self.page = await self.context.new_page()
    
    async def close(self) -> None:
        """关闭浏览器"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
    
    async def publish_note(
        self,
        title: str,
        desc: str,
        images: List[str],
        topics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        发布图文笔记（网页版）
        
        Args:
            title: 标题
            desc: 描述
            images: 图片文件路径列表
            topics: 话题标签
            
        Returns:
            发布结果
        """
        result = {
            "success": False,
            "note_id": None,
            "error": None,
            "timestamp": time.time()
        }
        
        try:
            if not self.page:
                await self.init(headless=False)  # 发布时用可见浏览器
            
            print("🌐 打开发布页面...")
            page_loaded = False
            
            for publish_url in self.PUBLISH_URLS:
                try:
                    await self.page.goto(publish_url, wait_until="networkidle", timeout=30000)
                    await asyncio.sleep(5)  # 等待 SPA 加载
                    
                    # 检查是否登录
                    current_url = self.page.url
                    if "login" in current_url:
                        print(f"  ⚠️ 需要登录：{publish_url}")
                        continue
                    
                    # 检查是否是发布页面（而不是首页）
                    page_html = await self.page.content()
                    if "publish" in current_url.lower() or "create" in current_url.lower() or "上传" in page_html or "publish" in page_html.lower():
                        print(f"  ✅ 成功访问：{publish_url}")
                        print(f"     当前 URL: {current_url}")
                        page_loaded = True
                        break
                    else:
                        print(f"  ⚠️ 页面不正确 (可能是首页): {publish_url}")
                        print(f"     当前 URL: {current_url}")
                except Exception as e:
                    print(f"  ⚠️ 访问失败 {publish_url}: {e}")
            
            if not page_loaded:
                result["error"] = "无法访问发布页面"
                return result
            

            
            print("📸 上传图片...")
            # 查找上传按钮并上传图片
            image_paths = [str(Path(img).absolute()) for img in images]
            
            # 尝试多种上传按钮选择器
            upload_selectors = [
                'input[type="file"]',
                '.upload-input',
                '[class*="upload"]',
                'button[class*="upload"]'
            ]
            
            uploaded_count = 0
            for img_path in image_paths:
                for selector in upload_selectors:
                    try:
                        file_input = await self.page.query_selector(selector)
                        if file_input:
                            await file_input.set_input_files(img_path)
                            print(f"  ✅ 已上传：{img_path}")
                            uploaded_count += 1
                            await asyncio.sleep(1)  # 等待上传完成
                            break
                    except:
                        continue
            
            if uploaded_count == 0:
                # 保存页面截图用于调试
                await self.page.screenshot(path="/tmp/xhs_publish_debug.png")
                print("  📸 页面截图已保存：/tmp/xhs_publish_debug.png")
                
                # 获取页面 HTML
                html = await self.page.content()
                with open("/tmp/xhs_publish_debug.html", "w") as f:
                    f.write(html[:10000])
                print("  📄 页面 HTML 已保存：/tmp/xhs_publish_debug.html")
                
                result["error"] = "图片上传失败 - 请检查页面结构"
                return result
            
            print(f"✅ {uploaded_count} 张图片上传完成")
            await asyncio.sleep(2)
            
            print("📝 填写标题...")
            # 填写标题
            title_selectors = [
                'input[placeholder*="标题"]',
                'input[class*="title"]',
                '[class*="title"] input'
            ]
            
            for selector in title_selectors:
                try:
                    title_input = await self.page.query_selector(selector)
                    if title_input:
                        await title_input.fill(title)
                        print(f"  ✅ 标题已填写")
                        break
                except:
                    continue
            
            print("📄 填写描述...")
            # 填写描述
            desc_selectors = [
                'textarea[placeholder*="正文"]',
                'textarea[placeholder*="描述"]',
                'textarea[class*="content"]',
                '[class*="editor"] textarea'
            ]
            
            for selector in desc_selectors:
                try:
                    desc_input = await self.page.query_selector(selector)
                    if desc_input:
                        await desc_input.fill(desc)
                        print(f"  ✅ 描述已填写")
                        break
                except:
                    continue
            
            # 添加话题
            if topics:
                print("🏷️ 添加话题...")
                for topic in topics:
                    try:
                        # 输入话题
                        topic_input = await self.page.query_selector('input[placeholder*="话题"]')
                        if topic_input:
                            await topic_input.fill(f"#{topic}")
                            await asyncio.sleep(0.5)
                            # 按回车选择第一个话题
                            await self.page.keyboard.press("Enter")
                            await asyncio.sleep(0.5)
                            print(f"  ✅ 已添加话题：#{topic}")
                    except Exception as e:
                        print(f"  ⚠️ 话题添加失败：{e}")
            
            print("🚀 点击发布...")
            # 点击发布按钮
            publish_selectors = [
                'button:has-text("发布")',
                'button:has-text("立即发布")',
                '[class*="publish"]',
                'button[class*="submit"]'
            ]
            
            for selector in publish_selectors:
                try:
                    publish_btn = await self.page.query_selector(selector)
                    if publish_btn:
                        await publish_btn.click()
                        print("  ✅ 已点击发布按钮")
                        break
                except:
                    continue
            
            # 等待发布完成
            print("⏳ 等待发布完成...")
            for i in range(30):
                await asyncio.sleep(1)
                
                # 检查是否发布成功
                current_url = self.page.url
                if "success" in current_url.lower() or "publish" not in current_url.lower():
                    print("✅ 发布成功！")
                    result["success"] = True
                    result["note_id"] = current_url
                    break
                
                # 检查是否有成功提示
                try:
                    success_msg = await self.page.query_selector('text=发布成功')
                    if success_msg:
                        print("✅ 检测到发布成功提示！")
                        result["success"] = True
                        break
                except:
                    pass
                
                if i % 5 == 0 and i > 0:
                    print(f"  ⏳ 已等待 {i} 秒...")
            
            if not result["success"]:
                result["error"] = "发布超时，请检查是否成功"
            
        except Exception as e:
            result["error"] = str(e)
            print(f"❌ 发布失败：{e}")
        finally:
            await self.close()
        
        return result
    
    async def test_login(self) -> bool:
        """测试登录状态"""
        try:
            if not self.page:
                await self.init(headless=True)
            
            await self.page.goto(self.BASE_URL, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(2)
            
            current_url = self.page.url
            is_logged_in = "login" not in current_url
            
            await self.close()
            return is_logged_in
        except Exception as e:
            print(f"❌ 测试失败：{e}")
            await self.close()
            return False


# 便捷函数
async def publish_via_web(
    title: str,
    desc: str,
    images: List[str],
    topics: Optional[List[str]] = None
) -> Dict[str, Any]:
    """快速发布（网页版）"""
    publisher = WebNotePublisher()
    return await publisher.publish_note(title, desc, images, topics)
