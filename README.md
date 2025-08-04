# TableParser - 智能文档解析与向量化系统

## 项目简介

TableParser 是一个基于 RAG（检索增强生成）技术的智能文档解析与向量化系统，专门用于处理 Word 和 Excel 文档中的表格数据。系统能够精准解析文档结构，提取表格内容，生成语义向量，并支持智能检索和问答。

## 🚀 核心功能

### 📄 智能文档解析
- **Word 文档支持**：DOC/DOCX 格式，使用 LibreOffice 转换 + python-docx 解析
- **Excel 文档支持**：XLSX 格式，支持多工作表解析
- **表格识别**：自动识别文档中的表格结构，处理合并单元格
- **智能分块**：支持文本段落和表格的智能分块处理
- **表格格式配置**：支持 HTML 和 Markdown 格式的表格输出
- **分块策略配置**：可选择只生成完整表格块或同时生成表格行数据

### 🔧 高级表格处理技术
- **合并单元格处理**：
  - Excel：基于 Worksheet 的精确合并单元格检测
  - Word：超增强合并单元格检测算法
  - 完整保留合并单元格内容和结构
- **智能表头检测**：
  - 多策略投票机制（合并单元格检测、结构特征分析、内容模式检测）
  - 结构特征分析
  - 合并单元格分布分析
- **多级表头支持**：
  - 层次表头构建
  - 父子表头关系映射
  - 动态表头内容继承
- **格式转换优化**：
  - HTML：正确生成 colspan/rowspan 属性
  - Markdown：层次表头显示
  - 结构保持和内容完整性

### 🧠 语义增强
- **LLM 增强**：基于智普 AI 的语义描述和关键词提取
- **上下文感知**：结合文档上下文进行内容理解
- **结构化输出**：生成标准化的 JSON 格式描述

### 🔍 向量化存储
- **向量嵌入**：使用智普 AI 生成高维语义向量
- **向量数据库**：基于 Weaviate 的向量存储和检索
- **知识库管理**：支持多知识库隔离和管理

### 💬 智能问答
- **语义检索**：基于向量相似度的内容检索
- **上下文问答**：结合检索结果的智能问答
- **多轮对话**：支持连续对话和上下文保持

## 🏗️ 技术架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   文档解析层     │    │   语义增强层     │    │   向量化存储层   │
│                 │    │                 │    │                 │
│ • DOC/DOCX      │───▶│ • LLM 增强      │───▶│ • 向量嵌入      │
│ • XLSX          │    │ • 语义描述      │    │ • Weaviate      │
│ • 表格识别      │    │ • 关键词提取    │    │ • 知识库管理    │
│ • 格式配置      │    │ • 上下文感知    │    │ • 批量操作      │
│ • 合并单元格    │    │                 │    │                 │
│ • 多级表头      │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   智能问答层     │
                       │                 │
                       │ • 语义检索      │
                       │ • 上下文问答    │
                       │ • 多轮对话      │
                       └─────────────────┘
