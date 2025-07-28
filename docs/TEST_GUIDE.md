# 文档解析器测试指南

## 测试文件说明

本项目提供了三个测试文件来验证文档解析器的功能：

### 1. `test_doc_parser.py` - Word文档解析器测试
- 测试 `doc_parser.py` 的功能
- 支持 `.docx` 和 `.doc` 格式
- 输出JSON格式的测试结果

### 2. `test_xlsx_parser.py` - Excel文档解析器测试
- 测试 `xlsx_parser.py` 的功能
- 支持 `.xlsx` 格式
- 输出JSON格式的测试结果

### 3. `test_parsers_comprehensive.py` - 综合测试
- 同时测试Word和Excel解析器
- 生成详细的综合报告
- 提供完整的测试统计

## 使用方法

### 单独测试Word解析器
```bash
python test_doc_parser.py
```

### 单独测试Excel解析器
```bash
python test_xlsx_parser.py
```

### 综合测试（推荐）
```bash
python test_parsers_comprehensive.py
```

## 输出文件

测试结果会保存在 `test_results/` 目录下，文件名包含时间戳：

- `doc_parser_test_YYYYMMDD_HHMMSS.json` - Word解析器测试结果
- `xlsx_parser_test_YYYYMMDD_HHMMSS.json` - Excel解析器测试结果
- `comprehensive_parser_test_YYYYMMDD_HHMMSS.json` - 综合测试结果

## 测试结果格式

### 单个解析器测试结果
```json
{
  "test_data/testData.docx": {
    "file_path": "test_data/testData.docx",
    "file_size": 12345,
    "total_chunks": 10,
    "chunk_types": {
      "text": 5,
      "table_full": 2,
      "table_row": 3
    },
    "enhanced_chunks": 10,
    "total_content_length": 5000,
    "parse_duration_seconds": 2.5,
    "parse_time": "2024-01-01T12:00:00",
    "success": true,
    "chunks": [...]
  }
}
```

### 综合测试结果
```json
{
  "test_time": "2024-01-01T12:00:00",
  "doc_parser_results": {...},
  "xlsx_parser_results": {...},
  "summary": {
    "total_files": 4,
    "successful_files": 4,
    "doc_chunks": 15,
    "xlsx_chunks": 20
  }
}
```

## 测试内容

### Word文档解析器测试
- ✅ 文档解析功能
- ✅ 分块生成（text、table_full、table_row）
- ✅ LLM增强（description、keywords）
- ✅ chunk_id生成
- ✅ 上下文信息提取
- ✅ 父子关系建立

### Excel文档解析器测试
- ✅ 多Sheet解析
- ✅ 表格识别和分块
- ✅ 合并单元格处理
- ✅ 行级分块生成
- ✅ LLM增强
- ✅ chunk_id生成
- ✅ 上下文信息提取

## 测试统计信息

### Word文档统计
- 总分块数
- 分块类型分布
- 增强分块数量
- 总内容长度
- 解析耗时

### Excel文档统计
- 总分块数
- Sheet数量
- 表格数量
- 行级分块数量
- 合并单元格数量
- 增强分块数量
- 解析耗时

## 注意事项

1. **确保测试文件存在**：测试文件应放在 `test_data/` 目录下
2. **LLM配置**：确保 `.env` 文件中的LLM配置正确
3. **网络连接**：LLM增强需要网络连接
4. **输出目录**：测试结果会自动创建 `test_results/` 目录

## 故障排除

### 常见问题

1. **文件不存在错误**
   - 检查 `test_data/` 目录是否存在测试文件
   - 确认文件路径正确

2. **LLM增强失败**
   - 检查API密钥配置
   - 确认网络连接正常
   - 查看错误日志

3. **解析失败**
   - 检查文件格式是否支持
   - 确认文件未损坏
   - 查看详细错误信息

### 调试建议

1. 查看控制台输出的详细日志
2. 检查生成的JSON文件内容
3. 验证分块结构是否正确
4. 确认LLM增强字段是否存在

## 示例输出

```
文档解析器综合测试
================================================================================

============================================================
Word文档解析器综合测试
============================================================

📄 正在解析: test_data/testData.docx
✅ 解析成功
   📊 总分块数: 15
   🏷️  分块类型: {'text': 8, 'table_full': 2, 'table_row': 5}
   🧠 增强分块: 15
   📏 总内容长度: 12,345 字符
   ⏱️  解析耗时: 3.45 秒

============================================================
Excel文档解析器综合测试
============================================================

📊 正在解析: test_data/testData.xlsx
✅ 解析成功
   📊 总分块数: 20
   🏷️  分块类型: {'table_full': 3, 'table_row': 17}
   📋 Sheet数量: 2
   🧠 增强分块: 20
   📏 总内容长度: 8,765 字符
   🔗 合并单元格: 5
   ⏱️  解析耗时: 2.12 秒

================================================================================
综合测试报告
================================================================================
📈 总体统计:
   总文件数: 2
   成功解析: 2
   解析失败: 0
   成功率: 100.0%

📄 Word文档统计:
   总分块数: 15
   增强分块: 15
   增强率: 100.0%

📊 Excel文档统计:
   总分块数: 20
   增强分块: 20
   表格数量: 3
   增强率: 100.0%
================================================================================

✅ 综合测试结果已保存到: test_results/comprehensive_parser_test_20240101_120000.json

🎉 综合测试完成！
``` 