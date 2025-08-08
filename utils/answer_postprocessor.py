"""
答案后处理器：当答案中包含图片引用(JSON)代码块时，
解析本地图片路径，将其转换为可渲染的内联 data URI，
并将预览片段追加到答案末尾（不修改原有 JSON 文本）。
"""

from __future__ import annotations

import base64
import json
import mimetypes
import os
import re
from pathlib import Path
from typing import Dict, Optional


# 匹配 ```json ... ``` 代码块，捕获首个合法 JSON 对象
_JSON_BLOCK_RE = re.compile(r"```json\s*(\{[\s\S]*?\})\s*```", re.IGNORECASE)


def _read_file_as_data_uri(
    image_path: Path, fallback_mime: str = "image/png"
) -> Optional[str]:
    """读取本地文件为 data URI 字符串。

    Args:
        image_path: 图片路径
        fallback_mime: 无法识别时的默认 MIME 类型

    Returns:
        data URI 字符串或 None
    """
    try:
        mime, _ = mimetypes.guess_type(str(image_path))
        mime = mime or fallback_mime
        data = image_path.read_bytes()
        encoded = base64.b64encode(data).decode("utf-8")
        return f"data:{mime};base64,{encoded}"
    except Exception:
        return None


def _extract_first_json_from_answer(answer: str) -> Optional[Dict]:
    """从答案中提取首个 ```json ... ``` 代码块并解析为字典。"""
    if not answer:
        return None
    m = _JSON_BLOCK_RE.search(answer)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except Exception:
        return None


def format_answer_with_images_if_json(
    result: Dict,
    *,
    max_images: int = 1,
    max_bytes: Optional[int] = None,
    image_width_px: int = 720,
) -> Dict:
    """仅当答案中存在图片引用 JSON 时才进行图片渲染追加。

    策略：
    - 解析答案末尾的 JSON 代码块，读取 images[0].path
    - 校验文件存在；可选大小限制；转换为 data URI
    - 将预览 <img> 片段追加到答案末尾

    Args:
        result: 问答返回结果字典
        max_images: 最多渲染图片数量（当前仅取 1）
        max_bytes: 单图体积上限（字节）。None 表示不限制
        image_width_px: 预览宽度（像素）

    Returns:
        新的结果字典（浅拷贝），answer 末尾可能追加图片预览 HTML
    """
    answer = (result or {}).get("answer") or ""
    payload = _extract_first_json_from_answer(answer)
    if not payload:
        return result

    images = payload.get("images")
    if not isinstance(images, list) or not images:
        return result

    # 仅处理第一张
    first = images[0]
    if not isinstance(first, dict):
        return result

    raw_path = (first.get("path") or "").replace("\\", "/").strip()
    if not raw_path:
        return result

    # 解析为绝对路径（相对路径基于当前工作目录）
    path_obj = Path(raw_path)
    if not path_obj.is_absolute():
        path_obj = (Path.cwd() / path_obj).resolve()

    if not path_obj.exists() or not path_obj.is_file():
        return result

    # 可选体积限制
    if isinstance(max_bytes, int) and max_bytes > 0:
        try:
            if path_obj.stat().st_size > max_bytes:
                return result
        except Exception:
            # stat 失败则忽略体积检查
            pass

    data_uri = _read_file_as_data_uri(path_obj)
    if not data_uri:
        return result

    # 只在答案末尾追加预览，保持 JSON 原样，避免破坏可解析性
    html = (
        "\n\n<p>图片预览：</p>\n"
        f'<div><img src="{data_uri}" alt="{raw_path}" style="max-width:100%;width:{image_width_px}px" /></div>'
    )

    new_result = dict(result)
    new_result["answer"] = answer + html
    # 记录被选中的图片路径（非 base64），便于审计/前端复用
    meta = dict(new_result.get("metadata") or {})
    selected = list(meta.get("selected_images") or [])
    selected.append(raw_path)
    meta["selected_images"] = selected[:max_images]
    new_result["metadata"] = meta

    return new_result