```

## 📊 表格解析技术特性

### 🔧 高级合并单元格处理

#### Excel 文档 (XLSX)
- **Worksheet 集成**：直接使用 openpyxl Worksheet 对象获取精确的合并单元格信息
- **多级表头支持**：正确处理跨行跨列的复杂表头结构
- **内容映射**：确保合并单元格内容正确显示在所有相关单元格中
- **HTML/Markdown 转换**：支持 `colspan` 和 `rowspan` 属性的正确生成

#### Word 文档 (DOC/DOCX)
- **超增强合并检测**：`_get_cell_span_ultra_enhanced` 方法提供精确的合并单元格信息
- **智能表头检测**：多策略投票机制确定表头行位置
- **层次表头构建**：`_build_header_hierarchy_for_doc` 构建清晰的表头层次结构
- **结构感知解析**：基于表格结构特征而非内容特征的智能解析

### 📊 智能表头检测系统

#### 多策略检测机制
1. **合并单元格检测** (`_detect_header_rows_by_merge_enhanced`)
   - 分析合并单元格分布模式
   - 识别表头行的合并特征

2. **结构特征检测** (`_detect_header_rows_by_structure_enhanced`)
   - 分析单元格空值分布
   - 检测合并单元格数量模式
   - 识别表格结构特征

3. **内容模式检测** (`_detect_header_rows_by_content_pattern`)
   - 关键词匹配（如"年度"、"学校"等）
   - 数值比例分析
   - 文本特征识别

4. **投票机制** (`_detect_header_rows_smart`)
   - 综合多种检测策略
   - 采用投票机制确定最终表头行位置
   - 提供可靠的表头检测结果

### 🎯 表头层次映射

#### 层次结构构建
- **多级表头支持**：正确处理父子表头关系
- **动态映射**：根据合并单元格信息动态构建表头映射
- **内容继承**：子表头正确继承父表头信息
- **格式保持**：保持原始表格的层次结构

#### 映射算法示例
```python
# 示例：表头层次映射
{
    0: "年度",           # 第一列：年度
    1: "学校名称",       # 第二列：学校名称  
    2: "本科生情况",     # 第三列：本科生情况（父表头）
    3: "本科生情况",     # 第四列：本科生情况（父表头）
    4: "备注"           # 第五列：备注
}
```

### 🚀 格式转换优化

#### HTML 格式
- **合并单元格支持**：正确生成 `colspan` 和 `rowspan` 属性
- **表头层次**：保持表头的层次结构
- **样式兼容**：生成标准 HTML 表格格式

#### Markdown 格式
- **层次表头**：正确处理多级表头显示
- **合并内容**：合并单元格内容正确显示
- **格式规范**：符合 Markdown 表格语法规范

### 🔍 质量保证机制

#### 验证和回退
- **结构验证**：`_validate_header_structure` 验证生成的表头结构
- **智能回退**：`_fallback_header_processing` 提供简化处理方案
- **错误恢复**：完善的错误处理和恢复机制

#### 示例输出对比

**优化前的问题：**
```markdown
| 年度/2005年/2005年/2005年/2005年/2005年 | 学校名称/Cedar 大学/Elm 学院/Maple 专科学院/Pine 学院/Oak 研究所 |
```

**优化后的正确输出：**
```markdown
| 年度 | 学校名称 | 本科生情况 | 本科生情况 | 备注 |
| --- | --- | ---: | ---: | --- |
| | | 新生人数 | 毕业生人数 | |
| 2005年 | Cedar 大学 | 110 | 103 | 合计 +7 |
```

## 🛠️ 安装部署

### 环境要求
- Python 3.8+
- LibreOffice（用于 DOC 文件转换）
- Weaviate 向量数据库

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd TableParser
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **安装 LibreOffice**
```bash
# Windows
# 下载并安装 LibreOffice

# Linux
sudo apt-get install libreoffice

# macOS
brew install libreoffice
```

4. **配置环境变量**
```bash
# 创建 .env 文件
ZHIPUAI_API_KEY=your_zhipu_api_key
WEAVIATE_URL=http://localhost:8089
```

5. **启动 Weaviate**
```bash
# 使用 Docker Compose
docker-compose up -d

# 或使用 Docker
docker run -d -p 8089:8080 --name weaviate-server cr.weaviate.io/semitechnologies/weaviate:1.22.4
```

## 🚀 快速开始

### 1. 处理单个文档
```python
from main_processor import process_single_document
import asyncio

async def main():
    result = await process_single_document("test_data/testData.docx", kb_id=1)
    print(f"处理结果: {result}")

asyncio.run(main())
```

### 2. 批量处理文档
```python
from main_processor import process_multiple_documents
import asyncio

async def main():
    file_paths = ["test_data/testData.docx", "test_data/test.xlsx"]
    results = await process_multiple_documents(file_paths, kb_id=1)
    for result in results:
        print(f"处理结果: {result}")

asyncio.run(main())
```

### 3. 智能问答
```python
from qa_service import QAService

qa_service = QAService()
response = await qa_service.answer_question("什么是人工智能？", kb_id=1)
print(f"回答: {response}")
```

### 4. 交互式问答演示
```python
from tests.qa_demo import QADemo
import asyncio

async def main():
    demo = QADemo()
    await demo.interactive_qa()

