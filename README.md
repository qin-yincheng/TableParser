# TableParser - 智能文档解析与向量化系统

## 项目简介

TableParser 是一个基于 RAG（检索增强生成）技术的智能文档解析与向量化系统，专门用于处理 Word 和 Excel 文档中的表格数据。系统能够精准解析文档结构，提取表格内容，生成语义向量，并支持智能检索和问答。

## 核心功能

### 📄 文档解析
- **Word 文档支持**：DOC/DOCX 格式，使用 LibreOffice 转换 + python-docx 解析
- **Excel 文档支持**：XLSX 格式，支持多工作表解析
- **表格识别**：自动识别文档中的表格结构，处理合并单元格
- **智能分块**：支持文本段落和表格的智能分块处理
- **表格格式配置**：支持 HTML 和 Markdown 格式的表格输出
- **分块策略配置**：可选择只生成完整表格块或同时生成表格行数据

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

## 技术架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   文档解析层     │    │   语义增强层     │    │   向量化存储层   │
│                 │    │                 │    │                 │
│ • DOC/DOCX      │───▶│ • LLM 增强      │───▶│ • 向量嵌入      │
│ • XLSX          │    │ • 语义描述      │    │ • Weaviate      │
│ • 表格识别      │    │ • 关键词提取    │    │ • 知识库管理    │
│ • 格式配置      │    │ • 上下文感知    │    │ • 批量操作      │
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

## 安装部署

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
WEAVIATE_URL=http://localhost:8080
```

5. **启动 Weaviate**
```bash
# 使用 Docker Compose
docker-compose up -d

# 或使用 Docker
docker run -d -p 8080:8080 --name weaviate-server cr.weaviate.io/semitechnologies/weaviate:1.22.4
```

## 快速开始

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
    file_paths = ["test_data/testData.docx", "test_data/testData.xlsx"]
    results = await process_multiple_documents(file_paths, kb_id=1)
    for result in results:
        print(f"处理结果: {result}")

asyncio.run(main())
```

### 3. 智能问答
```python
from qa_service import QAService

qa_service = QAService()
response = qa_service.ask_question("什么是人工智能？", kb_id=1)
print(f"回答: {response}")
```

## 表格处理配置

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

## 项目结构

```
TableParser/
├── parsers/                    # 文档解析器
│   ├── __init__.py
│   ├── doc_parser.py           # Word文档解析（支持DOC/DOCX）
│   ├── xlsx_parser.py          # Excel文档解析
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
│   └── db_manager.py           # 数据库管理
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
│   ├── test_embedding.py       # 向量化测试
│   ├── test_vector_integration.py # 向量集成测试
│   └── test_main_processor_config.py # 主处理器配置测试
│
├── docs/                       # 文档资料
│   ├── RAG系统开发方案.md       # 系统开发方案
│   ├── DOCKER_DEPLOYMENT.md    # Docker部署指南
│   ├── QA_SERVICE_GUIDE.md     # 问答服务指南
│   ├── TEST_GUIDE.md           # 测试指南
│   └── table_config_guide.md   # 表格配置指南
│
├── main_processor.py           # 主处理流程
├── operations.py               # 操作流程
├── connector.py                # 连接器
├── docker-compose.yml          # Docker编排
└── README.md                   # 项目说明
```

## 配置说明

### 分片配置
```yaml
fragmentation:
  enable: true
  max_chunk_size: 1000
  min_fragment_size: 200
  chunk_overlap: 100
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

## 核心特性

### 🔧 智能分片
- **自适应分块**：根据内容长度和语义边界智能分块
- **上下文保持**：确保分块后的内容保持语义完整性
- **重叠处理**：支持分块重叠，避免信息丢失

### 📊 表格处理
- **合并单元格**：完整保留表格的合并单元格信息
- **表头识别**：自动识别和提取表格表头
- **行列关系**：保持表格的行列结构和关系
- **格式配置**：支持 HTML 和 Markdown 格式输出
- **分块策略**：可选择只生成完整表格块或同时生成行数据
- **多级表头**：Excel 文档支持多级表头处理

### 🎯 语义增强
- **多类型支持**：针对文本、表格、分片等不同类型内容
- **上下文感知**：结合文档上下文进行语义理解
- **关键词提取**：自动提取内容的关键词和主题

### 🚀 高性能
- **异步处理**：支持异步并发处理多个文档
- **批量操作**：向量化和存储支持批量操作
- **错误恢复**：具备完善的错误处理和恢复机制

## 测试

### 运行测试
```bash
# 运行所有测试
python -m pytest tests/

# 运行特定测试
python -m pytest tests/test_doc_parser.py
python -m pytest tests/test_xlsx_parser.py
python -m pytest tests/test_vector_integration.py
python -m pytest tests/test_main_processor_config.py
```

### 测试数据
测试数据位于 `test_data/` 目录，包含：
- `testData.doc` / `testData.docx`：Word 文档测试
- `testData.xlsx`：Excel 文档测试

### 表格配置测试
```bash
# 测试表格配置功能
python tests/test_doc_parser.py
python tests/test_xlsx_parser.py
```

## 部署

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

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证。

## 联系方式

如有问题或建议，请通过以下方式联系：
- 提交 Issue
- 发送邮件
- 参与讨论

---

**TableParser** - 让文档解析更智能，让知识检索更精准！ 