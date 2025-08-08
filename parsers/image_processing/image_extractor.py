"""
图片提取器 - 负责图片的定位、保存、去重与图片块构建

升级后职责：
- 定位：在段落与表格单元格中按出现顺序发现图片（兼容 w:drawing 与 VML pict）
- 保存：根据 rel_id 从文档关系中获取图片数据并保存到磁盘
- 去重：基于 rel_id 做缓存，避免重复保存
- 构块：统一生成图片块（type=image）以便被解析器就地插入

保留旧方法 extract_images_from_docx 作为回退（append_end）策略，不再作为默认入口。
"""

import os
import time
from typing import List, Dict, Optional, TypedDict
from docx.oxml.ns import qn
from utils.logger import logger


class ImageExtractor:
    """图片定位/保存/去重/构块统一入口"""

    # 命名空间映射（用于底层XML遍历）
    _NSMAP = {
        "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
        "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
        "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
        "v": "urn:schemas-microsoft-com:vml",
    }

    class ParagraphImageRef(TypedDict):
        rel_id: str
        order_in_paragraph: int

    class TableCellImageRef(TypedDict):
        rel_id: str
        row_index: int
        col_index: int
        order_in_cell: int

    class SavedCacheMeta(TypedDict):
        image_path: str
        original_filename: str
        unique_filename: str
        ext: str

    class SavedImageMeta(TypedDict):
        image_path: str
        original_filename: str
        unique_filename: str
        ext: str
        rel_id: str
        image_index: int

    class AnchorMeta(TypedDict, total=False):
        container_type: str
        paragraph_index: Optional[int]
        table_id: Optional[str]
        row: Optional[int]
        col: Optional[int]
        parent_table_info: Optional[str]
        anchor_index: Optional[int]

    def __init__(self, storage_path: str = "storage/images"):
        self.storage_path = storage_path
        self.ensure_storage_directory()
        # 基于 rel_id 的去重缓存
        self._rel_cache: Dict[str, "ImageExtractor.SavedCacheMeta"] = {}

    def ensure_storage_directory(self) -> None:
        """确保存储目录存在"""
        os.makedirs(self.storage_path, exist_ok=True)

    # --------- 新增：定位方法（段落） ---------
    def discover_images_in_paragraph(
        self, paragraph
    ) -> List["ImageExtractor.ParagraphImageRef"]:
        """
        在段落内发现图片，保持出现顺序。

        Returns: List of { rel_id, order_in_paragraph }
        """
        results: List[ImageExtractor.ParagraphImageRef] = []
        try:
            p = paragraph._p  # 底层 w:p
            # 联合选择 a:blip 与 v:imagedata，保持文档顺序（使用 local-name 规避命名空间未注册问题）
            nodes = p.xpath(
                ".//*[local-name()='drawing']//*[local-name()='blip'] | .//*[local-name()='pict']//*[local-name()='imagedata']"
            )
            order = 0
            for node in nodes:
                rel_id = None
                # a:blip 使用 r:embed
                if node.tag.endswith("blip"):
                    rel_id = node.get(qn("r:embed"))
                else:
                    # v:imagedata 使用 r:id
                    rel_id = node.get(qn("r:id"))
                if rel_id:
                    results.append({"rel_id": rel_id, "order_in_paragraph": order})
                    order += 1
        except Exception as e:
            logger.warning(f"段落图片定位失败，已跳过：{e}")
        return results

    # --------- 新增：定位方法（表格单元格） ---------
    def discover_images_in_table_cell(
        self, cell
    ) -> List["ImageExtractor.TableCellImageRef"]:
        """
        在表格单元格内发现图片，保持出现顺序，计算 row/col 下标。

        Returns: List of { rel_id, row_index, col_index, order_in_cell }
        """
        results: List[ImageExtractor.TableCellImageRef] = []
        try:
            tc = cell._tc  # w:tc
            tr = tc.getparent()  # w:tr
            tbl = tr.getparent()  # w:tbl

            # 计算行下标
            row_index = 0
            for sibling in tbl.iterchildren():
                if sibling is tr:
                    break
                if sibling.tag.endswith("tr"):
                    row_index += 1

            # 计算列下标
            col_index = 0
            for sibling in tr.iterchildren():
                if sibling is tc:
                    break
                if sibling.tag.endswith("tc"):
                    col_index += 1

            # 遍历单元格内部段落以保持顺序（精细：run级图片会随段落顺序出现）
            order = 0
            for para in cell.paragraphs:
                p = para._p
                nodes = p.xpath(
                    ".//*[local-name()='drawing']//*[local-name()='blip'] | .//*[local-name()='pict']//*[local-name()='imagedata']"
                )
                for node in nodes:
                    rel_id = None
                    if node.tag.endswith("blip"):
                        rel_id = node.get(qn("r:embed"))
                    else:
                        rel_id = node.get(qn("r:id"))
                    if rel_id:
                        results.append(
                            {
                                "rel_id": rel_id,
                                "row_index": row_index,
                                "col_index": col_index,
                                "order_in_cell": order,
                            }
                        )
                        order += 1
        except Exception as e:
            logger.warning(f"表格单元格图片定位失败，已跳过：{e}")
        return results

    # --------- 新增：保存与去重 ---------
    def get_or_save_by_rel(
        self, document, rel_id: str, doc_id: str, image_index: int
    ) -> Optional["ImageExtractor.SavedImageMeta"]:
        """
        根据 rel_id 获取或保存图片，返回图片元信息。
        返回：{ image_path, original_filename, unique_filename, ext, rel_id, image_index }
        """
        try:
            if rel_id in self._rel_cache:
                cached = self._rel_cache[rel_id]
                return ImageExtractor.SavedImageMeta(
                    image_path=cached["image_path"],
                    original_filename=cached["original_filename"],
                    unique_filename=cached["unique_filename"],
                    ext=cached["ext"],
                    rel_id=rel_id,
                    image_index=image_index,
                )

            rel = document.part.rels.get(rel_id)
            if not rel:
                logger.warning(f"未在主文档关系中找到图片关系: {rel_id}，已跳过")
                return None

            image_data = rel.target_part.blob
            original_filename = rel.target_ref
            _, ext = os.path.splitext(original_filename)
            if not ext:
                ext = ".png"

            unique_filename = self.generate_filename(
                doc_id, image_index, original_filename
            )
            image_path = self.save_image(image_data, unique_filename, doc_id)

            info: ImageExtractor.SavedCacheMeta = ImageExtractor.SavedCacheMeta(
                image_path=image_path,
                original_filename=original_filename,
                unique_filename=unique_filename,
                ext=ext,
            )
            self._rel_cache[rel_id] = info

            return ImageExtractor.SavedImageMeta(
                image_path=image_path,
                original_filename=original_filename,
                unique_filename=unique_filename,
                ext=ext,
                rel_id=rel_id,
                image_index=image_index,
            )
        except Exception as e:
            logger.warning(f"通过关系保存图片失败（{rel_id}）：{e}")
            return None

    # --------- 新增：构建图片块 ---------
    def build_image_chunk(
        self,
        doc_id: str,
        image_meta: "ImageExtractor.SavedImageMeta",
        anchor_meta: "ImageExtractor.AnchorMeta",
    ) -> Dict[str, object]:
        """
        构建标准图片块（type=image）
        image_meta: { image_path, original_filename, unique_filename, ext, rel_id, image_index }
        anchor_meta: { container_type, paragraph_index? 或 table_id/row/col, parent_table_info?, anchor_index? }
        """
        metadata: Dict[str, object] = {
            "doc_id": doc_id,
            "image_filename": image_meta.get("unique_filename", ""),
            "original_filename": image_meta.get("original_filename", ""),
            "image_index": image_meta.get("image_index", -1),
            "rel_id": image_meta.get("rel_id", ""),
            "processing_status": "pending",
            # 锚点相关
            "container_type": anchor_meta.get("container_type", ""),
            "paragraph_index": anchor_meta.get("paragraph_index"),
            "table_id": anchor_meta.get("table_id"),
            "row": anchor_meta.get("row"),
            "col": anchor_meta.get("col"),
            "parent_table_info": anchor_meta.get("parent_table_info", ""),
            "anchor_index": anchor_meta.get("anchor_index"),
        }

        return {
            "type": "image",
            "content": image_meta.get("image_path", ""),
            "metadata": metadata,
            "context": "",
        }

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

        with open(file_path, "wb") as f:
            f.write(image_data)

        logger.info(f"图片已保存: {file_path}")
        return file_path

    # --------- 保留：回退方法（不在内联策略中使用） ---------
    def extract_images_from_docx(self, document, doc_id: str) -> List[Dict]:
        """从DOCX文档中提取图片（回退：append_end），不保证顺序正确"""
        images = []
        image_index = 0
        try:
            for rel_id, rel in document.part.rels.items():
                if "image" in getattr(rel, "target_ref", ""):
                    image_data = rel.target_part.blob
                    original_filename = rel.target_ref
                    unique_filename = self.generate_filename(
                        doc_id, image_index, original_filename
                    )
                    image_path = self.save_image(image_data, unique_filename, doc_id)
                    images.append(
                        {
                            "original_filename": original_filename,
                            "unique_filename": unique_filename,
                            "image_path": image_path,
                            "image_data": image_data,
                            "rel_id": rel_id,
                            "image_index": image_index,
                        }
                    )
                    image_index += 1
            logger.info(f"[fallback] 从文档 {doc_id} 中提取了 {len(images)} 张图片")
        except Exception as e:
            logger.error(f"[fallback] 图片提取失败: {str(e)}")
        return images