asyncio.run(main())
```

## ⚙️ 表格处理配置

### 表格格式配置
系统支持两种表格输出格式：

#### HTML 格式（默认）
```python
from parsers.fragment_config import TableProcessingConfig, FragmentConfig

# 配置HTML格式
table_config = TableProcessingConfig(
    table_format="html",
    table_chunking_strategy="full_only"
)
```

#### Markdown 格式
```python
# 配置Markdown格式
table_config = TableProcessingConfig(
    table_format="markdown",
    table_chunking_strategy="full_only"
)
```

### 分块策略配置

#### 只生成完整表格块
```python
# 只生成完整表格块，不生成行级数据
table_config = TableProcessingConfig(
    table_format="markdown",
    table_chunking_strategy="full_only"
)
```

#### 生成完整表格块和行数据
```python
# 生成完整表格块和行级数据
table_config = TableProcessingConfig(
    table_format="markdown",
    table_chunking_strategy="full_and_rows"
)
```

### 在解析器中使用配置

#### Word 文档解析器
```python
from parsers.doc_parser import DocFileParser
from parsers.fragment_config import FragmentConfig, TableProcessingConfig

# 创建表格配置
table_config = TableProcessingConfig(
    table_format="markdown",
    table_chunking_strategy="full_only"
)

# 创建解析器配置
fragment_config = FragmentConfig(
    enable_fragmentation=True,
    max_chunk_size=1000,
    table_processing=table_config
)

# 初始化解析器
parser = DocFileParser(fragment_config=fragment_config)
chunks = parser.process("document.docx")
```

#### Excel 文档解析器
```python
from parsers.xlsx_parser import XlsxFileParser
from parsers.fragment_config import FragmentConfig, TableProcessingConfig

# 创建表格配置
table_config = TableProcessingConfig(
    table_format="markdown",
    table_chunking_strategy="full_only"
)

# 创建解析器配置
fragment_config = FragmentConfig(table_processing=table_config)

# 初始化解析器
parser = XlsxFileParser(fragment_config=fragment_config)
chunks = parser.parse("document.xlsx")
```

### 默认配置
系统默认使用以下配置：
- **表格格式**：Markdown
- **分块策略**：只生成完整表格块
- **向后兼容**：保持与现有代码的兼容性

## 📁 项目结构

```
TableParser/
├── parsers/                    # 文档解析器
│   ├── __init__.py
│   ├── doc_parser.py           # Word文档解析（支持DOC/DOCX）
│   │                          # - 超增强合并单元格检测
│   │                          # - 智能表头检测系统
│   │                          # - 层次表头映射
│   │                          # - 结构感知解析
│   ├── xlsx_parser.py          # Excel文档解析
│   │                          # - Worksheet集成合并单元格处理
│   │                          # - 多级表头支持
│   │                          # - 精确内容映射
│   ├── chunker.py              # 智能分块处理
│   ├── fragment_manager.py     # 分片管理
│   ├── fragment_config.py      # 分片配置（包含表格处理配置）
│   ├── context_rebuilder.py    # 上下文重建
│   └── position_mapper.py      # 位置映射
│
├── utils/                      # 工具模块
│   ├── __init__.py
│   ├── config_manager.py       # 配置管理
│   ├── logger.py               # 日志工具
│   ├── zhipu_client.py         # 智普AI客户端
│   ├── chunk_prompts.py        # 提示词模板
│   ├── db_base.py              # 数据库基础类
│   ├── db_manager.py           # 数据库管理
│   └── config.py               # 配置工具
│
├── services/                   # 核心服务
│   ├── embedding_service.py    # 向量嵌入服务
│   ├── vector_service.py       # 向量数据库服务
│   ├── qa_service.py           # 问答服务
│   └── query_service.py        # 查询服务
│
├── config/                     # 配置文件
│   └── config.yaml             # 主配置文件
│
├── tests/                      # 测试代码
│   ├── test_doc_parser.py      # 文档解析测试
│   ├── test_xlsx_parser.py     # Excel解析测试
│   ├── test_qa_service.py      # 问答服务测试
│   ├── test_query_service.py   # 查询服务测试
│   ├── test_model_answer.py    # 模型答案测试
│   └── qa_demo.py              # 问答演示
│
├── docs/                       # 文档资料
│   ├── RAG系统开发方案.md       # 系统开发方案
│   └── 构建RAG系统以实现Word和Excel表格的精准解析与检索.md
│
├── test_data/                  # 测试数据
│   ├── testData1.docx          # Word测试文档
│   ├── test.xlsx               # Excel测试文档
│   └── test2.xlsx              # Excel测试文档2
│
├── test_results/               # 测试结果
│   ├── doc_parser_test_*.json  # 文档解析测试结果
│   ├── xlsx_parser_test_*.json # Excel解析测试结果
│   └── embedding_test_results/ # 向量化测试结果
│
├── main_processor.py           # 主处理流程
├── operations.py               # 操作流程
├── connector.py                # 连接器
├── docker-compose.yml          # Docker编排
└── README.md                   # 项目说明
```

## ⚙️ 配置说明

### 分片配置
```yaml
fragmentation:
  enable: true
  max_chunk_size: 500
  min_fragment_size: 100
  chunk_overlap: 50
  enable_context_rebuild: true
