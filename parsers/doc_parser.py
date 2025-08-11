"""
DOC/DOCX文件解析器实现（docx用python-docx，doc用LibreOffice转换）
"""

import os
import subprocess
import tempfile
import platform
from typing import List, Dict, Optional, Tuple
from utils.logger import logger

from docx.table import Table
from docx.text.paragraph import Paragraph
from dotenv import load_dotenv
import asyncio
from utils.zhipu_client import zhipu_complete_async, parse_json_response
from utils.chunk_prompts import SYSTEM_PROMPTS, STRUCTURED_PROMPTS
from utils.config import LLM_CONFIG
from .fragment_manager import FragmentManager
from .fragment_config import FragmentConfig, TableProcessingConfig


class LibreOfficeNotFoundError(Exception):
    """LibreOffice未安装或无法找到"""

    pass


class ConversionError(Exception):
    """DOC转DOCX转换失败"""

    pass


class ConversionTimeoutError(Exception):
    """转换超时"""

    pass


def check_libreoffice_installation() -> bool:
    """检测LibreOffice是否已安装"""
    system = platform.system().lower()

    if system == "windows":
        # Windows路径检查
        possible_paths = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return True
        return False
    else:
        # Linux/macOS使用which命令检查
        try:
            result = subprocess.run(
                ["which", "libreoffice"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False


def get_libreoffice_command() -> str:
    """获取LibreOffice命令路径"""
    system = platform.system().lower()

    if system == "windows":
        possible_paths = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        ]
        for path in possible_paths:
            if os.path.exists(path):
                return path
        raise LibreOfficeNotFoundError("Windows系统未找到LibreOffice安装")
    else:
        # Linux/macOS
        try:
            result = subprocess.run(
                ["which", "libreoffice"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
            )
            if result.returncode == 0:
                return "libreoffice"
            raise LibreOfficeNotFoundError("系统未找到libreoffice命令")
        except subprocess.TimeoutExpired:
            raise LibreOfficeNotFoundError("检测libreoffice命令超时")


def convert_doc_to_docx(doc_path: str, output_dir: Optional[str] = None) -> str:
    """使用LibreOffice将DOC文件转换为DOCX格式"""
    if not os.path.exists(doc_path):
        raise FileNotFoundError(f"DOC文件不存在: {doc_path}")

    # 检查LibreOffice安装
    if not check_libreoffice_installation():
        raise LibreOfficeNotFoundError("系统未安装LibreOffice，无法转换DOC文件")

    # 获取输出目录
    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="doc_conversion_")
    else:
        os.makedirs(output_dir, exist_ok=True)

    # 获取LibreOffice命令
    libreoffice_cmd = get_libreoffice_command()

    # 构建转换命令
    cmd = [
        libreoffice_cmd,
        "--headless",
        "--convert-to",
        "docx",
        "--outdir",
        output_dir,
        doc_path,
    ]

    try:
        # 执行转换命令
        result = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60  # 60秒超时
        )

        if result.returncode != 0:
            error_msg = result.stderr.decode("utf-8", errors="ignore")
            raise ConversionError(f"LibreOffice转换失败: {error_msg}")

        # 检查转换结果
        doc_filename = os.path.basename(doc_path)
        docx_filename = os.path.splitext(doc_filename)[0] + ".docx"
        docx_path = os.path.join(output_dir, docx_filename)

        if not os.path.exists(docx_path):
            raise ConversionError(f"转换后的DOCX文件不存在: {docx_path}")

        logger.info(f"成功将DOC文件转换为DOCX: {docx_path}")
        return docx_path

    except subprocess.TimeoutExpired:
        raise ConversionTimeoutError("DOC转DOCX转换超时（60秒）")
    except Exception as e:
        if isinstance(e, (ConversionError, ConversionTimeoutError)):
            raise
        raise ConversionError(f"转换过程中发生未知错误: {str(e)}")


