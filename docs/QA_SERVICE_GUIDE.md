# 问答服务使用指南

## 概述

问答服务是基于RAG（检索增强生成）技术的智能问答系统，能够基于文档内容回答用户问题。系统采用简化的4步流程，确保高效可靠的问答体验。

## 核心功能

### 1. 智能问答流程
- **语义检索**: 基于问题向量化进行相似度搜索
- **答案融合**: 去重、排序、筛选最相关结果
- **构建上下文**: 格式化检索结果作为答案上下文
- **生成答案**: 基于上下文生成准确答案

### 2. 支持的分块类型
- **text**: 文本段落
- **table_full**: 完整表格
- **table_row**: 表格行数据

## 快速开始

### 1. 基础使用

```python
import asyncio
from qa_service import QAService

async def basic_qa():
    qa_service = QAService()
    
    try:
        result = await qa_service.answer_question(
            question="Cedar 大学在2005年招收了多少名本科新生？",
            kb_id=1
        )
        
        if result.get("success"):
            print(f"答案: {result.get('answer')}")
            print(f"来源数: {result.get('metadata', {}).get('total_sources')}")
        else:
            print(f"错误: {result.get('error')}")
            
    finally:
        qa_service.close()

# 运行
asyncio.run(basic_qa())
```

### 2. 交互式问答

```bash
python qa_demo.py
```

选择模式1进行交互式问答，或选择模式2进行批量演示。

### 3. 完整测试

```bash
python test_qa_service.py
```

## API 参考

### QAService 类

#### 初始化
```python
qa_service = QAService()
```

#### 主要方法

##### answer_question()
```python
async def answer_question(
    self,
    question: str,
    kb_id: int,
) -> Dict[str, Union[bool, str, List[Dict]]]
```

**参数:**
- `question`: 用户问题
- `kb_id`: 知识库ID

**返回值:**
```python
{
    "success": True,
    "question": "用户问题",
    "answer": "生成的答案",
    "sources": [
        {
            "content": "来源内容片段",
            "chunk_type": "分块类型",
            "similarity_score": 0.15,  # 距离分数，越小越相似
            "source_info": {...}
        }
    ],
    "metadata": {
        "total_sources": 5
    }
}
```

## 配置参数

### 默认配置
- `max_context_length`: 4000 (上下文最大长度)
- `max_results`: 8 (最大检索结果数)
- `temperature`: 0.3 (答案生成温度)
- `max_tokens`: 1000 (答案最大长度)

## 错误处理

### 常见错误类型

1. **问题格式无效**
   - 原因: 问题为空或格式不正确
   - 解决: 检查问题内容

2. **未找到相关文档**
   - 原因: 知识库中没有相关内容
   - 解决: 尝试重新表述问题或检查知识库

3. **答案生成失败**
   - 原因: 模型调用失败
   - 解决: 检查网络连接和API配置

### 错误响应格式
```python
{
    "success": False,
    "error": "错误描述信息"
}
```

## 相似度分数说明

### 分数含义
- **距离分数**: 向量检索返回的是距离分数
- **越小越相似**: 分数越小表示内容与问题越相似
- **排序方式**: 按升序排列，取最相似的结果

### 分数范围
- 通常范围: 0.0 - 2.0
- 优秀匹配: < 0.3
- 良好匹配: 0.3 - 0.7
- 一般匹配: > 0.7

## 性能优化

### 1. 上下文长度控制
- 默认4000字符，可根据需要调整
- 过长上下文可能影响生成质量
- 过短上下文可能信息不足

### 2. 检索结果数量
- 默认8个结果，可根据需要调整
- 更多结果提供更丰富上下文
- 但会增加处理时间

### 3. 批量处理
```python
# 批量问答示例
questions = ["问题1", "问题2", "问题3"]
results = []

for question in questions:
    result = await qa_service.answer_question(question, kb_id=1)
    results.append(result)
    await asyncio.sleep(1)  # 避免API调用过于频繁
```

## 最佳实践

### 1. 问题表述
- 使用清晰、具体的问题
- 避免过于复杂的问题
- 对于表格数据，明确指定查询目标

### 2. 资源管理
- 及时调用 `close()` 方法释放资源
- 使用 `try-finally` 确保资源清理

### 3. 错误处理
- 始终检查返回结果的 `success` 字段
- 记录错误信息以便调试
- 实现重试机制处理临时错误

### 4. 性能监控
- 监控问答响应时间
- 跟踪成功率
- 分析相似度分数分布

## 扩展功能

### 1. 自定义上下文长度
```python
qa_service = QAService()
qa_service.max_context_length = 6000  # 自定义上下文长度
```

### 2. 自定义检索结果数量
```python
qa_service = QAService()
qa_service.max_results = 12  # 自定义检索结果数量
```

### 3. 自定义提示词
可以修改 `_generate_answer()` 方法中的提示词模板。

## 故障排除

### 1. 导入错误
确保安装了所有依赖包：
```bash
pip install zhipuai tenacity
```

### 2. 配置错误
检查配置文件中的API密钥和模型设置。

### 3. 网络问题
检查网络连接和API服务状态。

### 4. 内存问题
对于大量文档，考虑调整上下文长度和检索结果数量。

### 5. 相似度分数异常
- 检查向量数据库是否正常
- 验证嵌入模型配置
- 确认文档已正确向量化 