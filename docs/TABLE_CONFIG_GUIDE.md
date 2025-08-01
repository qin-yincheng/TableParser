# 表格配置使用指南

## 概述

本文档介绍如何在 `DocFileParser` 和 `XlsxFileParser` 中配置表格处理行为，包括表格格式选择和分块策略配置。

## 功能特性

### 1. 表格格式配置
- **HTML格式**（默认）：生成HTML表格标签
- **Markdown格式**：生成Markdown表格语法

### 2. 表格分块策略配置
- **完整表格块 + 行级分块**（默认）：生成完整表格和每行数据
- **只生成完整表格块**：仅生成完整表格，不生成行级分块

## 配置结构

### TableProcessingConfig
```python
@dataclass
class TableProcessingConfig:
    table_format: Literal["html", "markdown"] = "html"  # 表格输出格式
    table_chunking_strategy: Literal["full_only", "full_and_rows"] = "full_and_rows"  # 分块策略
    enable_table_processing: bool = True  # 是否启用表格处理
```

### FragmentConfig
```python
@dataclass
class FragmentConfig:
    # ... 其他配置项 ...
    table_processing: TableProcessingConfig = None  # 表格处理配置
```

## 使用示例

### Word文档解析器 (DocFileParser)

#### 1. 默认配置（向后兼容）

```python
from parsers.doc_parser import DocFileParser

# 使用默认配置，行为与之前版本完全一致
parser = DocFileParser()
chunks = parser.process("document.docx")
```

#### 2. 自定义表格格式

##### 使用Markdown格式
```python
from parsers.fragment_config import FragmentConfig, TableProcessingConfig
from parsers.doc_parser import DocFileParser

# 配置表格输出为Markdown格式
table_config = TableProcessingConfig(table_format="markdown")
fragment_config = FragmentConfig(table_processing=table_config)
parser = DocFileParser(fragment_config)

chunks = parser.process("document.docx")
```

##### 使用HTML格式（默认）
```python
from parsers.fragment_config import FragmentConfig, TableProcessingConfig
from parsers.doc_parser import DocFileParser

# 配置表格输出为HTML格式
table_config = TableProcessingConfig(table_format="html")
fragment_config = FragmentConfig(table_processing=table_config)
parser = DocFileParser(fragment_config)

chunks = parser.process("document.docx")
```

#### 3. 自定义分块策略

##### 只生成完整表格块
```python
from parsers.fragment_config import FragmentConfig, TableProcessingConfig
from parsers.doc_parser import DocFileParser

# 配置只生成完整表格块，不生成行级分块
table_config = TableProcessingConfig(table_chunking_strategy="full_only")
fragment_config = FragmentConfig(table_processing=table_config)
parser = DocFileParser(fragment_config)

chunks = parser.process("document.docx")
```

##### 生成完整表格块和行级分块（默认）
```python
from parsers.fragment_config import FragmentConfig, TableProcessingConfig
from parsers.doc_parser import DocFileParser

# 配置生成完整表格块和行级分块
table_config = TableProcessingConfig(table_chunking_strategy="full_and_rows")
fragment_config = FragmentConfig(table_processing=table_config)
parser = DocFileParser(fragment_config)

chunks = parser.process("document.docx")
```

### Excel文档解析器 (XlsxFileParser)

#### 1. 默认配置（向后兼容）

```python
from parsers.xlsx_parser import XlsxFileParser

# 使用默认配置，行为与之前版本完全一致
parser = XlsxFileParser()
chunks = parser.parse("document.xlsx")
```

#### 2. 自定义表格格式

##### 使用Markdown格式
```python
from parsers.fragment_config import FragmentConfig, TableProcessingConfig
from parsers.xlsx_parser import XlsxFileParser

# 配置表格输出为Markdown格式
table_config = TableProcessingConfig(table_format="markdown")
fragment_config = FragmentConfig(table_processing=table_config)
parser = XlsxFileParser(fragment_config)

chunks = parser.parse("document.xlsx")
```

##### 使用HTML格式（默认）
```python
from parsers.fragment_config import FragmentConfig, TableProcessingConfig
from parsers.xlsx_parser import XlsxFileParser

# 配置表格输出为HTML格式
table_config = TableProcessingConfig(table_format="html")
fragment_config = FragmentConfig(table_processing=table_config)
parser = XlsxFileParser(fragment_config)

chunks = parser.parse("document.xlsx")
```

#### 3. 自定义分块策略

##### 只生成完整表格块
```python
from parsers.fragment_config import FragmentConfig, TableProcessingConfig
from parsers.xlsx_parser import XlsxFileParser

# 配置只生成完整表格块，不生成行级分块
table_config = TableProcessingConfig(table_chunking_strategy="full_only")
fragment_config = FragmentConfig(table_processing=table_config)
parser = XlsxFileParser(fragment_config)

chunks = parser.parse("document.xlsx")
```

