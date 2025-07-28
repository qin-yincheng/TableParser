# xlsx_parser.py
# Excel文档解析器（待实现）

import os
from typing import List, Dict, Optional, Tuple, Any
import pandas as pd
from utils.logger import logger
from openpyxl import load_workbook
from openpyxl.worksheet.worksheet import Worksheet

from utils.zhipu_client import zhipu_complete_async, parse_json_response
from utils.chunk_prompts import (
    SYSTEM_PROMPTS,
    STRUCTURED_PROMPTS,
    STRUCTURED_PROMPTS_WITH_CONTEXT,
)
from utils.config import LLM_CONFIG
import asyncio


class XlsxFileParser:
    """Excel（.xlsx）文件解析器，输出分块结构，支持多Sheet和多表格。"""

    def parse(self, file_path: str) -> List[Dict]:
        """
        解析Excel文件，输出分块结构，每个分块包含type、content、metadata、context、parent_id。
        """
        logger.info(f"开始解析Excel文档: {file_path}")
        if not os.path.exists(file_path):
            logger.error(f"文件不存在: {file_path}")
            return []
        doc_id = os.path.basename(file_path)
        all_chunks: List[Dict] = []
        xls = None
        wb = None
        try:
            xls = pd.ExcelFile(file_path)
            wb = load_workbook(file_path, data_only=True)
            for sheet_name in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
                ws = wb[sheet_name]
                table_blocks = self._split_table_blocks(ws, df)
                merged_cells = self._get_merged_cells(ws)
                for block_idx, (start_row, end_row) in enumerate(table_blocks):
                    table_id = f"{sheet_name}_table_{block_idx+1}"
                    block_df = df.iloc[start_row : end_row + 1, :].copy()
                    block_df = self._drop_empty_cols(block_df)
                    if block_df.empty:
                        continue
                    header_rows = self._detect_header_rows(ws, start_row, end_row)
                    headers = self._get_multi_headers(block_df, header_rows)
                    table_html = self._df_to_html_multiheader(block_df, header_rows)
                    parent_table_info = self._get_parent_table_info(
                        headers, merged_cells
                    )
                    context = self._get_context_for_table(df, start_row, end_row)
                    table_chunk = {
                        "type": "table_full",
                        "content": table_html,
                        "metadata": {
                            "doc_id": doc_id,
                            "sheet": sheet_name,
                            "table_id": table_id,
                            "start_row": int(start_row),
                            "end_row": int(end_row),
                            "header_rows": header_rows,
                            "header": headers,
                            "merged_cells": merged_cells,
                            "parent_table_info": parent_table_info,
                        },
                        "context": context,
                        "parent_id": None,
                    }
                    all_chunks.append(table_chunk)
                    # 行级分块
                    if block_df.shape[0] > header_rows:
                        for r_idx in range(header_rows, block_df.shape[0]):
                            row_html = self._row_to_html(block_df.iloc[r_idx], headers)
                            row_context = self._get_context_for_row(
                                block_df, r_idx, header_rows
                            )
                            row_chunk = {
                                "type": "table_row",
                                "content": row_html,
                                "metadata": {
                                    "doc_id": doc_id,
                                    "sheet": sheet_name,
                                    "row": int(start_row + r_idx + 1),
                                    "table_id": table_id,
                                    "header": headers,
                                    "parent_table_info": parent_table_info,
                                },
                                "context": row_context,
                                "parent_id": table_id,
                            }
                            all_chunks.append(row_chunk)
        except Exception as e:
            logger.error(f"解析Excel文件出错: {file_path}, 错误: {str(e)}")
            return []
        finally:
            # 确保文件正确关闭
            if xls is not None:
                xls.close()
            if wb is not None:
                wb.close()

        # 为每个分块添加chunk_id
        for idx, chunk in enumerate(all_chunks):
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
                task = loop.create_task(enhance_all_chunks(all_chunks))
                enhanced_chunks = loop.run_until_complete(task)
            except RuntimeError:
                # 如果没有运行的事件循环，使用asyncio.run
                enhanced_chunks = asyncio.run(enhance_all_chunks(all_chunks))

            logger.info(f"成功增强 {len(enhanced_chunks)} 个分块")
            return enhanced_chunks
        except Exception as e:
            logger.error(f"LLM增强分块失败: {str(e)}")
            return all_chunks  # 如果增强失败，返回原始分块

    def _detect_header_rows(
        self, ws: Worksheet, start_row: int, end_row: int, max_header_rows: int = 3
    ) -> int:
        """启发式分析[start_row, end_row]区间内的表头行数，基于合并单元格分布。"""
        merge_counts = [0] * (end_row - start_row + 1)
        for mc in ws.merged_cells.ranges:
            for row in range(
                max(mc.min_row, start_row + 1), min(mc.max_row, end_row + 1) + 1
            ):
                merge_counts[row - (start_row + 1)] += 1
        header_rows = 0
        for i in range(min(max_header_rows, len(merge_counts))):
            if merge_counts[i] > 0:
                header_rows += 1
            else:
                break
        return header_rows if header_rows > 0 else 1

    def _split_table_blocks(
        self, ws: Worksheet, df: pd.DataFrame
    ) -> List[Tuple[int, int]]:
        """结合合并单元格、空行、非空密度智能分块。返回每个表格的起止行索引。"""
        blocks: List[Tuple[int, int]] = []
        in_block = False
        start = 0
        for idx, row in df.iterrows():
            has_data = row.notna().any()
            has_merge = self._row_has_merge(ws, idx + 1)
            if has_data or has_merge:
                if not in_block:
                    start = idx
                    in_block = True
            else:
                if in_block:
                    blocks.append((start, idx - 1))
                    in_block = False
        if in_block:
            blocks.append((start, df.shape[0] - 1))
        return blocks

    def _row_has_merge(self, ws: Worksheet, row_idx: int) -> bool:
        """判断某一行是否有合并单元格。"""
        for mc in ws.merged_cells.ranges:
            if mc.min_row <= row_idx <= mc.max_row:
                return True
        return False

    def _drop_empty_cols(self, df: pd.DataFrame) -> pd.DataFrame:
        """去除全空列。"""
        return df.dropna(axis=1, how="all")

    def _get_multi_headers(self, df: pd.DataFrame, header_rows: int) -> List[str]:
        """获取多级表头，拼接为单行表头。"""
        if df.shape[0] < header_rows:
            return []
        headers = []
        for col in range(df.shape[1]):
            parts = [
                str(df.iloc[h, col]) if pd.notna(df.iloc[h, col]) else ""
                for h in range(header_rows)
            ]
            header = "/".join([p for p in parts if p])
            headers.append(header)
        return headers

    def _df_to_html_multiheader(self, df: pd.DataFrame, header_rows: int) -> str:
        """将多级表头的DataFrame转为HTML表格。"""
        if df.shape[0] == 0 or header_rows == 0:
            return "<table></table>"
        headers = self._get_multi_headers(df, header_rows)
        html = ["<table border='1'>"]
        # 多级表头
        for h in range(header_rows):
            html.append(
                "<tr>"
                + "".join(
                    [
                        f"<th>{str(df.iloc[h, col]) if pd.notna(df.iloc[h, col]) else ''}</th>"
                        for col in range(df.shape[1])
                    ]
                )
                + "</tr>"
            )
        # 表体
        for i in range(header_rows, df.shape[0]):
            html.append(
                "<tr>"
                + "".join(
                    [f"<td>{str(x) if pd.notna(x) else ''}</td>" for x in df.iloc[i]]
                )
                + "</tr>"
            )
        html.append("</table>")
        return "\n".join(html)

    def _row_to_html(self, row: pd.Series, headers: List[str]) -> str:
        """将单行转为HTML表格。"""
        html = "<table border='1'><tr>"
        for cell in row:
            html += f"<td>{str(cell) if pd.notna(cell) else ''}</td>"
        html += "</tr></table>"
        return html

    def _get_merged_cells(self, ws: Worksheet) -> List[Dict[str, Any]]:
        """获取合并单元格信息。"""
        merged: List[Dict[str, Any]] = []
        for mc in ws.merged_cells.ranges:
            merged.append(
                {
                    "coord": str(mc.coord),
                    "min_row": mc.min_row,
                    "max_row": mc.max_row,
                    "min_col": mc.min_col,
                    "max_col": mc.max_col,
                }
            )
        return merged

    def _get_parent_table_info(
        self, headers: List[str], merged_cells: List[Dict[str, Any]]
    ) -> str:
        """生成父表格信息描述。"""
        return f"表头: {headers} 合并单元格: {merged_cells}"

    def _get_context_for_table(
        self, df: pd.DataFrame, start_row: int, end_row: int
    ) -> str:
        """获取表格的上下文内容（前后非空行内容）。"""
        prev_content = self._get_nonempty_row_content(df, start_row - 1)
        next_content = self._get_nonempty_row_content(df, end_row + 1)
        context = f"上一行：{prev_content or ''}。下一行：{next_content or ''}"
        return context

    def _get_context_for_row(
        self, df: pd.DataFrame, row_idx: int, header_rows: int
    ) -> str:
        """获取行的上下文内容（前后行内容，排除表头）。"""
        prev_content = (
            self._get_nonempty_row_content(df, row_idx - 1)
            if row_idx > header_rows
            else ""
        )
        next_content = (
            self._get_nonempty_row_content(df, row_idx + 1)
            if row_idx < df.shape[0] - 1
            else ""
        )
        context = f"上一行：{prev_content or ''}。下一行：{next_content or ''}"
        return context

    def _get_nonempty_row_content(
        self, df: pd.DataFrame, row_idx: int
    ) -> Optional[str]:
        """获取指定行的内容（非空则拼接为字符串）。"""
        if 0 <= row_idx < df.shape[0]:
            row = df.iloc[row_idx]
            if row.notna().any():
                return " | ".join([str(x) if pd.notna(x) else "" for x in row])
        return None

    @classmethod
    def can_handle(cls, ext: str) -> bool:
        return ext.lower() == "xlsx"


