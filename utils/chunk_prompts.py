# chunk_prompts.py
"""
分块语义增强Prompt模板，适用于RAG系统的text/table_full/table_row三类分块。
包含系统提示词、结构化输出Prompt、内容分析模板，支持上下文和元数据动态插入。
"""

from typing import Dict

# 系统提示词（按分块类型）
SYSTEM_PROMPTS: Dict[str, str] = {
    "text": "你是一名专业的内容分析师，请对下方文本内容进行简明、准确的分析和总结。",
    "table_full": "你是一名专业的数据分析师，请对下方表格内容进行详细、专业的分析和主题总结。",
    "table_row": "你是一名专业的数据分析师，请结合表头和父表格信息，对下方表格行数据进行简明、准确的分析和总结。",
    # "future_type": "..."
}

# 结构化输出Prompt（用于API调用生成description/keywords）
STRUCTURED_PROMPTS: Dict[str, str] = {
    "text": (
        "请用简洁准确的语言总结第{paragraph_index}段文本的核心信息，输出如下JSON结构：\n"
        "{{\n"
        '  "description": "高度概括该段文本的主要内容和语义要点",\n'
        '  "keywords": ["关键词1", "关键词2", "关键词3"]\n'
        "}}\n"
        "文本内容：\n{content}\n"
        "只输出JSON，不要其他内容。"
    ),
    "table_full": (
        "请用一句话高度概括下表（表名：{table_title}，Sheet：{sheet}）的主题和主要内容，输出如下JSON结构：\n"
        "{{\n"
        '  "description": "高度概括该表格的主题、主要内容",\n'
        '  "keywords": ["关键词1", "关键词2", "关键词3", "关键词4"]\n'
        "}}\n"
        "表头：{header}\n"
        "表格内容：\n{content}\n"
        "只输出JSON，不要其他内容。"
    ),
    "table_row": (
        "请结合表头和父表格信息，用简洁准确的语言总结该行数据的具体内容和语义，输出如下JSON结构：\n"
        "{{\n"
        '  "description": "高度概括该行数据的内容和语义要点",\n'
        '  "keywords": ["关键词1", "关键词2"]\n'
        "}}\n"
        "表头：{header}\n"
        "父表格摘要：{parent_table_info}\n"
        "行内容：{content}\n"
        "只输出JSON，不要其他内容。"
    ),
    # "future_type": "..."
}

# 带上下文的结构化输出Prompt
STRUCTURED_PROMPTS_WITH_CONTEXT: Dict[str, str] = {
    "text": (
        "请结合上下文，用简洁准确的语言总结第{paragraph_index}段文本的核心信息，必要时补充上下文关键信息，输出如下JSON结构：\n"
        "{{\n"
        '  "description": "高度概括该段文本的主要内容和语义要点，必要时结合上下文补充信息",\n'
        '  "keywords": ["关键词1", "关键词2", "关键词3"]\n'
        "}}\n"
        "上下文内容：{context}\n"
        "文本内容：{content}\n"
        "只输出JSON，不要其他内容。"
    ),
    "table_full": (
        "请结合上下文，用一句话高度概括下表（表名：{table_title}，Sheet：{sheet}）的主题和主要内容，必要时补充上下文关键信息，输出如下JSON结构：\n"
        "{{\n"
        '  "description": "高度概括该表格的主题、主要内容及其与上下文的关联",\n'
        '  "keywords": ["关键词1", "关键词2", "关键词3", "关键词4"]\n'
        "}}\n"
        "上下文内容：{context}\n"
        "表头：{header}\n"
        "表格内容：{content}\n"
        "只输出JSON，不要其他内容。"
    ),
    "table_row": (
        "请结合上下文和父表格（表名：{table_title}，Sheet：{sheet}）信息，用简洁准确的语言总结该行数据的具体内容和语义，必要时补充表头、父表格和上下文关键信息，输出如下JSON结构：\n"
        "{{\n"
        '  "description": "高度概括该行数据的内容和语义要点，必要时结合表头、父表格和上下文补充信息",\n'
        '  "keywords": ["关键词1", "关键词2"]\n'
        "}}\n"
        "上下文内容：{context}\n"
        "表头：{header}\n"
        "父表格摘要：{parent_table_info}\n"
        "行内容：{content}\n"
        "只输出JSON，不要其他内容。"
    ),
    # "future_type": "..."
}

# 分块内容分析Prompt（用于检索结果展示、摘要生成）
ANALYSIS_PROMPTS: Dict[str, str] = {
    "text": (
        "文本内容分析:\n"
        "段落索引: {paragraph_index}\n"
        "内容: {content}\n\n"
        "分析结果: {enhanced_caption}"
    ),
    "table_full": (
        "表格内容分析:\n"
        "表名: {table_title}\nSheet: {sheet}\n表头: {header}\n"
        "结构: {content}\n\n"
        "分析结果: {enhanced_caption}"
    ),
    "table_row": (
        "表格行内容分析:\n"
        "表名: {table_title}\nSheet: {sheet}\n表头: {header}\n"
        "父表格摘要: {parent_table_info}\n"
        "行数据: {content}\n\n"
        "分析结果: {enhanced_caption}"
    ),
    # "future_type": "..."
}

# 带上下文的内容分析Prompt
ANALYSIS_PROMPTS_WITH_CONTEXT: Dict[str, str] = {
    "text": (
        "文本内容分析（含上下文）:\n"
        "段落索引: {paragraph_index}\n"
        "上下文: {context}\n"
        "内容: {content}\n\n"
        "分析结果: {enhanced_caption}"
    ),
    "table_full": (
        "表格内容分析（含上下文）:\n"
        "表名: {table_title}\nSheet: {sheet}\n表头: {header}\n"
        "上下文: {context}\n"
        "结构: {content}\n\n"
        "分析结果: {enhanced_caption}"
    ),
    "table_row": (
        "表格行内容分析（含上下文）:\n"
        "表名: {table_title}\nSheet: {sheet}\n表头: {header}\n"
        "父表格摘要: {parent_table_info}\n"
        "上下文: {context}\n"
        "行数据: {content}\n\n"
        "分析结果: {enhanced_caption}"
    ),
    # "future_type": "..."
}