class DocFileParser:
    """DOC/DOCX文件解析器，docx用python-docx，doc用textract/antiword，输出分块结构"""

    def __init__(self, fragment_config: Optional[FragmentConfig] = None):
        """初始化解析器"""
        self.fragment_manager = (
            FragmentManager(fragment_config) if fragment_config else None
        )
        self.table_config = (
            fragment_config.table_processing
            if fragment_config
            else TableProcessingConfig()
        )

        # 新增图片处理组件
        try:
            from utils.config_manager import ConfigManager

            config_manager = ConfigManager()
            image_config = config_manager.get_image_processing_config()

            if image_config.get("enabled", False):
                from .image_processing.image_extractor import ImageExtractor
                from .image_processing.context_collector import ContextCollector
                from .image_processing.image_analyzer import ImageAnalyzer
                from utils.zhipu_client import VisionModelClient

                self.image_extractor = ImageExtractor(
                    image_config.get("storage_path", "storage/images")
                )
                self.context_collector = ContextCollector(
                    image_config.get("context_window", 1)
                )
                self.vision_model = VisionModelClient(image_config.get("api_key"))
                self.image_analyzer = ImageAnalyzer(
                    self.vision_model, self.context_collector
                )
                # 新增：图片策略配置
                self.image_position_strategy = image_config.get(
                    "image_position_strategy", "inline"
                )
                self.table_image_attach_mode = image_config.get(
                    "table_image_attach_mode", "separate_block"
                )
                self.image_processing_enabled = True
                logger.info("图片处理功能已启用")
            else:
                self.image_processing_enabled = False
                logger.debug("图片处理功能未启用")
        except Exception as e:
            logger.warning(f"图片处理组件初始化失败，将禁用图片处理功能: {str(e)}")
            self.image_processing_enabled = False

    async def process(self, file_path: str) -> List[Dict]:
        logger.info(f"开始解析Word文档: {file_path}")
        if not os.path.exists(file_path):
            logger.error(f"文件不存在: {file_path}")
            return []

        # 清空图片提取器缓存，确保每个文档的图片处理都是独立的
        if hasattr(self, "image_extractor") and self.image_extractor:
            self.image_extractor.clear_cache()
            logger.debug(f"已清空图片提取器缓存，准备处理新文档: {file_path}")

        _, ext = os.path.splitext(file_path)
        ext = ext.lower().lstrip(".")
        doc_id = os.path.basename(file_path)
        if ext == "docx":
            try:
                chunks = await self._process_docx(file_path, doc_id)
            except Exception as e:
                logger.error(f"DOCX文件处理失败: {str(e)}")
                return []
        elif ext == "doc":
            try:
                chunks = await self._process_doc(file_path, doc_id)
            except (
                LibreOfficeNotFoundError,
                ConversionError,
                ConversionTimeoutError,
            ) as e:
                logger.error(f"DOC文件处理失败: {str(e)}")
                return []  # 转换失败时返回空列表
        else:
            logger.error(f"不支持的Word文档格式: {ext}")
            return []

        # 新增：智能分片处理
        if self.fragment_manager:
            chunks = self.fragment_manager.process_chunks(chunks)
            # 输出分片统计信息
            stats = self.fragment_manager.get_fragment_statistics(chunks)
            logger.info(f"分片统计: {stats}")

        # 为每个分块添加chunk_id
        for idx, chunk in enumerate(chunks):
            chunk["chunk_id"] = f"{doc_id}_{idx+1}"

        # 调用LLM增强所有分块
        try:
            import asyncio
            import nest_asyncio

            # 应用nest_asyncio以支持嵌套事件循环
            nest_asyncio.apply()

            # 检查是否已有运行的事件循环
            try:
                loop = asyncio.get_running_loop()
                # 如果已有事件循环，创建任务
                task = loop.create_task(enhance_all_chunks(chunks))
                enhanced_chunks = loop.run_until_complete(task)
            except RuntimeError:
                # 如果没有运行的事件循环，使用asyncio.run
                enhanced_chunks = asyncio.run(enhance_all_chunks(chunks))

            logger.info(f"成功增强 {len(enhanced_chunks)} 个分块")
            return enhanced_chunks
        except Exception as e:
            logger.error(f"LLM增强分块失败: {str(e)}")
            return chunks  # 如果增强失败，返回原始分块

    async def _process_docx(self, file_path: str, doc_id: str) -> List[Dict]:
        """解析DOCX文件，提取段落、表格和图片内容"""
        try:
            from docx import Document

            document = Document(file_path)

            # 混合遍历段落和表格，记录表格前后段落索引
            block_items = list(self._iter_block_items(document))
            # 先收集所有段落内容
            all_paragraphs = [
                block.text
                for block in block_items
                if isinstance(block, Paragraph) and block.text.strip()
            ]
            paragraphs = []
            all_chunks = []
            para_idx = 0
            # 全局图片索引，保证文档范围内唯一且递增
            global_image_index = 0
            # 构块阶段全局去重：记录已处理过的图片关系ID（rel_id）
            seen_rel_ids = set()
            for idx, block in enumerate(block_items):
                if isinstance(block, Paragraph):
                    has_text = bool(block.text.strip())
                    if has_text:
                        paragraphs.append(block.text)
                        context = self._get_context_for_paragraph(
                            all_paragraphs, para_idx
                        )
                        chunk = {
                            "type": "text",
                            "content": block.text,  # 纯文本输出
                            "metadata": {
                                "doc_id": doc_id,
                                "paragraph_index": para_idx + 1,
                            },
                            "context": context,
                        }
                        all_chunks.append(chunk)

                    # 段落后内联图片（无论该段是否有文本）
                    if (
                        self.image_processing_enabled
                        and self.image_position_strategy == "inline"
                    ):
                        try:
                            discovered = (
                                self.image_extractor.discover_images_in_paragraph(block)
                            )
                            for order_in_para, item in enumerate(discovered):
                                rel_id = item.get("rel_id")
                                if not rel_id:
                                    continue
                                # 去重：同一图片（rel_id）仅生成一个图片块
                                if rel_id in seen_rel_ids:
                                    continue
                                image_meta = self.image_extractor.get_or_save_by_rel(
                                    document,
                                    rel_id,
                                    doc_id,
                                    image_index=global_image_index,
                                )
                                if not image_meta:
                                    continue
                                seen_rel_ids.add(rel_id)
                                paragraph_index_for_anchor = (
                                    (para_idx + 1)
                                    if has_text
                                    else (para_idx if para_idx > 0 else 1)
                                )
                                anchor_meta = {
                                    "container_type": "paragraph",
                                    "paragraph_index": paragraph_index_for_anchor,
                                    "anchor_index": len(all_chunks),
                                }
                                image_chunk = self.image_extractor.build_image_chunk(
                                    doc_id, image_meta, anchor_meta
                                )
                                all_chunks.append(image_chunk)
                                global_image_index += 1

                            if discovered:
                                if has_text:
                                    try:
                                        ctx = self._get_context_for_paragraph(
                                            all_paragraphs, para_idx
                                        )
                                        prev20 = ctx.split("。下一段：")[0].replace(
                                            "上一段：", ""
                                        )[:20]
                                        next20 = ctx.split("。下一段：")[-1][:20]
                                    except Exception:
                                        prev20, next20 = "", ""
                                    logger.debug(
                                        f"段落{para_idx + 1}后插入图片{len(discovered)}张，前后摘要：{prev20} | {next20}"
                                    )
                                else:
                                    logger.debug(
                                        f"空段落后插入图片{len(discovered)}张（锚定到段落{paragraph_index_for_anchor}）"
                                    )
                        except Exception as e:
                            logger.warning(f"段落内联图片处理失败，已跳过：{e}")

                    if has_text:
                        para_idx += 1
                elif isinstance(block, Table):
                    # 找到表格前后最近的段落索引
                    preceding = para_idx if para_idx > 0 else None
                    # 查找下一个段落
                    following = None
                    for j in range(idx + 1, len(block_items)):
                        if (
                            isinstance(block_items[j], Paragraph)
                            and block_items[j].text.strip()
                        ):
                            following = para_idx + 1  # 预期下一个段落索引
                            break
                    table_chunks = self._split_table_with_merge(
                        block, doc_id, preceding, following, paragraphs=all_paragraphs
                    )
                    all_chunks.extend(table_chunks)

                    # 表格内图片处理
                    if (
                        self.image_processing_enabled
                        and self.image_position_strategy == "inline"
                    ):
                        try:
                            # 构造 table_id，与 _split_table_with_merge 保持一致
                            table_id = f"table_{id(block)}"
                            header_rows = self._detect_header_rows_smart(block)
                            # 收集每个单元格的图片
                            table_images: List[Dict] = []
                            for r_idx, row in enumerate(block.rows):
                                for c_idx, cell in enumerate(row.cells):
                                    discovered = self.image_extractor.discover_images_in_table_cell(
                                        cell
                                    )
                                    if not discovered:
                                        continue
                                    for item in discovered:
                                        rel_id = item.get("rel_id")
                                        if not rel_id:
                                            continue
                                        # 去重：同一图片（rel_id）仅生成一个图片块
                                        if rel_id in seen_rel_ids:
                                            continue
                                        image_meta = (
                                            self.image_extractor.get_or_save_by_rel(
                                                document,
                                                rel_id,
                                                doc_id,
                                                image_index=global_image_index,
                                            )
                                        )
                                        if not image_meta:
                                            continue
                                        seen_rel_ids.add(rel_id)
                                        anchor_meta = {
                                            "container_type": "table_cell",
                                            "table_id": table_id,
                                            "row": r_idx + 1,
                                            "col": c_idx + 1,
                                            "parent_table_info": f"header_rows={header_rows}",
                                            "anchor_index": len(all_chunks),
                                        }
                                        image_chunk = (
                                            self.image_extractor.build_image_chunk(
                                                doc_id, image_meta, anchor_meta
                                            )
                                        )
                                        table_images.append(
                                            {
                                                "row": r_idx + 1,
                                                "col": c_idx + 1,
                                                "chunk": image_chunk,
                                            }
                                        )
                                        global_image_index += 1

                            # 按策略附着
                            if table_images:
                                if self.table_image_attach_mode == "separate_block":
                                    # 插在表格相关块之后（当前已把表格块加入 all_chunks，直接 append）
                                    for ti in table_images:
                                        all_chunks.append(ti["chunk"])
                                    # 计算邻接段落摘要用于调试
                                    try:
                                        prev_text = (
                                            self.get_paragraph_content_by_index(
                                                all_paragraphs, preceding
                                            )
                                            if all_paragraphs
                                            else ""
                                        ) or ""
                                        next_text = (
                                            self.get_paragraph_content_by_index(
                                                all_paragraphs, following
                                            )
                                            if all_paragraphs
                                            else ""
                                        ) or ""
                                    except Exception:
                                        prev_text, next_text = "", ""
                                    logger.debug(
                                        f"表格{table_id}后追加图片{len(table_images)}张，邻接段落摘要：{prev_text[:20]} | {next_text[:20]}"
                                    )
                                elif self.table_image_attach_mode == "merge_into_row":
                                    # 合并进对应行块的 metadata.embedded_images
                                    for ti in table_images:
                                        row_no = ti["row"]
                                        # 逆向查找刚加入的 table_row 对应的块（简易策略：查找最近的、table_id+row匹配）
                                        for chk in reversed(all_chunks):
                                            md = chk.get("metadata", {})
                                            if (
                                                chk.get("type") == "table_row"
                                                and md.get("table_id") == table_id
                                                and md.get("row") == row_no
                                            ):
                                                md.setdefault(
                                                    "embedded_images", []
                                                ).append(ti["chunk"])
                                                break
                                    logger.debug(
                                        f"表格{table_id}按行合并图片{len(table_images)}张"
                                    )
                                elif self.table_image_attach_mode == "merge_into_table":
                                    # 合并进 table_full 的 metadata.embedded_images
                                    for chk in reversed(all_chunks):
                                        md = chk.get("metadata", {})
                                        if (
                                            chk.get("type") == "table_full"
                                            and md.get("table_id") == table_id
                                        ):
                                            md.setdefault("embedded_images", []).extend(
                                                [ti["chunk"] for ti in table_images]
                                            )
                                            break
                                    logger.debug(
                                        f"表格{table_id}整体合并图片{len(table_images)}张"
                                    )
                        except Exception as e:
                            logger.warning(f"表格内联图片处理失败，已跳过：{e}")

            # 内联模式下，图片块已经插入 all_chunks；选择分析时机
            if self.image_processing_enabled:
                # 收集本轮生成的图片块
                image_chunks = [c for c in all_chunks if c.get("type") == "image"]
                if image_chunks:
                    try:
                        await self._process_images_async(image_chunks, all_chunks)
                    except Exception as e:
                        logger.warning(f"图片分析失败: {str(e)}")

            return all_chunks
        except ImportError:
            logger.error("未安装python-docx库，无法解析DOCX文件")
            raise
        except Exception as e:
            logger.error(f"解析DOCX文件出错: {file_path}, 错误: {str(e)}")
            raise

    async def _process_doc(self, file_path: str, doc_id: str) -> List[Dict]:
        """使用LibreOffice转换DOC文件为DOCX，然后解析"""
        docx_path = None
        try:
            # 使用LibreOffice将DOC文件转换为DOCX
            docx_path = convert_doc_to_docx(file_path)
            # 使用现有的DOCX解析逻辑
            chunks = await self._process_docx(docx_path, doc_id)
            return chunks
        except (LibreOfficeNotFoundError, ConversionError, ConversionTimeoutError) as e:
            logger.error(f"DOC文件转换失败: {file_path}, 错误: {str(e)}")
            raise  # 转换失败直接抛出异常，不进行备选解析
        except Exception as e:
            logger.error(f"解析DOC文件出错: {file_path}, 错误: {str(e)}")
            raise
        finally:
            # 清理临时转换文件
            if docx_path and os.path.exists(docx_path):
                try:
                    os.remove(docx_path)
                    # 尝试删除临时目录（如果为空）
                    temp_dir = os.path.dirname(docx_path)
                    if os.path.exists(temp_dir) and not os.listdir(temp_dir):
                        os.rmdir(temp_dir)
                except Exception as e:
                    logger.warning(f"清理临时文件失败: {str(e)}")

    def _split_paragraphs(self, paragraphs: List[str], doc_id: str) -> List[Dict]:
        chunks = []
        for idx, para in enumerate(paragraphs):
            context = self._get_context_for_paragraph(paragraphs, idx)
            chunk = {
                "type": "text",
                "content": para,
                "metadata": {"doc_id": doc_id, "paragraph_index": idx + 1},
                "context": context,
            }
            chunks.append(chunk)
        return chunks

    def _split_table_with_merge(
        self,
        table: Table,
        doc_id: str,
        preceding: Optional[int],
        following: Optional[int],
        paragraphs: Optional[List[str]] = None,
        headers: Optional[List[str]] = None,
        parent_table_info: Optional[str] = None,
    ) -> List[Dict]:
        """
        处理合并单元格，根据配置生成表格分块，记录合并信息和上下文段落内容。
        paragraphs: 所有段落内容列表，用于查找上下文内容
        headers: 可选，表头内容
        parent_table_info: 可选，父表格信息
        """
        all_chunks = []
        table_id = f"table_{id(table)}"

        # 根据配置获取表格格式
        table_content, table_headers, merged_cells = self._convert_table_to_format(
            table
        )

        # 获取上下文段落内容
        preceding_content = (
            self.get_paragraph_content_by_index(paragraphs, preceding)
            if paragraphs
            else None
        )
        following_content = (
            self.get_paragraph_content_by_index(paragraphs, following)
            if paragraphs
            else None
        )
        context = self._get_context_for_table(preceding_content, following_content)

        # 构造 parent_table_info
        parent_info = (
            parent_table_info
            if parent_table_info is not None
            else f"表头: {table_headers} 合并单元格: {merged_cells}"
        )

        # 根据配置决定是否生成完整表格块
        if self.table_config.table_chunking_strategy in ["full_only", "full_and_rows"]:
            table_chunk = {
                "type": "table_full",
                "content": table_content,
                "metadata": {
                    "doc_id": doc_id,
                    "table_id": table_id,
                    "preceding_paragraph_index": preceding,
                    "following_paragraph_index": following,
                    "preceding_paragraph_content": preceding_content,
                    "following_paragraph_content": following_content,
                    "header": table_headers,
                    "merged_cells": merged_cells,
                    "parent_table_info": parent_info,
                    "table_format": self.table_config.table_format,
                },
                "context": context,
            }
            all_chunks.append(table_chunk)

        # 根据配置决定是否生成表格行数据
        if self.table_config.table_chunking_strategy == "full_and_rows":
            row_chunks = self._generate_table_row_chunks(
                table,
                doc_id,
                table_id,
                preceding,
                following,
                preceding_content,
                following_content,
                table_headers,
                parent_info,
                context,
            )
            all_chunks.extend(row_chunks)

        return all_chunks

    def _convert_table_to_format(
        self, table: Table
    ) -> Tuple[str, List[str], List[Dict]]:
        """根据配置将表格转换为指定格式，包含错误处理和回退机制"""
        try:
            if self.table_config.table_format == "markdown":
                return self._table_to_markdown_with_merge_enhanced(table)
            else:
                return self._table_to_html_with_merge_enhanced(table)
        except Exception as e:
            logger.warning(f"增强表格转换失败，回退到基础方法: {str(e)}")
            # 回退到基础方法
            try:
                if self.table_config.table_format == "markdown":
                    return self._table_to_markdown_with_merge_fallback(table)
                else:
                    return self._table_to_html_with_merge_fallback(table)
            except Exception as fallback_error:
                logger.error(f"基础表格转换也失败: {str(fallback_error)}")
                # 最后的回退：返回空表格
                return "<table></table>", [], []

    def _table_to_html_with_merge_enhanced(
        self, table: Table
    ) -> Tuple[str, List[str], List[Dict]]:
        """
        增强的HTML表格转换，正确处理合并单元格
        """
        if not table.rows:
            return "<table></table>", [], []

        # 构建表头映射（使用带回退机制的方法）
        header_mapping = self._build_header_mapping_with_fallback(table)

        # 获取合并单元格信息
        merged_cells = self._get_merged_cells_info_ultra_enhanced(table)

        # 生成最终表头
        headers = []
        for col in range(len(table.rows[0].cells)):
            header = header_mapping.get(col, "")
            headers.append(header)

        html = ["<table border='1'>"]

        # 构建合并单元格映射，用于HTML生成
        merge_map = self._build_merge_map_for_html_enhanced(
            merged_cells, len(table.rows[0].cells)
        )

        # 生成表头行
        self._generate_html_header_rows_enhanced(table, html, merge_map, header_mapping)

        # 生成表体行
        self._generate_html_body_rows_enhanced(table, html, merge_map)

        html.append("</table>")
        return "\n".join(html), headers, merged_cells

    def _build_merge_map_for_html_enhanced(
        self, merged_cells: List[Dict], num_cols: int
    ) -> Dict[int, Dict]:
        """构建增强的合并单元格映射，用于HTML生成"""
        merge_map = {}
        for merge_info in merged_cells:
            if merge_info["is_merged_start"]:
                start_col = merge_info["col"]
                colspan = merge_info["colspan"]
                for col_offset in range(colspan):
                    col = start_col + col_offset
                    if col < num_cols:
                        merge_map[col] = {
                            "is_merged": col_offset == 0,  # 只有第一个单元格显示内容
                            "colspan": (
                                colspan if col_offset == 0 else 0
                            ),  # 只有第一个单元格有colspan
                            "text": merge_info["text"] if col_offset == 0 else "",
                            "merge_type": merge_info["merge_type"],
                        }
        return merge_map

    def _generate_html_header_rows_enhanced(
        self,
        table: Table,
        html: List[str],
        merge_map: Dict[int, Dict],
        header_mapping: Dict[int, str],
    ):
        """生成增强的HTML表头行，正确处理表头行数"""
        # 检测表头行数
        header_rows = self._detect_header_rows_smart(table)

        # 只生成表头行
        for row_idx in range(header_rows):
            if row_idx >= len(table.rows):
                break
            row = table.rows[row_idx]
            html.append("<tr>")
            for col_idx, cell in enumerate(row.cells):
                if col_idx in merge_map and merge_map[col_idx]["is_merged"]:
                    # 合并单元格
                    colspan = merge_map[col_idx]["colspan"]
                    text = merge_map[col_idx]["text"]
                    html.append(f'<th colspan="{colspan}">{text}</th>')
                elif col_idx in merge_map and not merge_map[col_idx]["is_merged"]:
                    # 被合并的单元格，跳过
                    continue
                else:
                    # 普通单元格
                    cell_text = cell.text.strip()
                    html.append(f"<th>{cell_text if cell_text else '-'}</th>")
            html.append("</tr>")

    def _generate_html_body_rows_enhanced(
        self, table: Table, html: List[str], merge_map: Dict[int, Dict]
    ):
        """生成增强的HTML表体行，正确处理表头行数"""
        # 检测表头行数
        header_rows = self._detect_header_rows_smart(table)

        # 从表头行之后开始生成表体行
        for row_idx in range(header_rows, len(table.rows)):
            row = table.rows[row_idx]
            html.append("<tr>")
            for col_idx, cell in enumerate(row.cells):
                cell_text = cell.text.strip()
                html.append(f"<td>{cell_text if cell_text else '-'}</td>")
            html.append("</tr>")

    def _table_to_html_with_merge_fallback(
        self, table: Table
    ) -> Tuple[str, List[str], List[Dict]]:
        """HTML转换的回退方法"""
        if not table.rows:
            return "<table></table>", [], []

        html = ["<table border='1'>"]
        headers = []
        merged_cells = []

        # 简单的表头处理
        if table.rows:
            headers = [cell.text.strip() for cell in table.rows[0].cells]
            html.append(
                "<tr>"
                + "".join(
                    [f"<th>{header if header else '-'}</th>" for header in headers]
                )
                + "</tr>"
            )

        # 简单的表体处理
        for row in table.rows[1:]:
            html.append(
                "<tr>"
                + "".join(
                    [
                        f"<td>{cell.text.strip() if cell.text.strip() else '-'}</td>"
                        for cell in row.cells
                    ]
                )
                + "</tr>"
            )

        html.append("</table>")
        return "\n".join(html), headers, merged_cells

    def _table_to_markdown_with_merge_enhanced(
        self, table: Table
    ) -> Tuple[str, List[str], List[Dict]]:
        """增强的Markdown表格转换，体现合并单元格层次结构"""
        if not table.rows:
            return "", [], []

        # 构建表头映射（使用带回退机制的方法）
        header_mapping = self._build_header_mapping_with_fallback(table)

        # 获取合并单元格信息
        merged_cells = self._get_merged_cells_info_ultra_enhanced(table)

        # 生成最终表头
        headers = []
        for col in range(len(table.rows[0].cells)):
            header = header_mapping.get(col, "")
            headers.append(header)

        markdown_lines = []

        # 表头 - 使用层次结构表头
        header_row = "| " + " | ".join(headers) + " |"
        markdown_lines.append(header_row)

        # 分隔线 - 使用标准格式并添加对齐方式
        separator_cells = []
        for col in range(len(headers)):
            # 根据数据类型确定对齐方式
            alignment = self._get_column_alignment_for_doc_enhanced(table, col)
            separator_cells.append(alignment)
        separator_row = "| " + " | ".join(separator_cells) + " |"
        markdown_lines.append(separator_row)

        # 表体 - 过滤空行，确保数据行连续
        header_rows = self._detect_header_rows_smart(table)
        for row_idx in range(header_rows, len(table.rows)):
            row = table.rows[row_idx]
            # 检查当前行是否为空行
            row_texts = [cell.text.strip() for cell in row.cells]
            if any(text for text in row_texts):  # 只有当行中有非空数据时才添加
                data_row = (
                    "| "
                    + " | ".join(
                        [
                            cell.text.strip() if cell.text.strip() else "-"
                            for cell in row.cells
                        ]
                    )
                    + " |"
                )
                markdown_lines.append(data_row)

        return "\n".join(markdown_lines), headers, merged_cells

    def _table_to_markdown_with_merge_fallback(
        self, table: Table
    ) -> Tuple[str, List[str], List[Dict]]:
        """Markdown转换的回退方法"""
        if not table.rows:
            return "", [], []

        markdown_lines = []
        headers = []
        merged_cells = []

        # 简单的表头处理
        if table.rows:
            headers = [
                cell.text.strip() if cell.text.strip() else "-"
                for cell in table.rows[0].cells
            ]
            header_row = "| " + " | ".join(headers) + " |"
            markdown_lines.append(header_row)

            # 分隔线 - 第一列左对齐，其他列右对齐
            separator_cells = []
            for i in range(len(headers)):
                if i == 0:
                    separator_cells.append("---")  # 第一列左对齐
                else:
                    separator_cells.append("---:")  # 其他列右对齐
            separator_row = "| " + " | ".join(separator_cells) + " |"
            markdown_lines.append(separator_row)

        # 简单的表体处理
        for row in table.rows[1:]:
            data_row = (
                "| "
                + " | ".join(
                    [
                        cell.text.strip() if cell.text.strip() else "-"
                        for cell in row.cells
                    ]
                )
                + " |"
            )
            markdown_lines.append(data_row)

        return "\n".join(markdown_lines), headers, merged_cells

    def _get_column_alignment_for_doc_enhanced(self, table: Table, col: int) -> str:
        """根据列位置确定对齐方式：第一列左对齐，其他列右对齐"""
        if col == 0:
            return "---"  # 第一列左对齐
        else:
            return "---:"  # 其他列右对齐

    def _generate_table_row_chunks(
        self,
        table: Table,
        doc_id: str,
        table_id: str,
        preceding: Optional[int],
        following: Optional[int],
        preceding_content: Optional[str],
        following_content: Optional[str],
        table_headers: List[str],
        parent_info: str,
        context: str,
    ) -> List[Dict]:
        """生成表格行分块，正确处理表头行数"""
        row_chunks = []
        header_rows = self._detect_header_rows_smart(table)

        for r_idx in range(header_rows, len(table.rows)):
            row = table.rows[r_idx]
            row_content = self._row_to_format(row, table_headers)
            row_chunk = {
                "type": "table_row",
                "content": row_content,
                "metadata": {
                    "doc_id": doc_id,
                    "table_id": table_id,
                    "row": r_idx + 1,
                    "preceding_paragraph_index": preceding,
                    "following_paragraph_index": following,
                    "preceding_paragraph_content": preceding_content,
                    "following_paragraph_content": following_content,
                    "header": table_headers,
                    "parent_table_info": parent_info,
                    "table_format": self.table_config.table_format,
                },
                "parent_id": table_id,
                "context": context,
            }
            row_chunks.append(row_chunk)
        return row_chunks

    def _row_to_format(self, row, headers: List[str]) -> str:
        """根据配置将表格行转换为指定格式"""
        if self.table_config.table_format == "markdown":
            return self._row_to_markdown(row, headers)
        else:
            return self._row_to_html(row, headers)

    def _row_to_html(self, row, headers: List[str]) -> str:
        """生成单行HTML字符串"""
        cells = [cell.text.strip() for cell in row.cells]
        html = "<table border='1'><tr>"
        for cell in cells:
            html += f"<td>{cell if cell else '-'}</td>"
        html += "</tr></table>"
        return html

    def _row_to_markdown(self, row, headers: List[str]) -> str:
        """生成单行Markdown字符串"""
        # 修复：过滤空值，确保生成的markdown格式正确
        cells = []
        for cell in row.cells:
            text = cell.text.strip()
            if text:
                cells.append(text)
            else:
                cells.append("-")
        markdown = "| " + " | ".join(cells) + " |"
        return markdown

    def _get_cell_span(self, cell) -> Tuple[int, int]:
        # 检测合并单元格的行/列跨度
        tc = cell._tc
        rowspan = 1
        colspan = 1
        gridspan = tc.xpath(".//w:gridSpan")
        if gridspan:
            try:
                colspan = int(
                    gridspan[0].get(
                        "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val"
                    )
                )
            except Exception:
                colspan = 1
        vmerge = tc.xpath(".//w:vMerge")
        if vmerge:
            # 只在合并起始单元格上标注
            val = vmerge[0].get(
                "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val"
            )
            if val == "restart":
                # 统计向下合并了多少行（简单实现，复杂表格需更精细处理）
                rowspan = 2  # 这里只能简单标注2行，复杂情况需更复杂逻辑
        return rowspan, colspan

    def _get_cell_span_enhanced(self, cell) -> Tuple[int, int, bool, str]:
        """
        增强的合并单元格检测
        返回: (rowspan, colspan, is_merged_start, parent_text)
        """
        tc = cell._tc
        rowspan = 1
        colspan = 1
        is_merged_start = False
        parent_text = cell.text.strip()

        # 检测水平合并（colspan）
        gridspan = tc.xpath(".//w:gridSpan")
        if gridspan:
            try:
                colspan = int(
                    gridspan[0].get(
                        "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val"
                    )
                )
            except (ValueError, TypeError):
                colspan = 1

        # 检测垂直合并（rowspan）
        vmerge = tc.xpath(".//w:vMerge")
        if vmerge:
            val = vmerge[0].get(
                "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val"
            )
            if val == "restart":
                # 合并起始单元格
                is_merged_start = True
                # 计算实际合并的行数
                rowspan = self._calculate_rowspan(cell)
            else:
                # 被合并的单元格，不显示
                rowspan = 0

        return rowspan, colspan, is_merged_start, parent_text

    def _calculate_rowspan(self, cell) -> int:
        """计算单元格实际合并的行数"""
        # 简化实现：通过查找后续相同列的单元格来判断合并行数
        # 实际应用中可能需要更复杂的逻辑
        return 2  # 默认返回2，复杂情况需要更精细的处理

    def _iter_block_items(self, parent):
        # 依次遍历段落和表格
        for child in parent.element.body.iterchildren():
            if child.tag.endswith("tbl"):
                yield Table(child, parent)
            elif child.tag.endswith("p"):
                yield Paragraph(child, parent)

    @classmethod
    def can_handle(cls, ext: str) -> bool:
        return ext.lower() in ["doc", "docx"]

    @staticmethod
    def get_paragraph_content_by_index(
        paragraphs: Optional[List[str]], idx: Optional[int]
    ) -> Optional[str]:
        """
        根据段落索引获取段落内容，idx为1-based
        """
        if paragraphs is None or idx is None:
            return None
        if 1 <= idx <= len(paragraphs):
            return paragraphs[idx - 1]
        return None

    def _get_context_for_paragraph(self, paragraphs: List[str], idx: int) -> str:
        """
        获取指定段落的上下文（前后段落内容），idx为0-based。
        """
        prev_para = paragraphs[idx - 1] if idx > 0 else ""
        next_para = paragraphs[idx + 1] if idx < len(paragraphs) - 1 else ""
        context = f"上一段：{prev_para}。下一段：{next_para}"
        return context

    def _get_context_for_table(
        self, preceding_content: Optional[str], following_content: Optional[str]
    ) -> str:
        """
        获取表格的上下文内容（前后段落内容拼接）。
        """
        context = (
            f"上一段：{preceding_content or ''}。下一段：{following_content or ''}"
        )
        return context

    def _create_image_chunks(
        self, images: List[Dict], doc_id: str, all_chunks: List[Dict]
    ) -> List[Dict]:
        """创建图片块"""
        image_chunks = []

        for image_data in images:
            image_chunk = {
                "type": "image",
                "content": image_data["image_path"],
                "metadata": {
                    "doc_id": doc_id,
                    "image_filename": image_data["unique_filename"],
                    "original_filename": image_data["original_filename"],
                    "image_index": image_data["image_index"],
                    "processing_status": "pending",
                    "description": "",
                    "keywords": [],
                    "image_type": "",
                    "context_relation": "",
                    "key_information": [],
                },
                "context": "",
            }
            image_chunks.append(image_chunk)

        logger.info(f"创建了 {len(image_chunks)} 个图片块")
        return image_chunks

    async def _process_images_async(
        self, image_chunks: List[Dict], all_chunks: List[Dict]
    ):
        """异步处理图片分析"""
        try:
            # 为每个图片收集上下文
            for image_chunk in image_chunks:
                context = self.context_collector.collect_context_for_image(
                    image_chunk, all_chunks
                )
                # 方案一：保持完整的上下文结构，不立即格式化
                image_chunk["context"] = context

            # 并发分析所有图片
            tasks = []
            for image_chunk in image_chunks:
                task = self._analyze_single_image_async(image_chunk)
                tasks.append(task)

            # 等待所有分析完成
            await asyncio.gather(*tasks, return_exceptions=True)

            logger.info(f"图片分析完成，共处理 {len(image_chunks)} 张图片")

        except Exception as e:
            logger.error(f"图片异步处理失败: {str(e)}")

    async def _analyze_single_image_async(self, image_chunk: Dict):
        """异步分析单个图片"""
        try:
            image_path = image_chunk["content"]
            context = image_chunk["context"]

            # 方案一：传递完整的上下文字典，而不是字符串
            analysis_result = await self.image_analyzer.analyze_image_with_context(
                image_path, context
            )

            # 更新图片块
            image_chunk["metadata"]["processing_status"] = "completed"
            image_chunk["metadata"]["description"] = analysis_result.get(
                "description", ""
            )
            image_chunk["metadata"]["keywords"] = analysis_result.get("keywords", [])
            image_chunk["metadata"]["image_type"] = analysis_result.get(
                "image_type", ""
            )
            image_chunk["metadata"]["context_relation"] = analysis_result.get(
                "context_relation", ""
            )
            image_chunk["metadata"]["key_information"] = analysis_result.get(
                "key_information", []
            )

            logger.debug(f"图片分析完成: {image_path}")

        except Exception as e:
            logger.error(f"图片分析失败: {image_chunk['content']}, 错误: {str(e)}")
            image_chunk["metadata"]["processing_status"] = "failed"

    def _extract_table_data(self, table: Table) -> List[List[Dict]]:
        """提取表格数据"""
        rows = []
        for r_idx, row in enumerate(table.rows):
            row_cells = []
            for c_idx, cell in enumerate(row.cells):
                text = cell.text.strip()
                rowspan, colspan = self._get_cell_span(cell)
                cell_info = {
                    "text": text,
                    "rowspan": rowspan,
                    "colspan": colspan,
                    "row": r_idx,
                    "col": c_idx,
                }
                row_cells.append(cell_info)
            rows.append(row_cells)
        return rows

    def _get_merged_cells_info(self, table: Table) -> List[Dict]:
        """获取合并单元格信息"""
        merged_cells = []
        for r_idx, row in enumerate(table.rows):
            for c_idx, cell in enumerate(row.cells):
                rowspan, colspan = self._get_cell_span(cell)
                if rowspan > 1 or colspan > 1:
                    merged_cells.append(
                        {
                            "text": cell.text.strip(),
                            "rowspan": rowspan,
                            "colspan": colspan,
                            "row": r_idx,
                            "col": c_idx,
                        }
                    )
        return merged_cells

    def _build_header_mapping_for_doc(self, table: Table) -> Dict[int, str]:
        """
        为DOC/DOCX表格构建表头映射，处理合并单元格层次结构
        """
        header_mapping = {}
        merged_cells = self._get_merged_cells_info_enhanced(table)

        # 处理合并单元格
        for merge_info in merged_cells:
            if merge_info["is_merged_start"]:
                parent_text = merge_info["text"]
                start_col = merge_info["col"]
                colspan = merge_info["colspan"]

                # 为合并单元格的子列分配表头
                for col_offset in range(colspan):
                    col = start_col + col_offset
                    if col < len(table.rows[0].cells):
                        # 获取子列的表头信息
                        child_header = self._get_child_header_for_doc(
                            table, col, parent_text
                        )
                        header_mapping[col] = child_header

        # 处理未合并的列
        for col in range(len(table.rows[0].cells)):
            if col not in header_mapping:
                header = self._get_single_column_header_for_doc(table, col)
                header_mapping[col] = header

        return header_mapping

    def _get_merged_cells_info_enhanced(self, table: Table) -> List[Dict]:
        """获取增强的合并单元格信息"""
        merged_cells = []
        for r_idx, row in enumerate(table.rows):
            for c_idx, cell in enumerate(row.cells):
                rowspan, colspan, is_merged_start, parent_text = (
                    self._get_cell_span_enhanced(cell)
                )
                if rowspan > 1 or colspan > 1:
                    merged_cells.append(
                        {
                            "text": parent_text,
                            "rowspan": rowspan,
                            "colspan": colspan,
                            "row": r_idx,
                            "col": c_idx,
                            "is_merged_start": is_merged_start,
                        }
                    )
        return merged_cells

    def _get_cell_span_ultra_enhanced(
        self, cell, table: Table, row_idx: int, col_idx: int
    ) -> Tuple[int, int, bool, str, Dict]:
        """
        超增强的合并单元格检测
        返回: (rowspan, colspan, is_merged_start, parent_text, merge_info)
        """
        tc = cell._tc
        rowspan = 1
        colspan = 1
        is_merged_start = False
        parent_text = cell.text.strip()
        merge_info = {
            "row": row_idx,
            "col": col_idx,
            "text": parent_text,
            "rowspan": 1,
            "colspan": 1,
            "is_merged_start": False,
            "merge_type": "none",
        }

        # 检测水平合并（colspan）
        gridspan = tc.xpath(".//w:gridSpan")
        if gridspan:
            try:
                colspan = int(
                    gridspan[0].get(
                        "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val"
                    )
                )
                merge_info["colspan"] = colspan
                merge_info["merge_type"] = "horizontal"
            except (ValueError, TypeError):
                colspan = 1

        # 检测垂直合并（rowspan）- 通过遍历后续行来判断
        vmerge = tc.xpath(".//w:vMerge")
        if vmerge:
            val = vmerge[0].get(
                "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val"
            )
            if val == "restart":
                # 合并起始单元格
                is_merged_start = True
                rowspan = self._calculate_actual_rowspan(table, row_idx, col_idx)
                merge_info["rowspan"] = rowspan
                merge_info["is_merged_start"] = True
                merge_info["merge_type"] = "vertical" if colspan == 1 else "both"
            else:
                # 被合并的单元格，不显示
                rowspan = 0
                merge_info["rowspan"] = 0
                merge_info["merge_type"] = "merged"

        # 更新合并信息
        merge_info["rowspan"] = rowspan
        merge_info["colspan"] = colspan
        merge_info["is_merged_start"] = is_merged_start

        return rowspan, colspan, is_merged_start, parent_text, merge_info

    def _calculate_actual_rowspan(self, table: Table, start_row: int, col: int) -> int:
        """计算单元格实际合并的行数"""
        rowspan = 1
        # 从下一行开始检查，直到找到非空单元格或到达表格末尾
        for row_idx in range(start_row + 1, len(table.rows)):
            if col < len(table.rows[row_idx].cells):
                cell = table.rows[row_idx].cells[col]
                # 检查该单元格是否被垂直合并
                tc = cell._tc
                vmerge = tc.xpath(".//w:vMerge")
                if vmerge:
                    val = vmerge[0].get(
                        "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val"
                    )
                    if val == "continue":
                        rowspan += 1
                    else:
                        break
                else:
                    # 如果没有vMerge标记，检查单元格是否有内容
                    if cell.text.strip():
                        break
                    else:
                        rowspan += 1
            else:
                break
        return rowspan

    def _get_child_header_for_doc(
        self, table: Table, col: int, parent_text: str
    ) -> str:
        """获取合并单元格子列的表头"""
        # 获取该列在表头行的所有非空值
        header_parts = []
        for row_idx, row in enumerate(table.rows):
            if col < len(row.cells):
                cell_value = row.cells[col].text.strip()
                if cell_value:
                    header_parts.append(cell_value)

        # 构建层次结构表头
        if header_parts:
            if parent_text not in header_parts:
                header_parts.insert(0, parent_text)
            return "/".join(header_parts)
        else:
            return parent_text

    def _get_single_column_header_for_doc(self, table: Table, col: int) -> str:
        """获取单列的表头"""
        header_parts = []
        for row_idx, row in enumerate(table.rows):
            if col < len(row.cells):
                cell_value = row.cells[col].text.strip()
                if cell_value:
                    header_parts.append(cell_value)

        return "/".join(header_parts) if header_parts else ""

    def _detect_header_rows_smart(self, table: Table) -> int:
        """智能表头行检测，基于多种特征"""
        if not table.rows:
            return 0

        # 使用多种方法检测表头行数
        methods = [
            self._detect_header_rows_by_merge_enhanced,
            self._detect_header_rows_by_content_pattern,
            self._detect_header_rows_by_structure_enhanced,
        ]

        results = []
        for method in methods:
            try:
                result = method(table)
                if result > 0:
                    results.append(result)
            except Exception:
                continue

        # 使用投票机制确定最终结果
        if results:
            # 取众数，如果没有众数则取中位数
            from collections import Counter

            counter = Counter(results)
            most_common = counter.most_common(1)
            if most_common[0][1] > 1:  # 如果有多个相同的结果
                return most_common[0][0]
            else:
                return sorted(results)[len(results) // 2]  # 中位数

        return 1  # 默认返回1

    def _detect_header_rows_by_merge_enhanced(self, table: Table) -> int:
        """增强的基于合并单元格分布检测表头行"""
        if not table.rows:
            return 0

        # 统计每行的合并单元格数量和类型
        merge_stats = []
        for row_idx, row in enumerate(table.rows):
            horizontal_merges = 0
            vertical_merges = 0
            total_merges = 0

            for col_idx, cell in enumerate(row.cells):
                _, _, _, _, merge_info = self._get_cell_span_ultra_enhanced(
                    cell, table, row_idx, col_idx
                )

                if merge_info["merge_type"] in ["horizontal", "both"]:
                    horizontal_merges += 1
                if merge_info["merge_type"] in ["vertical", "both"]:
                    vertical_merges += 1
                if merge_info["merge_type"] != "none":
                    total_merges += 1

            merge_stats.append(
                {
                    "horizontal": horizontal_merges,
                    "vertical": vertical_merges,
                    "total": total_merges,
                }
            )

        # 检测表头行
        header_rows = 0
        max_header_rows = min(3, len(table.rows))

        for row_idx in range(max_header_rows):
            stats = merge_stats[row_idx]
            # 如果水平合并较多，可能是表头行
            if stats["horizontal"] > 0 or stats["total"] > 0:
                header_rows += 1
            else:
                break

        return header_rows if header_rows > 0 else 1

    def _detect_header_rows_by_content_pattern(self, table: Table) -> int:
        """基于内容模式检测表头行"""
        if not table.rows:
            return 0

        header_rows = 0
        max_header_rows = min(3, len(table.rows))

        for row_idx in range(max_header_rows):
            row = table.rows[row_idx]
            if self._is_header_row_by_content_pattern(row, row_idx):
                header_rows += 1
            else:
                break

        return header_rows if header_rows > 0 else 1

    def _is_header_row_by_content_pattern(self, row, row_idx: int) -> bool:
        """基于内容模式判断是否为表头行"""
        # 检查是否包含常见的表头关键词
        header_keywords = [
            "年度",
            "年份",
            "学校",
            "名称",
            "情况",
            "人数",
            "合计",
            "备注",
        ]

        cell_texts = [cell.text.strip() for cell in row.cells]
        keyword_count = 0

        for text in cell_texts:
            for keyword in header_keywords:
                if keyword in text:
                    keyword_count += 1
                    break

        # 如果超过30%的单元格包含表头关键词，可能是表头行
        if len(cell_texts) > 0 and keyword_count / len(cell_texts) > 0.3:
            return True

        # 检查是否包含数值（数据行通常包含数值）
        numeric_count = 0
        for text in cell_texts:
            if text and self._is_numeric(text):
                numeric_count += 1

        # 如果数值比例较低，可能是表头行
        if len(cell_texts) > 0 and numeric_count / len(cell_texts) < 0.3:
            return True

        return False

    def _is_numeric(self, text: str) -> bool:
        """判断文本是否为数值"""
        try:
            # 移除常见的非数值字符
            cleaned_text = (
                text.replace(",", "").replace("%", "").replace("+", "").replace("-", "")
            )
            float(cleaned_text)
            return True
        except (ValueError, TypeError):
            return False

    def _detect_header_rows_by_structure_enhanced(self, table: Table) -> int:
        """增强的基于行结构特征检测表头行"""
        if not table.rows:
            return 0

        header_rows = 0
        max_header_rows = min(3, len(table.rows))

        for row_idx in range(max_header_rows):
            row = table.rows[row_idx]
            if self._is_header_row_by_structure_enhanced(row, row_idx):
                header_rows += 1
            else:
                break

        return header_rows if header_rows > 0 else 1

    def _is_header_row_by_structure_enhanced(self, row, row_idx: int) -> bool:
        """增强的基于结构特征判断是否为表头行"""
        # 检查合并单元格分布
        merge_count = 0
        for col_idx, cell in enumerate(row.cells):
            _, _, _, _, merge_info = self._get_cell_span_ultra_enhanced(
                cell, row, row_idx, col_idx
            )
            if merge_info["merge_type"] != "none":
                merge_count += 1

        # 如果合并单元格数量较多，可能是表头行
        if merge_count > 0:
            return True

        # 检查单元格内容的特征
        empty_cells = 0
        total_cells = len(row.cells)
        for cell in row.cells:
            if not cell.text.strip():
                empty_cells += 1

        # 如果空单元格比例较低，可能是表头行
        if total_cells > 0 and empty_cells / total_cells < 0.5:
            return True

        return False

    def _detect_header_rows_for_doc(self, table: Table) -> int:
        """综合检测表头行数"""
        # 优先使用合并单元格检测
        header_rows_by_merge = self._detect_header_rows_by_merge(table)
        if header_rows_by_merge > 1:
            return header_rows_by_merge

        # 如果合并单元格不明显，使用结构特征检测
        header_rows_by_structure = self._detect_header_rows_by_structure(table)
        return header_rows_by_structure

    def _get_child_header_for_doc_fixed(
        self, table: Table, col: int, parent_text: str, header_rows: int
    ) -> str:
        """修复后的子列表头获取方法，只处理表头行"""
        # 只处理表头行，不包含数据行
        header_parts = []
        for row_idx in range(header_rows):
            if row_idx < len(table.rows) and col < len(table.rows[row_idx].cells):
                cell_value = table.rows[row_idx].cells[col].text.strip()
                if cell_value:
                    header_parts.append(cell_value)

        # 构建层次结构表头
        if header_parts:
            if parent_text not in header_parts:
                header_parts.insert(0, parent_text)
            return "/".join(header_parts)
        else:
            return parent_text

    def _get_single_column_header_for_doc_fixed(
        self, table: Table, col: int, header_rows: int
    ) -> str:
        """修复后的单列表头获取方法，只处理表头行"""
        header_parts = []
        for row_idx in range(header_rows):
            if row_idx < len(table.rows) and col < len(table.rows[row_idx].cells):
                cell_value = table.rows[row_idx].cells[col].text.strip()
                if cell_value:
                    header_parts.append(cell_value)

        return "/".join(header_parts) if header_parts else ""

    def _build_header_mapping_for_doc_fixed(self, table: Table) -> Dict[int, str]:
        """修复后的表头映射构建，正确处理表头行"""
        # 先检测表头行数
        header_rows = self._detect_header_rows_for_doc(table)

        header_mapping = {}
        merged_cells = self._get_merged_cells_info_enhanced(table)

        # 处理合并单元格
        for merge_info in merged_cells:
            if merge_info["is_merged_start"]:
                parent_text = merge_info["text"]
                start_col = merge_info["col"]
                colspan = merge_info["colspan"]

                # 为合并单元格的子列分配表头
                for col_offset in range(colspan):
                    col = start_col + col_offset
                    if col < len(table.rows[0].cells):
                        # 获取子列的表头信息
                        child_header = self._get_child_header_for_doc_fixed(
                            table, col, parent_text, header_rows
                        )
                        header_mapping[col] = child_header

        # 处理未合并的列
        for col in range(len(table.rows[0].cells)):
            if col not in header_mapping:
                header = self._get_single_column_header_for_doc_fixed(
                    table, col, header_rows
                )
                header_mapping[col] = header

        return header_mapping

    def _build_header_hierarchy_for_doc(self, table: Table) -> Dict[int, List[str]]:
        """构建表头层次结构，正确处理多级表头"""
        header_rows = self._detect_header_rows_smart(table)
        header_hierarchy = {}

        # 为每列构建表头层次
        for col in range(len(table.rows[0].cells)):
            column_headers = []

            # 收集该列在表头行中的内容
            for row_idx in range(header_rows):
                if row_idx < len(table.rows) and col < len(table.rows[row_idx].cells):
                    cell_text = table.rows[row_idx].cells[col].text.strip()
                    if cell_text:
                        column_headers.append(cell_text)

            header_hierarchy[col] = column_headers

        return header_hierarchy

    def _build_header_mapping_ultra_enhanced(self, table: Table) -> Dict[int, str]:
        """超增强的表头映射构建"""
        # 获取表头层次结构
        header_hierarchy = self._build_header_hierarchy_for_doc(table)

        # 获取合并单元格信息
        merged_cells = self._get_merged_cells_info_ultra_enhanced(table)

        header_mapping = {}

        # 处理合并单元格
        for merge_info in merged_cells:
            if merge_info["is_merged_start"]:
                parent_text = merge_info["text"]
                start_col = merge_info["col"]
                colspan = merge_info["colspan"]

                # 为合并单元格的子列分配表头
                for col_offset in range(colspan):
                    col = start_col + col_offset
                    if col < len(table.rows[0].cells):
                        # 获取子列的表头信息
                        child_header = self._get_child_header_ultra_enhanced(
                            table, col, parent_text, header_hierarchy
                        )
                        header_mapping[col] = child_header

        # 处理未合并的列
        for col in range(len(table.rows[0].cells)):
            if col not in header_mapping:
                header = self._get_single_column_header_ultra_enhanced(
                    table, col, header_hierarchy
                )
                header_mapping[col] = header

        return header_mapping

    def _get_merged_cells_info_ultra_enhanced(self, table: Table) -> List[Dict]:
        """获取超增强的合并单元格信息"""
        merged_cells = []
        for row_idx, row in enumerate(table.rows):
            for col_idx, cell in enumerate(row.cells):
                _, _, _, _, merge_info = self._get_cell_span_ultra_enhanced(
                    cell, table, row_idx, col_idx
                )
                if merge_info["merge_type"] != "none":
                    merged_cells.append(merge_info)
        return merged_cells

    def _get_child_header_ultra_enhanced(
        self,
        table: Table,
        col: int,
        parent_text: str,
        header_hierarchy: Dict[int, List[str]],
    ) -> str:
        """超增强的子列表头获取方法"""
        column_headers = header_hierarchy.get(col, [])

        # 构建层次结构表头
        if column_headers:
            if parent_text not in column_headers:
                column_headers.insert(0, parent_text)
            return "/".join(column_headers)
        else:
            return parent_text

    def _get_single_column_header_ultra_enhanced(
        self, table: Table, col: int, header_hierarchy: Dict[int, List[str]]
    ) -> str:
        """超增强的单列表头获取方法"""
        column_headers = header_hierarchy.get(col, [])
        return "/".join(column_headers) if column_headers else ""

    def _validate_header_structure(self, headers: List[str], table: Table) -> bool:
        """验证表头结构的合理性"""
        # 检查表头数量与列数是否匹配
        if len(headers) != len(table.rows[0].cells):
            return False

        # 检查表头是否为空（允许部分为空）
        empty_count = sum(1 for header in headers if not header.strip())
        if empty_count > len(headers) * 0.5:  # 如果超过50%为空，可能有问题
            return False

        # 检查表头层次是否合理
        for header in headers:
            if header and "/" in header:
                parts = header.split("/")
                if len(parts) > 3:  # 层次过多可能有问题
                    return False

        return True

    def _fallback_header_processing(self, table: Table) -> Dict[int, str]:
        """表头处理的回退机制"""
        logger.warning("使用表头处理回退机制")

        # 使用简化的表头处理
        headers = []
        for col in range(len(table.rows[0].cells)):
            if table.rows and col < len(table.rows[0].cells):
                header = table.rows[0].cells[col].text.strip()
                headers.append(header)
            else:
                headers.append("")

        header_mapping = {}
        for col, header in enumerate(headers):
            header_mapping[col] = header

        return header_mapping

    def _build_header_mapping_with_fallback(self, table: Table) -> Dict[int, str]:
        """带回退机制的表头映射构建"""
        try:
            # 尝试使用超增强的方法
            header_mapping = self._build_header_mapping_ultra_enhanced(table)

            # 验证结果
            headers = []
            for col in range(len(table.rows[0].cells)):
                header = header_mapping.get(col, "")
                headers.append(header)

            if self._validate_header_structure(headers, table):
                return header_mapping
            else:
                logger.warning("表头结构验证失败，使用回退机制")
                return self._fallback_header_processing(table)

        except Exception as e:
            logger.error(f"表头映射构建失败: {str(e)}，使用回退机制")
            return self._fallback_header_processing(table)


# 加载.env文件，获取API Key
load_dotenv()
ZHIPU_API_KEY = os.getenv("ZHIPUAI_API_KEY")


def build_prompt_for_chunk(chunk: dict, with_context: bool = True) -> str:
    """根据分块类型和元数据动态生成Prompt，支持有无上下文。"""
    chunk_type = chunk.get("type", "text")

    # 检查是否为分片chunk
    if chunk.get("metadata", {}).get("is_fragment"):
        chunk_type = "text_fragment"

    if with_context:
        from utils.chunk_prompts import STRUCTURED_PROMPTS_WITH_CONTEXT as PROMPTS
    else:
        from utils.chunk_prompts import STRUCTURED_PROMPTS as PROMPTS

    metadata = chunk.get("metadata", {})

    # 根据chunk类型构建不同的prompt参数
    if chunk_type == "text_fragment":
        prompt = PROMPTS.get(chunk_type, PROMPTS["text"]).format(
            content=chunk.get("content", ""),
            paragraph_index=metadata.get("paragraph_index", ""),
            fragment_index=metadata.get("fragment_index", ""),
            total_fragments=metadata.get("total_fragments", ""),
            original_content=metadata.get("original_content", ""),
            context=chunk.get("context", ""),
        )
    else:
        prompt = PROMPTS.get(chunk_type, PROMPTS["text"]).format(
            content=chunk.get("content", ""),
            paragraph_index=metadata.get("paragraph_index", ""),
            table_title=metadata.get("table_title", ""),
            sheet=metadata.get("sheet", ""),
            header=metadata.get("header", ""),
            parent_table_info=metadata.get("parent_table_info", ""),
            context=chunk.get("context", ""),
        )

    return prompt


def get_system_prompt_for_chunk(chunk: dict) -> str:
    """根据分块类型获取系统提示词。"""
    chunk_type = chunk.get("type", "text")

    # 检查是否为分片chunk
    if chunk.get("metadata", {}).get("is_fragment"):
        chunk_type = "text_fragment"

    return SYSTEM_PROMPTS.get(chunk_type, SYSTEM_PROMPTS["text"])


async def enhance_chunk(chunk: dict) -> dict:
    """调用智普API为分块生成description和keywords。"""
    prompt = build_prompt_for_chunk(chunk)
    system_prompt = get_system_prompt_for_chunk(chunk)
    response = await zhipu_complete_async(
        prompt=prompt,
        api_key=LLM_CONFIG["api_key"],
        model=LLM_CONFIG["model"],
        temperature=LLM_CONFIG["temperature"],
        timeout=LLM_CONFIG["timeout"],
        max_tokens=LLM_CONFIG["max_tokens"],
        system_prompt=system_prompt,
    )
    result = parse_json_response(response)
    chunk.setdefault("metadata", {})["description"] = result.get("description", "")
    chunk["metadata"]["keywords"] = result.get("keywords", [])
    return chunk


async def enhance_all_chunks(chunks: list[dict]) -> list[dict]:
    """批量异步增强所有分块，跳过已处理的图片块"""
    # 过滤出需要增强的分块（排除image类型）
    chunks_to_enhance = [chunk for chunk in chunks if chunk.get("type") != "image"]

    # 只对非图片分块进行增强
    tasks = [enhance_chunk(chunk) for chunk in chunks_to_enhance]
    enhanced_chunks = await asyncio.gather(*tasks)

    # 将图片块和增强后的分块合并
    image_chunks = [chunk for chunk in chunks if chunk.get("type") == "image"]
    return enhanced_chunks + image_chunks


# 示例主流程（可根据实际集成位置调整）
if __name__ == "__main__":
    # 示例：解析一个文档文件
    parser = DocFileParser()
    test_file = "test_data/sample.docx"  # 替换为实际文件路径

    if os.path.exists(test_file):
        chunks = parser.process(test_file)
        enhanced_chunks = asyncio.run(enhance_all_chunks(chunks))
        logger.info(f"处理完成，共生成 {len(enhanced_chunks)} 个增强分块")
    else:
        logger.info("测试文件不存在，跳过示例执行")
