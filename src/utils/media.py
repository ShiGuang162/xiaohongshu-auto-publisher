"""
媒体处理模块
图片/视频的压缩、裁剪、格式转换等
"""

import os
from pathlib import Path
from typing import Optional, Tuple, Dict
from PIL import Image


class ImageProcessor:
    """图片处理器"""
    
    MAX_WIDTH = 1080
    MAX_HEIGHT = 1920
    QUALITY = 90
    
    @staticmethod
    def compress(
        image_path: str,
        output_path: Optional[str] = None,
        max_width: int = 1080,
        max_height: int = 1920,
        quality: int = 90
    ) -> Optional[str]:
        """
        压缩图片
        
        Args:
            image_path: 输入图片路径
            output_path: 输出路径 (默认覆盖原文件)
            max_width: 最大宽度
            max_height: 最大高度
            quality: JPEG 质量 (1-100)
            
        Returns:
            输出文件路径或 None
        """
        path = Path(image_path)
        if not path.exists():
            print(f"❌ 文件不存在：{image_path}")
            return None
        
        try:
            img = Image.open(path)
            
            # 调整尺寸
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # 转换格式 (确保是 RGB)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # 确定输出路径
            if output_path:
                out_path = Path(output_path)
            else:
                out_path = path
            
            # 保存
            out_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(out_path, 'JPEG', quality=quality, optimize=True)
            
            # 获取文件大小
            original_size = path.stat().st_size
            compressed_size = out_path.stat().st_size
            ratio = (1 - compressed_size / original_size) * 100
            
            print(f"✅ 图片压缩完成：{out_path}")
            print(f"   原始：{original_size / 1024:.1f} KB → 压缩后：{compressed_size / 1024:.1f} KB (节省 {ratio:.1f}%)")
            
            return str(out_path)
            
        except Exception as e:
            print(f"❌ 图片压缩失败：{e}")
            return None
    
    @staticmethod
    def get_info(image_path: str) -> Optional[Dict]:
        """获取图片信息"""
        try:
            img = Image.open(image_path)
            return {
                "width": img.width,
                "height": img.height,
                "format": img.format,
                "mode": img.mode,
                "size": Path(image_path).stat().st_size
            }
        except Exception as e:
            print(f"❌ 获取图片信息失败：{e}")
            return None
    
    @staticmethod
    def create_cover(video_path: str, output_path: str, timestamp: float = 0.5) -> Optional[str]:
        """
        从视频生成封面
        
        Args:
            video_path: 视频路径
            output_path: 输出封面路径
            timestamp: 截取时间点 (0.0-1.0)
            
        Returns:
            封面图片路径或 None
        """
        # TODO: 使用 ffmpeg 实现
        print("⚠️ 视频封面生成功能开发中...")
        return None


class VideoProcessor:
    """视频处理器"""
    
    MAX_SIZE_MB = 500
    SUPPORTED_FORMATS = ['.mp4', '.mov', '.avi', '.mkv']
    
    @staticmethod
    def compress(
        video_path: str,
        output_path: Optional[str] = None,
        max_size_mb: int = 500
    ) -> Optional[str]:
        """
        压缩视频
        
        Args:
            video_path: 输入视频路径
            output_path: 输出路径
            max_size_mb: 最大文件大小 (MB)
            
        Returns:
            输出文件路径或 None
        """
        # TODO: 使用 ffmpeg 实现
        print("⚠️ 视频压缩功能开发中...")
        return None
    
    @staticmethod
    def get_info(video_path: str) -> Optional[Dict]:
        """获取视频信息"""
        path = Path(video_path)
        if not path.exists():
            return None
        
        try:
            # TODO: 使用 ffprobe 获取详细信息
            return {
                "path": str(path),
                "size": path.stat().st_size,
                "format": path.suffix
            }
        except Exception as e:
            print(f"❌ 获取视频信息失败：{e}")
            return None
    
    @staticmethod
    def validate(video_path: str) -> Tuple[bool, str]:
        """
        验证视频是否符合小红书要求
        
        Returns:
            (valid, message)
        """
        path = Path(video_path)
        
        if not path.exists():
            return False, "文件不存在"
        
        if path.suffix.lower() not in VideoProcessor.SUPPORTED_FORMATS:
            return False, f"不支持的视频格式：{path.suffix}"
        
        size_mb = path.stat().st_size / (1024 * 1024)
        if size_mb > VideoProcessor.MAX_SIZE_MB:
            return False, f"视频过大：{size_mb:.1f} MB (最大 {VideoProcessor.MAX_SIZE_MB} MB)"
        
        return True, "验证通过"


# 便捷函数
def process_image(path: str, output: Optional[str] = None) -> Optional[str]:
    """快速处理图片"""
    return ImageProcessor.compress(path, output)


def validate_video(path: str) -> Tuple[bool, str]:
    """快速验证视频"""
    return VideoProcessor.validate(path)
