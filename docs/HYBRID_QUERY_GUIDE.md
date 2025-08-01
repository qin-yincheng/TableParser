# 混合查询功能使用指南

## 概述

混合查询（Hybrid Search）结合了文本搜索和向量搜索的优势，提供更精准的检索结果。本功能已经集成到现有的查询服务中，可以自动处理问题文本的向量化并进行混合检索。

## 功能特点

- **自动向量化**：问题文本自动转换为向量表示
- **混合检索**：结合文本匹配和语义相似度
- **可配置参数**：支持距离阈值、结果数量限制等
- **向后兼容**：现有代码无需修改即可使用

## 使用方法

### 1. 通过 QueryService 使用（推荐）

```python
from query_service import QueryService

# 初始化服务
query_service = QueryService()

# 执行混合查询
result = await query_service.query_by_semantic(
    question="什么是机器学习？",
    kb_id=1,
    limit=5
)

if result.get("success"):
    results = result.get("results", [])
    for item in results:
        print(f"分数: {item.get('score')}")
        print(f"内容: {item.get('properties', {}).get('content')}")
```

### 2. 直接使用 VectorService

```python
from vector_service import VectorService

# 初始化服务
vector_service = VectorService()

# 执行混合查询
results = vector_service.query_by_hybrid(
    kb_id=1,
    question="深度学习的基本原理是什么？",
    limit=3,
    distance_threshold=0.8
)

for item in results:
    print(f"ID: {item.get('id')}")
    print(f"分数: {item.get('score')}")
    print(f"内容: {item.get('properties', {}).get('content')}")
```

## 参数说明

### QueryService.query_by_semantic()

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| question | str | 是 | - | 用户问题文本 |
| kb_id | int | 是 | - | 知识库ID |
| limit | int | 否 | 10 | 返回结果数量限制 |
| distance_threshold | float | 否 | None | 距离阈值，超过此值的结果将被过滤 |

### VectorService.query_by_hybrid()

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| kb_id | int | 是 | - | 知识库ID |
| question | str | 是 | - | 问题文本 |
| limit | int | 否 | 10 | 返回结果数量限制 |
| distance_threshold | float | 否 | None | 距离阈值 |
| alpha | float | 否 | 0.7 | 混合比例（0-1之间） |

## 返回结果格式

### QueryService 返回格式

```python
{
    "success": True,
    "question": "用户问题",
    "kb_id": 1,
    "total_count": 5,
    "results": [
        {
            "id": "对象ID",
            "score": 0.85,
            "properties": {
                "doc_id": "文档ID",
                "chunk_id": "分块ID",
                "chunk_type": "分块类型",
                "content": "内容",
                "description": "描述",
                "keywords": ["关键词1", "关键词2"]
            }
        }
    ]
}
```

### VectorService 返回格式

```python
[
    {
        "id": "对象ID",
        "score": 0.85,
        "properties": {
            "doc_id": "文档ID",
            "chunk_id": "分块ID",
            "chunk_type": "分块类型",
            "content": "内容",
            "description": "描述",
            "keywords": ["关键词1", "关键词2"]
        }
    }
]
```

## 优势对比

### 混合查询 vs 纯向量查询

| 特性 | 混合查询 | 纯向量查询 |
|------|----------|------------|
| 文本匹配 | ✅ 支持 | ❌ 不支持 |
| 语义相似度 | ✅ 支持 | ✅ 支持 |
| 关键词匹配 | ✅ 支持 | ❌ 不支持 |
| 检索精度 | 更高 | 中等 |
| 处理速度 | 稍慢 | 较快 |

### 混合查询 vs 纯文本查询

| 特性 | 混合查询 | 纯文本查询 |
|------|----------|------------|
| 语义理解 | ✅ 支持 | ❌ 不支持 |
| 同义词匹配 | ✅ 支持 | ❌ 不支持 |
| 文本匹配 | ✅ 支持 | ✅ 支持 |
| 检索精度 | 更高 | 较低 |

## 使用建议

1. **默认使用混合查询**：对于大多数场景，混合查询提供更好的检索效果
2. **调整 alpha 参数**：根据数据特点调整文本和向量的权重比例
3. **设置距离阈值**：过滤低质量结果，提高检索精度
4. **监控性能**：混合查询比纯向量查询稍慢，注意性能监控

## 错误处理

常见错误及解决方案：

1. **向量化失败**
   - 检查网络连接
   - 验证API密钥配置
   - 确保问题文本不为空

2. **集合不存在**
   - 确认知识库ID正确
   - 检查集合是否已创建

3. **查询超时**
   - 减少limit参数
   - 检查网络连接
   - 考虑使用异步查询

## 示例代码

完整的使用示例请参考：
- `examples/hybrid_query_example.py` - 详细使用示例
- `tests/test_hybrid_query.py` - 功能测试代码

## 注意事项

1. 确保Weaviate服务正常运行
2. 检查embedding服务配置正确
3. 知识库数据已正确导入
4. 网络连接稳定

## 更新日志

- **v1.0.0**: 初始版本，支持基本的混合查询功能
- 自动向量化问题文本
- 集成到现有查询服务
- 提供完整的API文档 