##### 生成完整表格块和行级分块（默认）
```python
from parsers.fragment_config import FragmentConfig, TableProcessingConfig
from parsers.xlsx_parser import XlsxFileParser

# 配置生成完整表格块和行级分块
table_config = TableProcessingConfig(table_chunking_strategy="full_and_rows")
fragment_config = FragmentConfig(table_processing=table_config)
parser = XlsxFileParser(fragment_config)

chunks = parser.parse("document.xlsx")
```

### 4. 组合配置

```python
from parsers.fragment_config import FragmentConfig, TableProcessingConfig
from parsers.doc_parser import DocFileParser
from parsers.xlsx_parser import XlsxFileParser

# 组合配置：Markdown格式 + 只生成完整表格块
table_config = TableProcessingConfig(
    table_format="markdown",
    table_chunking_strategy="full_only"
)
fragment_config = FragmentConfig(table_processing=table_config)

# Word文档解析器
doc_parser = DocFileParser(fragment_config)
doc_chunks = doc_parser.process("document.docx")

# Excel文档解析器
xlsx_parser = XlsxFileParser(fragment_config)
xlsx_chunks = xlsx_parser.parse("document.xlsx")
```

## 输出格式示例

### HTML格式输出
```html
<table border='1'>
<tr><th>姓名</th><th>年龄</th></tr>
<tr><td>张三</td><td>25</td></tr>
<tr><td>李四</td><td>30</td></tr>
</table>
```

### Markdown格式输出
```markdown
| 姓名 | 年龄 |
| --- | --- |
| 张三 | 25 |
| 李四 | 30 |
```

## 分块类型

### 1. 完整表格块（table_full）
包含整个表格的内容，适用于需要完整表格信息的场景。

### 2. 表格行分块（table_row）
包含单行表格数据，适用于需要逐行处理表格数据的场景。

## 元数据信息

每个表格分块都包含以下元数据：

```python
{
    "doc_id": "文档ID",
    "table_id": "表格ID",
    "table_format": "html|markdown",  # 表格格式
    "header": ["列1", "列2", ...],   # 表头信息
    "merged_cells": [...],           # 合并单元格信息
    "preceding_paragraph_content": "前一段内容",
    "following_paragraph_content": "后一段内容",
    # Excel特有字段
    "sheet": "Sheet名称",            # Excel工作表名称
    "start_row": 1,                 # 表格起始行
    "end_row": 10,                  # 表格结束行
    # ... 其他元数据
}
```

## 向后兼容性

- 所有现有代码无需修改即可正常工作
- 默认配置保持与之前版本完全一致的行为
- 支持传入 `None` 配置，自动使用默认配置

## 错误处理

- 配置验证：使用 `Literal` 类型确保配置值有效
- 格式转换失败：自动回退到HTML格式
- 日志记录：详细记录配置变更和错误信息

## 测试

运行测试验证功能：

```bash
# Word文档表格配置测试
python tests/test_table_config.py

# Excel文档表格配置测试
python tests/test_xlsx_table_config.py
```

## 注意事项

### Word文档 (DocFileParser)
1. **性能考虑**：Markdown格式转换比HTML格式稍快，但功能相对简单
2. **合并单元格**：Markdown格式不支持合并单元格的复杂显示，会转换为普通表格
3. **样式信息**：两种格式都不保留原始表格的样式信息
4. **编码处理**：确保文档使用UTF-8编码以获得最佳结果

### Excel文档 (XlsxFileParser)
1. **多级表头**：Markdown格式会将多级表头合并为单级表头
2. **合并单元格**：Excel的合并单元格在Markdown格式下会简化为普通表格
3. **多Sheet处理**：每个Sheet都会应用相同的配置
4. **数据类型**：Excel的数值类型在转换时会保持原格式

## 迁移指南

### 从旧版本迁移

1. **无需修改**：现有代码可以继续使用，默认行为不变
2. **可选优化**：根据需要添加表格配置以优化处理行为
3. **渐进式迁移**：可以逐步为不同文档类型配置不同的表格处理策略

### 配置建议

- **文档检索场景**：建议使用 `full_and_rows` 策略，提供更细粒度的检索
- **文档展示场景**：建议使用 `full_only` 策略，减少冗余数据
- **Markdown兼容场景**：建议使用 `markdown` 格式，便于后续处理
- **Web展示场景**：建议使用 `html` 格式，保持样式一致性
- **Excel多Sheet场景**：建议使用 `full_only` 策略，避免数据冗余 