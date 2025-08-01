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
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"
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
                timeout=10
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
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"
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
                timeout=10
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
        "--convert-to", "docx",
        "--outdir", output_dir,
        doc_path
    ]
    
    try:
        # 执行转换命令
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60  # 60秒超时
        )
        
        if result.returncode != 0:
            error_msg = result.stderr.decode('utf-8', errors='ignore')
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
        self.fragment_manager = FragmentManager(fragment_config) if fragment_config else None
        self.table_config = fragment_config.table_processing if fragment_config else TableProcessingConfig()
        self.table_config = fragment_config.table_processing if fragment_config else TableProcessingConfig()

    def process(self, file_path: str) -> List[Dict]:
        logger.info(f"开始解析Word文档: {file_path}")
        if not os.path.exists(file_path):
            logger.error(f"文件不存在: {file_path}")
            return []
        _, ext = os.path.splitext(file_path)
        ext = ext.lower().lstrip(".")
        doc_id = os.path.basename(file_path)
        if ext == "docx":
            try:
                chunks = self._process_docx(file_path, doc_id)
            except Exception as e:
                logger.error(f"DOCX文件处理失败: {str(e)}")
                return []
        elif ext == "doc":
            try:
                chunks = self._process_doc(file_path, doc_id)
            except (LibreOfficeNotFoundError, ConversionError, ConversionTimeoutError) as e:
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

    def _process_docx(self, file_path: str, doc_id: str) -> List[Dict]:
        """解析DOCX文件，提取段落和表格内容"""
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
            for idx, block in enumerate(block_items):
                if isinstance(block, Paragraph):
                    if block.text.strip():
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
            return all_chunks
        except ImportError:
            logger.error("未安装python-docx库，无法解析DOCX文件")
            raise
        except Exception as e:
            logger.error(f"解析DOCX文件出错: {file_path}, 错误: {str(e)}")
            raise

    def _process_doc(self, file_path: str, doc_id: str) -> List[Dict]:
        """使用LibreOffice转换DOC文件为DOCX，然后解析"""
        docx_path = None
        try:
            # 使用LibreOffice将DOC文件转换为DOCX
            docx_path = convert_doc_to_docx(file_path)
            # 使用现有的DOCX解析逻辑
            chunks = self._process_docx(docx_path, doc_id)
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
        table_content, table_headers, merged_cells = self._convert_table_to_format(table)
        
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
                table, doc_id, table_id, preceding, following, 
                preceding_content, following_content, table_headers, parent_info, context
            )
            all_chunks.extend(row_chunks)
        
        return all_chunks

    def _convert_table_to_format(self, table: Table) -> Tuple[str, List[str], List[Dict]]:
        """根据配置将表格转换为指定格式"""
        if self.table_config.table_format == "markdown":
            return self._table_to_markdown_with_merge(table)
        else:
            return self._table_to_html_with_merge(table)

    def _table_to_html_with_merge(self, table: Table) -> Tuple[str, List[str], List[Dict]]:
        """
        生成带合并信息的HTML表格和合并单元格元数据
        返回: (html字符串, headers, merged_cells)
        """
        rows = []
        merged_cells = []
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
                if rowspan > 1 or colspan > 1:
                    merged_cells.append(cell_info)
                row_cells.append(cell_info)
            rows.append(row_cells)
        if not rows:
            return "<table></table>", [], merged_cells
        headers = [cell["text"] for cell in rows[0]]
        html = ["<table border='1'>"]
        # 表头
        html.append(
            "<tr>" + "".join([f"<th>{cell['text']}</th>" for cell in rows[0]]) + "</tr>"
        )
        # 表体
        for row in rows[1:]:
            html.append(
                "<tr>"
                + "".join(
                    [
                        f"<td{' rowspan=\"'+str(cell['rowspan'])+'\"' if cell['rowspan']>1 else ''}{' colspan=\"'+str(cell['colspan'])+'\"' if cell['colspan']>1 else ''}>{cell['text']}</td>"
                        for cell in row
                    ]
                )
                + "</tr>"
            )
        html.append("</table>")
        return "\n".join(html), headers, merged_cells

    def _table_to_markdown_with_merge(self, table: Table) -> Tuple[str, List[str], List[Dict]]:
        """
        生成带合并信息的Markdown表格和合并单元格元数据
        返回: (markdown字符串, headers, merged_cells)
        """
        rows = []
        merged_cells = []
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
                if rowspan > 1 or colspan > 1:
                    merged_cells.append(cell_info)
                row_cells.append(cell_info)
            rows.append(row_cells)
        
        if not rows:
            return "", [], merged_cells
        
        headers = [cell["text"] for cell in rows[0]]
        markdown_lines = []
        
        # 表头
        header_row = "| " + " | ".join([cell["text"] for cell in rows[0]]) + " |"
        markdown_lines.append(header_row)
        
        # 分隔线
        separator_row = "| " + " | ".join(["---"] * len(rows[0])) + " |"
        markdown_lines.append(separator_row)
        
        # 表体
        for row in rows[1:]:
            data_row = "| " + " | ".join([cell["text"] for cell in row]) + " |"
            markdown_lines.append(data_row)
        
        return "\n".join(markdown_lines), headers, merged_cells

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
        context: str
    ) -> List[Dict]:
        """生成表格行分块"""
        row_chunks = []
        for r_idx, row in enumerate(table.rows):
            if r_idx == 0:
                continue  # 跳过表头
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
            html += f"<td>{cell}</td>"
        html += "</tr></table>"
        return html

    def _row_to_markdown(self, row, headers: List[str]) -> str:
        """生成单行Markdown字符串"""
        cells = [cell.text.strip() for cell in row.cells]
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
    """批量异步增强所有分块。"""
    tasks = [enhance_chunk(chunk) for chunk in chunks]
    return await asyncio.gather(*tasks)


# 示例主流程（可根据实际集成位置调整）
if __name__ == "__main__":
    # 假设chunks为已解析的分块列表
    if "chunks" in globals():
        enhanced_chunks = asyncio.run(enhance_all_chunks(chunks))
        # enhanced_chunks 现在每个分块都带有 description 和 keywords，可保存或后续处理