def build_prompt_for_chunk(chunk: dict, with_context: bool = True) -> str:
    """
    根据分块类型和元数据动态生成Prompt，支持有无上下文。
    """
    chunk_type = chunk.get("type", "table_full")
    if with_context:
        PROMPTS = STRUCTURED_PROMPTS_WITH_CONTEXT
    else:
        PROMPTS = STRUCTURED_PROMPTS
    metadata = chunk.get("metadata", {})
    prompt = PROMPTS.get(chunk_type, PROMPTS["table_full"]).format(
        content=chunk.get("content", ""),
        sheet=metadata.get("sheet", ""),
        header=metadata.get("header", ""),
        parent_table_info=metadata.get("parent_table_info", ""),
        context=chunk.get("context", ""),
        row=metadata.get("row", ""),
        table_title=metadata.get("table_title", ""),
        paragraph_index=metadata.get("paragraph_index", ""),
    )
    return prompt


def get_system_prompt_for_chunk(chunk: dict) -> str:
    """
    根据分块类型获取系统提示词。
    """
    chunk_type = chunk.get("type", "table_full")
    return SYSTEM_PROMPTS.get(chunk_type, SYSTEM_PROMPTS["table_full"])


async def enhance_chunk(chunk: dict) -> dict:
    """
    调用LLM为分块生成description和keywords。
    """
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


async def enhance_all_chunks(chunks: List[Dict]) -> List[Dict]:
    """
    批量异步增强所有分块。
    """
    tasks = [enhance_chunk(chunk) for chunk in chunks]
    return await asyncio.gather(*tasks)
