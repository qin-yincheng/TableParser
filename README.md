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
- **图片处理**：支持段落与表格内联图片的定位、提取和语义分析

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

### 🖼️ 图片处理功能
- **图片定位与提取**：支持段落与表格内联图片的定位与提取
- **图片存储管理**：自动保存至 `storage/images/<doc_id>/` 目录
- **图片语义分析**：结合上下文进行图片语义分析（需配置视觉模型）
- **图片元数据生成**：生成描述、关键词等元数据并参与向量检索
- **配置化策略**：支持多种图片定位和附着策略配置

### 🧠 语义增强
- **LLM 增强**：基于智普 AI 的语义描述和关键词提取
- **上下文感知**：结合文档上下文进行内容理解
- **结构化输出**：生成标准化的 JSON 格式描述
- **多类型内容支持**：针对文本、表格、图片等不同类型内容进行语义增强

### 🔍 向量化存储
- **向量嵌入**：使用智普 AI 生成高维语义向量
- **向量数据库**：基于 Weaviate 的向量存储和检索
- **知识库管理**：支持多知识库隔离和管理
- **批量操作**：支持批量向量化和存储操作

### 💬 智能问答
- **语义检索**：基于向量相似度的内容检索
- **上下文问答**：结合检索结果的智能问答
- **多轮对话**：支持连续对话和上下文保持
- **答案来源追踪**：提供答案的来源信息和相似度分数

## 🏗️ 技术架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   文档解析层     │    │   语义增强层     │    │   向量化存储层   │
│                 │    │                 │    │                 │
│ • DOC/DOCX      │───▶│ • LLM 增强      │───▶│ • 向量嵌入      │
│ • XLSX          │    │ • 语义描述      │    │ • Weaviate      │
│ • 表格识别      │    │ • 关键词提取    │    │ • 知识库管理    │
│ • 图片处理      │    │ • 上下文感知    │    │ • 批量操作      │
│ • 格式配置      │    │ • 视觉分析      │    │ • 多粒度存储    │
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
                       │ • 答案追踪      │
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
- Python 3.8+ (推荐 3.12.9)
- LibreOffice（用于 DOC 文件转换）
- Weaviate 向量数据库
- 智普 AI API 密钥

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
# 下载并安装 LibreOffice: https://www.libreoffice.org/download/download/

# Linux (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install libreoffice

# macOS
brew install libreoffice
```

4. **配置环境变量**
```bash
# 创建 .env 文件
# 大模型配置
LLM_BINDING=openai
LLM_MODEL=glm-4-plus
LLM_BINDING_API_KEY=your_zhipu_api_key

# 向量模型配置
EMBEDDING_BINDING=openai
EMBEDDING_MODEL=embedding-3
EMBEDDING_BINDING_API_KEY=your_zhipu_api_key

# 视觉模型配置（用于图片理解）
VISION_MODEL=glm-4v-plus
VISION_BINDING_API_KEY=your_zhipu_api_key

# 可选配置
ENABLE_LLM_CACHE=false
ENABLE_LLM_CACHE_FOR_EXTRACT=false
TIMEOUT=60
TEMPERATURE=0
MAX_ASYNC=4
MAX_TOKENS=2048
```

5. **启动 Weaviate**
```bash
# 使用 Docker Compose（推荐）
docker-compose up -d

# 或使用 Docker（与 docker-compose 端口保持一致）
docker run -d \
  -p 8089:8080 \
  -p 50055:50051 \
  --name weaviate-server \
  semitechnologies/weaviate:latest
```

## 🚀 快速开始

### 1. 处理单个文档
```python
from main_processor import process_single_document
import asyncio

async def main():
    result = await process_single_document("test_data/testData1.docx", kb_id=1)
    print(f"处理结果: {result}")

asyncio.run(main())
```

### 2. 批量处理文档
```python
from main_processor import process_multiple_documents
import asyncio

async def main():
    file_paths = ["test_data/testData1.docx", "test_data/test.xlsx"]
    results = await process_multiple_documents(file_paths, kb_id=1)
    for result in results:
        print(f"处理结果: {result}")

asyncio.run(main())
```

### 3. 智能问答
```python
from qa_service import QAService
import asyncio

async def main():
    qa_service = QAService()
    response = await qa_service.answer_question("什么是人工智能？", kb_id=1)
    print(f"回答: {response}")

asyncio.run(main())
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

#### HTML 格式（示例）
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
import asyncio

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

async def main():
    # 初始化解析器并解析（异步）
    parser = DocFileParser(fragment_config=fragment_config)
    chunks = await parser.process("document.docx")
    print(len(chunks))

