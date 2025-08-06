# chunk_prompts.py
"""
分块语义增强Prompt模板，适用于RAG系统的text/table_full/table_row三类分块。
包含系统提示词、结构化输出Prompt、内容分析模板，支持上下文和元数据动态插入。
"""

from typing import Dict

# 系统提示词（按分块类型）
SYSTEM_PROMPTS: Dict[str, str] = {
    "text": "你是一名专业的内容分析师，请对下方文本内容进行简明、准确的分析和总结。",
    "text_fragment": "你是一名专业的内容分析师，请对下方文本分片内容进行简明、准确的分析和总结，注意这是完整段落的一部分。",
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
    "text_fragment": (
        "请用简洁准确的语言总结第{paragraph_index}段文本的分片内容（分片{fragment_index}/{total_fragments}），输出如下JSON结构：\n"
        "{{\n"
        '  "description": "高度概括该分片的主要内容和语义要点，注意这是完整段落的一部分",\n'
        '  "keywords": ["关键词1", "关键词2", "关键词3"]\n'
        "}}\n"
        "原始段落内容：{original_content}\n"
        "分片内容：\n{content}\n"
        "只输出JSON，不要其他内容。"
    ),
    "table_full": (
        "分析表格内容并生成详细的检索描述。\n\n"
        "表格信息：\n"
        "- 表名：{table_title}\n"
        "- Sheet：{sheet}\n"
        "- 表头：{header}\n"
        "- 内容：{content}\n\n"
        "要求生成包含以下要素的描述：\n"
        "1. 表格主题和数据类型\n"
        "2. 具体的列名、行名、关键数值\n"
        "3. 时间范围、地域范围、行业范围（如适用）\n"
        "4. 数据特征：最大值、最小值、变化趋势\n"
        "5. 用户可能的查询意图和表达方式\n"
        "6. 相关的同义词和术语\n\n"
        "输出JSON格式：\n"
        "{{\n"
        '  "description": "详细描述表格内容，包含具体指标、数值范围、适用场景，便于用户查询匹配",\n'
        '  "keywords": ["主题词", "指标名", "时间词", "地区词", "数值词", "查询词", "同义词"]\n'
        "}}\n"
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
    "text_fragment": (
        "请结合上下文，用简洁准确的语言总结第{paragraph_index}段文本的分片内容（分片{fragment_index}/{total_fragments}），必要时补充上下文关键信息，输出如下JSON结构：\n"
        "{{\n"
        '  "description": "高度概括该分片的主要内容和语义要点，注意这是完整段落的一部分，必要时结合上下文补充信息",\n'
        '  "keywords": ["关键词1", "关键词2", "关键词3"]\n'
        "}}\n"
        "上下文内容：{context}\n"
        "原始段落内容：{original_content}\n"
        "分片内容：\n{content}\n"
        "只输出JSON，不要其他内容。"
    ),
    "table_full": (
        "分析表格内容并生成高质量的检索描述，确保用户查询时能精准匹配。\n\n"
        "表格信息：\n"
        "- 标题：{table_title}\n"
        "- Sheet：{sheet}\n"
        "- 表头：{header}\n"
        "- 内容：{content}\n"
        "- 上下文：{context}\n\n"
        "优化要求：\n"
        "1. **多维度描述**：从数据内容、业务场景、时间维度、地域维度、行业领域等多角度描述\n"
        "2. **关键数据突出**：明确提及重要数值、时间范围、地区名称、指标名称\n"
        "3. **查询意图预测**：预测用户可能的提问方式，如\"哪个地区最高\"、\"什么时候开始\"、\"如何变化\"等\n"
        "4. **同义词覆盖**：包含专业术语的通俗表达、简称、全称、相关概念\n"
        "5. **场景化表述**：描述表格适用的分析场景、决策支持、研究用途\n"
        "6. **数据特征强化**：描述数据的分布特点、异常值、趋势模式\n\n"
        "生成原则：\n"
        "- description长度控制在150-300字，信息密度高\n"
        "- 使用自然语言，避免生硬的技术表述\n"
        "- 包含用户可能使用的口语化查询\n"
        "- 重点突出可查询的具体信息点\n\n"
        "输出JSON格式：\n"
        "{{\n"
        '  "description": "结合表格主题+核心指标+时空范围+数据特征+查询场景的综合描述，包含用户可能的各种查询表述",\n'
        '  "keywords": ["核心主题词", "具体指标名", "时间关键词", "地区/行业名", "数值特征", "查询动词", "同义表达", "场景词汇"]\n'
        "}}\n"
        "只输出JSON，不要其他内容。"
    ),
    "table_row": (
        "分析表格行数据并生成检索友好的描述。\n\n"
        "行数据信息：\n"
        "- 表名：{table_title}\n"
        "- Sheet：{sheet}\n"
        "- 表头：{header}\n"
        "- 父表格摘要：{parent_table_info}\n"
        "- 行内容：{content}\n"
        "- 上下文：{context}\n\n"
        "要求：\n"
        "1. 结合表头解释每列数据的具体含义\n"
        "2. 突出该行的关键数值和特征\n"
        "3. 说明该行在整体数据中的位置和意义\n"
        "4. 包含用户可能查询该行的具体问法\n"
        "5. 提供相关的对比和分析角度\n\n"
        "输出JSON格式：\n"
        "{{\n"
        '  "description": "详细描述该行数据的具体内容、数值特征和查询价值，便于精确检索",\n'
        '  "keywords": ["行标识词", "数值关键词", "比较词", "查询词"]\n'
        "}}\n"
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
