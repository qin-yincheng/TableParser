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
    "image": "你是一名专业的图像分析师，擅长结合图像与文档上下文提取信息、总结图像含义。",
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
    "image": (
        "根据图像内容，生成结构化信息。\n\n"
        "图像路径：{image_path}\n\n"
        "要求返回以下JSON字段：\n"
        "{{\n"
        '  "description": "图像描述",\n'
        '  "keywords": ["关键词1", "关键词2", "关键词3"],\n'
        '  "image_type": "图片类型（如：图表、截图、插图等）",\n'
        '  "context_relation": "图像与文档的关系",\n'
        '  "key_information": ["关键信息1", "关键信息2"]\n'
        "}}\n"
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
        '3. **查询意图预测**：预测用户可能的提问方式，如"哪个地区最高"、"什么时候开始"、"如何变化"等\n'
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
    "image": (
        "深度分析图片内容并生成高质量的多维度检索描述，确保用户通过各种查询方式都能精准匹配。\n\n"
        "图像信息：\n"
        "- 图像路径：{image_path}\n"
        "- 文档上下文：{context}\n\n"
        "深度分析要求：\n"
        "1. **视觉内容全解析**：\n"
        "   - 主体识别：人物、物体、场景、品牌标识\n"
        "   - 数据提取：图表类型、数值、趋势、比例、排名\n"
        "   - 文字信息：标题、标签、注释、水印、说明文字\n"
        "   - 视觉特征：颜色主调、布局结构、设计风格\n"
        "2. **数据维度强化**（针对统计图表）：\n"
        "   - 准确提取所有数值、百分比、时间序列\n"
        "   - 描述数据趋势：上升/下降/波动/峰值/谷值\n"
        "   - 对比关系：最大/最小值、差异倍数、占比关系\n"
        "   - 异常特征：突变点、拐点、离群值\n"
        "3. **查询意图全覆盖**：\n"
        "   - 直接查询：\"显示...的图\"、\"关于...的图表\"\n"
        "   - 数据查询：\"最高的是\"、\"增长了多少\"、\"占比多少\"\n"
        "   - 对比查询：\"A和B的对比\"、\"哪个更高\"、\"差距多大\"\n"
        "   - 趋势查询：\"如何变化\"、\"什么趋势\"、\"拐点在哪\"\n"
        "   - 视觉查询：\"蓝色的图\"、\"饼图\"、\"流程图\"\n"
        "4. **语义扩展网络**：\n"
        "   - 专业术语的多种表达（如：营收/收入/销售额/营业收入）\n"
        "   - 图表类型的各种称呼（如：柱状图/条形图/bar chart）\n"
        "   - 口语化表达（如：\"那个对比图\"、\"增长的图\"）\n"
        "5. **场景化应用描述**：\n"
        "   - 业务用途：决策支持、报告展示、数据分析\n"
        "   - 适用场景：会议汇报、研究分析、教学说明\n"
        "   - 关联主题：所属章节、相关指标、影响因素\n"
        "6. **信息密度优化**：\n"
        "   - 优先描述可查询的具体信息点\n"
        "   - 包含独特标识符（如特定年份、公司名、产品名）\n"
        "   - 强调数据的业务含义而非单纯数值\n\n"
        "生成原则：\n"
        "- description长度200-400字，根据图片复杂度调整\n"
        "- 对数据密集型图表，重点描述数据洞察而非逐个列举\n"
        "- 使用\"该图显示...\"、\"从图中可以看出...\"等自然表达\n"
        "- 预埋用户的各种问答模式\n"
        "- 图文关联：明确说明图片如何支撑或补充文档内容\n\n"
        "输出JSON格式：\n"
        "{{\n"
        '  "description": "综合描述：图片类型+核心内容+关键数据/信息+视觉特征+业务含义+查询触发词的自然语言描述",\n'
        '  "keywords": ["图表类型", "主题词", "具体数值/指标", "时间/地点", "颜色/样式", "趋势词", "对比词", "业务术语", "同义词"],\n'
        '  "image_type": "具体类型（line_chart/bar_chart/pie_chart/flow_chart/mind_map/photo/screenshot/infographic/table_image/mixed）",\n'
        '  "data_insights": ["关键发现1：具体数值或趋势", "关键发现2：对比或异常", "关键发现3：业务含义"],\n'
        '  "visual_elements": ["主要颜色", "布局特征", "标注信息", "特殊标记"],\n'
        '  "context_relation": "图片与文档的关系：支撑论点/提供证据/总结概括/详细展开等",\n'
        '  "searchable_queries": ["可能的用户查询1", "可能的用户查询2", "可能的用户查询3"]\n'
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
    "image": (
        "图片内容分析:\n" "图片路径: {image_path}\n\n" "分析结果: {enhanced_caption}"
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
    "image": (
        "图片内容分析（含上下文）:\n"
        "图片路径: {image_path}\n"
        "文档上下文: {context}\n\n"
        "分析结果: {enhanced_caption}"
    ),
    # "future_type": "..."
}