asyncio.run(main())
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
│   ├── doc_parser.py          # Word文档解析器
│   ├── xlsx_parser.py         # Excel文档解析器
│   ├── chunker.py             # 文本分块器
│   ├── fragment_manager.py    # 分片管理器
│   ├── fragment_config.py     # 分片配置
│   ├── context_rebuilder.py   # 上下文重构器
│   ├── position_mapper.py     # 位置映射器
│   └── image_processing/      # 图片处理模块
│       ├── __init__.py
│       ├── image_extractor.py # 图片提取器
│       ├── context_collector.py # 上下文收集器
│       └── image_analyzer.py  # 图片分析器
│
├── utils/                     # 工具模块
│   ├── __init__.py
│   ├── answer_postprocessor.py # 答案后处理器
│   ├── chunk_prompts.py       # 分块提示词
│   ├── config_manager.py      # 配置管理器
│   ├── logger.py              # 日志工具
│   ├── db_base.py             # 数据库基类
│   ├── db_manager.py          # 数据库管理器
│   ├── config.py              # 配置工具
│   └── zhipu_client.py        # 智普AI客户端
│
├── config/                    # 配置文件
│   └── config.yaml           # 主配置文件
│
├── tests/                     # 测试模块
│   ├── __init__.py
│   ├── qa_demo.py            # 问答演示
│   ├── test_doc_parser.py    # Word解析器测试
│   ├── test_xlsx_parser.py   # Excel解析器测试
│   ├── test_qa_service.py    # 问答服务测试
│   ├── test_query_service.py # 查询服务测试
│   └── test_model_answer.py  # 模型答案测试
│
├── logs/                      # 日志目录
├── storage/                   # 存储目录
│   └── images/               # 图片存储
├── temp/                      # 临时文件目录
├── test_data/                 # 测试数据
├── test_results/              # 测试结果
├── docs/                      # 文档目录
│
├── main_processor.py          # 主处理器
├── operations.py              # 数据库操作
├── connector.py               # 数据库连接器
├── embedding_service.py       # 向量嵌入服务
├── vector_service.py          # 向量服务
├── qa_service.py              # 问答服务
├── query_service.py           # 查询服务
├── docker-compose.yml         # Docker编排文件
├── requirements.txt           # 依赖包列表
├── README.md                  # 项目说明
└── 说明文档.md                # 详细说明文档
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

### 图片处理配置
```yaml
image_processing:
  enabled: true
  storage_path: "storage/images"
  image_position_strategy: "inline"           # inline | placeholder_replace | append_end
  table_image_attach_mode: "separate_block"  # separate_block | merge_into_row | merge_into_table
```

### Weaviate 数据库配置
```yaml
database:
  weaviate:
    host: "localhost"
    port: 8089
    grpc_host: "localhost"
    grpc_port: 50055
    scheme: "http"
    api_key: null
    timeout: [5, 30]
```

### 环境变量配置
```bash
# LLM配置
LLM_BINDING=openai
LLM_MODEL=glm-4-plus
LLM_BINDING_API_KEY=your_zhipu_api_key

# 向量模型配置
EMBEDDING_BINDING=openai
EMBEDDING_MODEL=embedding-3
EMBEDDING_BINDING_API_KEY=your_zhipu_api_key

# 视觉模型配置
VISION_MODEL=glm-4v-plus
VISION_BINDING_API_KEY=your_zhipu_api_key

# 性能配置
ENABLE_LLM_CACHE=false
TIMEOUT=60
TEMPERATURE=0
MAX_ASYNC=4
MAX_TOKENS=2048
```

## 🔧 核心特性

### 🔧 智能分片
- **自适应分块**：根据内容长度和语义边界智能分块
- **上下文保持**：确保分块后的内容保持语义完整性
- **重叠处理**：支持分块重叠，避免信息丢失
- **多粒度支持**：支持文本、表格、图片等多种内容类型的分块

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

### 🖼️ 图片处理功能
- **图片定位与提取**：支持段落与表格内联图片的定位与提取
- **图片存储管理**：自动保存至 `storage/images/<doc_id>/` 目录
- **图片语义分析**：结合上下文进行图片语义分析（需配置视觉模型）
- **图片元数据生成**：生成描述、关键词等元数据并参与向量检索
- **配置化策略**：支持多种图片定位和附着策略配置

### 🎯 语义增强
- **多类型支持**：针对文本、表格、图片等不同类型内容
- **上下文感知**：结合文档上下文进行语义理解
- **关键词提取**：自动提取内容的关键词和主题
- **结构化输出**：生成标准化的 JSON 格式描述

### 🚀 高性能
- **异步处理**：支持异步并发处理多个文档
- **批量操作**：向量化和存储支持批量操作
- **错误恢复**：具备完善的错误处理和恢复机制
- **缓存机制**：支持LLM和向量化结果的缓存

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
 
# 访问 Weaviate Console（如启用）
# http://localhost:3000
```

### 生产环境部署
1. **配置环境变量**
   - 设置智普AI API密钥
   - 配置数据库连接参数
   - 设置日志级别

2. **启动 Weaviate 向量数据库**
   ```bash
   docker-compose up -d weaviate
   ```

3. **运行主服务**
   ```bash
   python main_processor.py --kb-id 1 test_data/testData1.docx
   ```

4. **配置反向代理（可选）**
   - 使用 Nginx 进行负载均衡
   - 配置 SSL 证书
   - 设置访问控制

## 🖥️ 命令行用法

```bash
# 查看帮助
python main_processor.py --help

