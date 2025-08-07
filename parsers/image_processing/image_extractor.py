"""
图片提取器 - 从DOCX文档中提取图片
"""
import os
import time
from typing import List, Dict, Optional
from utils.logger import logger


class ImageExtractor:
    """从DOCX文档中提取图片"""
    
    def __init__(self, storage_path: str = "storage/images"):
        self.storage_path = storage_path
        self.ensure_storage_directory()
    
    def ensure_storage_directory(self):
        """确保存储目录存在"""
        os.makedirs(self.storage_path, exist_ok=True)
    
    def extract_images_from_docx(self, document, doc_id: str) -> List[Dict]:
        """从DOCX文档中提取图片"""
        images = []
        image_index = 0
        
        try:
            # 遍历文档中的所有关系
            for rel_id, rel in document.part.rels.items():
                if "image" in rel.target_ref:
                    # 提取图片数据
                    image_data = rel.target_part.blob
                    original_filename = rel.target_ref
                    
                    # 生成唯一文件名
                    unique_filename = self.generate_filename(doc_id, image_index, original_filename)
                    
                    # 保存图片文件
                    image_path = self.save_image(image_data, unique_filename, doc_id)
                    
                    images.append({
                        "original_filename": original_filename,
                        "unique_filename": unique_filename,
                        "image_path": image_path,
                        "image_data": image_data,
                        "rel_id": rel_id,
                        "image_index": image_index
                    })
                    
                    image_index += 1
            
            logger.info(f"从文档 {doc_id} 中提取了 {len(images)} 张图片")
            return images
            
        except Exception as e:
            logger.error(f"图片提取失败: {str(e)}")
            return []
    
    def generate_filename(self, doc_id: str, index: int, original_filename: str) -> str:
        """生成唯一文件名"""
        timestamp = int(time.time())
        # 获取原始文件扩展名
        _, ext = os.path.splitext(original_filename)
        if not ext:
            ext = ".png"  # 默认扩展名
        
        return f"{doc_id}_img_{index}_{timestamp}{ext}"
    
    def save_image(self, image_data: bytes, filename: str, doc_id: str) -> str:
        """保存图片到存储路径"""
        # 创建文档专用目录
        doc_dir = os.path.join(self.storage_path, doc_id)
        os.makedirs(doc_dir, exist_ok=True)
        
        file_path = os.path.join(doc_dir, filename)
        
        with open(file_path, 'wb') as f:
            f.write(image_data)
        
        logger.info(f"图片已保存: {file_path}")
        return file_path