```

### 表格处理配置
```yaml
table_processing:
  table_format: "markdown"        # "html" 或 "markdown"
  table_chunking_strategy: "full_only"  # "full_only" 或 "full_and_rows"
  enable_table_processing: true
```

### LLM 配置
```yaml
llm:
  api_key: ${ZHIPUAI_API_KEY}
  model: glm-4
  temperature: 0.1
  timeout: 30
  max_tokens: 1000
```

### 向量数据库配置
```yaml
vector_db:
  url: ${WEAVIATE_URL}
  timeout: 60
  batch_size: 100
```

## 🔧 核心特性

### 🔧 智能分片
- **自适应分块**：根据内容长度和语义边界智能分块
- **上下文保持**：确保分块后的内容保持语义完整性
- **重叠处理**：支持分块重叠，避免信息丢失

### 📊 高级表格处理
- **合并单元格处理**：
  - Excel：基于 Worksheet 的精确合并单元格检测
  - Word：超增强合并单元格检测算法
  - 完整保留合并单元格内容和结构
- **智能表头检测**：
  - 多策略投票机制
  - 结构特征分析
  - 合并单元格分布分析
- **多级表头支持**：
  - 层次表头构建
  - 父子表头关系映射
  - 动态表头内容继承
- **格式转换优化**：
  - HTML：正确生成 colspan/rowspan 属性
  - Markdown：层次表头显示
  - 结构保持和内容完整性
- **质量保证**：
  - 表头结构验证
  - 智能回退机制
  - 错误恢复处理

### 🎯 语义增强
- **多类型支持**：针对文本、表格、分片等不同类型内容
- **上下文感知**：结合文档上下文进行语义理解
- **关键词提取**：自动提取内容的关键词和主题

### 🚀 高性能
- **异步处理**：支持异步并发处理多个文档
- **批量操作**：向量化和存储支持批量操作
- **错误恢复**：具备完善的错误处理和恢复机制

## 🧪 测试

### 运行测试
```bash
# 运行所有测试
python -m pytest tests/

# 运行特定测试
python -m pytest tests/test_doc_parser.py
python -m pytest tests/test_xlsx_parser.py
python -m pytest tests/test_qa_service.py
python -m pytest tests/test_query_service.py
```

### 测试数据
测试数据位于 `test_data/` 目录，包含：
- `testData1.docx`：Word 文档测试
- `test.xlsx`：Excel 文档测试
- `test2.xlsx`：Excel 文档测试2

### 表格配置测试
```bash
# 测试表格配置功能
python tests/test_doc_parser.py
python tests/test_xlsx_parser.py
```

### 问答演示
```bash
# 运行交互式问答演示
python tests/qa_demo.py
```

## 🐳 部署

### Docker 部署
```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs weaviate
```

### 生产环境
1. 配置环境变量
2. 启动 Weaviate 向量数据库
3. 运行主服务
4. 配置反向代理（如 Nginx）

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- 提交 [Issue](../../issues)
- 发送邮件
- 参与讨论

---

**TableParser** - 让文档解析更智能，让知识检索更精准！ 🚀 