# 处理单个或多个文件到指定知识库
python main_processor.py --kb-id 100 test_data/testData1.docx
python main_processor.py --kb-id 200 test_data/testData1.docx test_data/test.xlsx

# 强制重建知识库后再处理
python main_processor.py --kb-id 300 --force-recreate test_data/testData1.docx
```

## 🔍 使用示例

### 1. 文档处理示例
```python
import asyncio
from main_processor import process_single_document

async def process_document():
    # 处理Word文档
    result = await process_single_document("document.docx", kb_id=1)
    print(f"处理结果: {result}")
    
    # 处理Excel文档
    result = await process_single_document("data.xlsx", kb_id=1)
    print(f"处理结果: {result}")

asyncio.run(process_document())
```

### 2. 问答系统示例
```python
import asyncio
from qa_service import QAService

async def ask_questions():
    qa_service = QAService()
    
    # 简单问答
    response = await qa_service.answer_question("什么是人工智能？", kb_id=1)
    print(f"答案: {response['answer']}")
    
    # 表格数据查询
    response = await qa_service.answer_question("2023年的销售额是多少？", kb_id=1)
    print(f"答案: {response['answer']}")

asyncio.run(ask_questions())
```

### 3. 自定义配置示例
```python
from parsers.fragment_config import FragmentConfig, TableProcessingConfig
from parsers.doc_parser import DocFileParser

# 自定义表格配置
table_config = TableProcessingConfig(
    table_format="html",
    table_chunking_strategy="full_and_rows"
)

# 自定义分片配置
fragment_config = FragmentConfig(
    enable_fragmentation=True,
    max_chunk_size=800,
    min_fragment_size=150,
    chunk_overlap=100,
    table_processing=table_config
)

# 使用自定义配置
parser = DocFileParser(fragment_config=fragment_config)
```

## 🚨 注意事项

### 1. 环境要求
- 确保 LibreOffice 已正确安装（用于 DOC 文件转换）
- 确保 Weaviate 向量数据库正在运行
- 确保智普AI API密钥配置正确

### 2. 性能优化
- 对于大文档，建议启用分片功能
- 使用批量处理可以提高效率
- 合理配置缓存参数可以提升性能

### 3. 错误处理
- 系统具备完善的错误处理和恢复机制
- 查看日志文件了解详细错误信息
- 对于API调用失败，系统会自动重试

### 4. 数据安全
- 敏感文档建议使用私有部署
- 定期备份向量数据库数据
- 注意API密钥的安全存储

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

## 📚 相关文档

- [详细说明文档](说明文档.md) - 系统详细技术说明
- [API文档](docs/api.md) - API接口文档
- [部署指南](docs/deployment.md) - 详细部署指南
- [故障排除](docs/troubleshooting.md) - 常见问题解决方案

## 🔧 环境变量配置详解

### LLM 配置
```bash
# LLM提供商和模型
LLM_BINDING=openai                    # LLM提供商
LLM_MODEL=glm-4-plus                  # 模型名称
LLM_BINDING_API_KEY=your_api_key      # API密钥

# 性能配置
TIMEOUT=60                            # 超时时间（秒）
TEMPERATURE=0                         # 温度参数
MAX_ASYNC=4                          # 最大并发数
MAX_TOKENS=2048                      # 最大token数

# 缓存配置
ENABLE_LLM_CACHE=false               # 是否启用LLM缓存
```

### 向量模型配置
```bash
# 向量模型配置
EMBEDDING_BINDING=openai              # 向量模型提供商
EMBEDDING_MODEL=embedding-3           # 向量模型名称
EMBEDDING_BINDING_API_KEY=your_api_key # API密钥
EMBEDDING_DIM=2048                   # 向量维度
```

### 视觉模型配置
```bash
# 视觉模型配置（用于图片理解）
VISION_MODEL=glm-4v-plus             # 视觉模型名称
VISION_BINDING_API_KEY=your_api_key  # API密钥
VISION_TIMEOUT=60                    # 超时时间
VISION_MAX_CONCURRENT=5              # 最大并发数
VISION_CONTEXT_WINDOW=1              # 上下文窗口
VISION_RETRY_COUNT=3                 # 重试次数
VISION_CACHE_ENABLED=true            # 是否启用缓存
VISION_CACHE_TTL=3600                # 缓存TTL（秒）
```

## 🚀 性能优化建议

### 1. 系统配置优化
- **内存配置**：建议至少8GB内存，大文档处理建议16GB+
- **CPU配置**：多核CPU可以提升并发处理能力
- **存储配置**：使用SSD可以提升I/O性能

### 2. 参数调优
- **分片大小**：根据文档特点调整 `max_chunk_size`
- **并发数**：根据API限制调整 `MAX_ASYNC`
- **缓存策略**：合理配置缓存参数减少API调用

### 3. 批量处理
- 使用批量处理接口提高效率
- 合理设置批量大小避免内存溢出
- 监控处理进度和错误率

---

**TableParser** - 让文档解析更智能，让知识检索更精准！ 🚀 