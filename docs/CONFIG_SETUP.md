# 配置设置说明

## 环境变量配置

在项目根目录创建 `.env` 文件，包含以下配置：

### LLM配置
```bash
# LLM配置
LLM_BINDING=openai
LLM_MODEL=glm-4-plus
LLM_BINDING_API_KEY=your_llm_api_key_here
LLM_BINDING_HOST=https://open.bigmodel.cn/api/paas/v4
```

### 嵌入模型配置
```bash
# 嵌入模型配置
EMBEDDING_BINDING=openai
EMBEDDING_MODEL=embedding-3
EMBEDDING_DIM=2048
EMBEDDING_BINDING_API_KEY=57610fba9f9546b8a6f096aa607c2965.9z8WvkhfcCEgZIs1
EMBEDDING_BINDING_HOST=https://open.bigmodel.cn/api/paas/v4
```

### 其他配置
```bash
# 其他配置
TIMEOUT=60
TEMPERATURE=0
MAX_ASYNC=4
MAX_TOKENS=2048
ENABLE_LLM_CACHE=false
ENABLE_LLM_CACHE_FOR_EXTRACT=false
```

## 测试配置

运行以下命令测试配置是否正确：

```bash
python test_embedding.py
```

这将测试：
1. 嵌入模型配置是否正确
2. 单个文本向量化是否正常
3. 分块向量化是否正常
4. 批量向量化是否正常

## 使用示例

```python
from main_processor import process_single_document
import asyncio

# 处理单个文档
result = asyncio.run(process_single_document("test_data/testData.docx", kb_id=1))
print(result)
```

## 注意事项

1. 确保API密钥正确配置
2. 确保网络连接正常
3. 如果向量化失败，检查API配额和限制
4. 向量维度为2048，确保Weaviate配置支持此维度 