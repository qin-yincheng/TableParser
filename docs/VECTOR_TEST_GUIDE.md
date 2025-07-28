# 向量化加入库测试指南

本文档介绍如何使用向量化测试套件来验证文档解析结果到向量库的完整流程。

## 测试文件说明

### 1. 主要测试文件

- **`test_vector_integration.py`** - 完整的向量化集成测试
- **`test_vector_quick.py`** - 快速向量化功能测试
- **`test_vector_config.py`** - 测试配置管理
- **`run_vector_tests.py`** - 测试运行脚本

### 2. 测试数据文件

测试使用以下解析结果文件：
- `test_results/doc_parser_test_20250727_151620.json` - DOC文档解析结果
- `test_results/xlsx_parser_test_20250727_152437.json` - XLSX文档解析结果

## 测试模式

### 1. 快速测试 (Quick)
- 测试基本向量化功能
- 验证向量库基本操作
- 快速验证解析结果集成
- 适合开发调试

### 2. 完整测试 (Full)
- 测试完整的向量化流程
- 验证DOC和XLSX解析结果处理
- 测试混合文档类型处理
- 包含查询功能测试

### 3. 性能测试 (Performance)
- 测试大量数据的向量化性能
- 测量向量化和存储时间
- 测试查询性能
- 适合性能优化

## 使用方法

### 1. 运行快速测试
```bash
python run_vector_tests.py --mode quick
```

### 2. 运行完整测试
```bash
python run_vector_tests.py --mode full
```

### 3. 运行性能测试
```bash
python run_vector_tests.py --mode performance
```

### 4. 运行所有测试
```bash
python run_vector_tests.py --mode all
```

### 5. 详细输出模式
```bash
python run_vector_tests.py --mode full --verbose
```

## 测试内容

### 1. 向量化服务测试
- 单个文本向量化
- 批量文本向量化
- 不同类型分块的向量化（文本、表格）
- 向量化错误处理

### 2. 向量库服务测试
- 集合创建和删除
- 数据插入和查询
- 向量相似度查询
- 过滤条件查询

### 3. 解析结果集成测试
- DOC文档解析结果处理
- XLSX文档解析结果处理
- 混合文档类型处理
- 完整流程验证

### 4. 性能测试
- 批量向量化性能
- 批量存储性能
- 查询性能测试
- 内存使用监控

## 测试结果

### 1. 控制台输出
测试过程中会输出详细的执行信息：
```
开始测试: 向量化完整测试 (模式: full)
============================================================
1. 测试集合管理功能
集合管理功能测试完成
2. 测试DOC解析到向量化流程
处理文档: test_data/testData.docx, 分块数量: 46
开始测试10个分块的向量化
向量化完成: 10/10 成功, 耗时: 2.34秒
存储完成: 10/10 成功, 耗时: 1.23秒
测试结果已保存到: test_results/vector_integration_test/vector_test_doc_1703123456.json
```

### 2. 结果文件
测试结果保存在 `test_results/vector_integration_test/` 目录下：
- `vector_test_doc_*.json` - DOC测试结果
- `vector_test_xlsx_*.json` - XLSX测试结果
- `vector_test_mixed_*.json` - 混合测试结果

### 3. 结果格式
```json
{
  "test_time": "2025-01-27T15:30:45.123456",
  "doc_type": "doc",
  "total_chunks": 10,
  "vectorization_success": 10,
  "storage_success": 10,
  "vectorization_time": 2.34,
  "storage_time": 1.23,
  "total_time": 3.57
}
```

## 配置说明

### 1. 测试配置
在 `test_vector_config.py` 中可以修改：
- 测试知识库ID
- 最大测试分块数量
- 查询结果限制
- 性能测试参数

### 2. 测试数据
- 可以修改测试数据文件路径
- 可以调整测试样本内容
- 可以自定义查询样本

## 故障排除

### 1. 常见问题

**问题**: 测试数据文件不存在
```
解决: 确保先运行文档解析测试生成测试数据文件
```

**问题**: 向量库连接失败
```
解决: 检查Weaviate服务是否启动，配置文件是否正确
```

**问题**: 向量化API调用失败
```
解决: 检查智普API配置，确保API密钥有效
```

### 2. 调试模式
使用 `--verbose` 参数启用详细日志：
```bash
python run_vector_tests.py --mode quick --verbose
```

### 3. 单独运行测试
可以直接运行单个测试文件：
```bash
python test_vector_quick.py
python test_vector_integration.py
```

## 性能基准

### 1. 向量化性能
- 单个分块向量化: < 0.5秒
- 批量向量化(10个): < 3秒
- 批量向量化(50个): < 15秒

### 2. 存储性能
- 单个分块存储: < 0.2秒
- 批量存储(10个): < 2秒
- 批量存储(50个): < 10秒

### 3. 查询性能
- 向量相似度查询: < 0.1秒
- 过滤条件查询: < 0.05秒

## 扩展测试

### 1. 添加新的测试用例
在 `test_vector_config.py` 中添加新的测试样本：
```python
TEST_SAMPLES["new_chunks"] = [
    {
        "type": "text",
        "content": "新的测试内容",
        "metadata": {
            "description": "新测试描述",
            "keywords": ["新", "测试"]
        }
    }
]
```

### 2. 自定义测试流程
创建新的测试类继承 `TestVectorIntegration`：
```python
class CustomVectorTest(TestVectorIntegration):
    async def test_custom_functionality(self):
        # 自定义测试逻辑
        pass
```

## 注意事项

1. **数据清理**: 测试会自动清理创建的测试集合
2. **API限制**: 注意智普API的调用频率限制
3. **资源使用**: 性能测试会消耗较多内存和CPU资源
4. **网络依赖**: 需要稳定的网络连接访问向量化API

## 联系支持

如果遇到问题，请检查：
1. 配置文件是否正确
2. 依赖服务是否启动
3. 网络连接是否正常
4. API密钥是否有效 