# TableParser 项目结构说明

## 目录结构

```
TableParser/
│
├── parsers/                    # 文档解析器相关代码
│   ├── __init__.py
│   ├── doc_parser.py           # Word文档解析
│   ├── xlsx_parser.py          # Excel文档解析（待实现）
│   └── chunker.py              # 分块与结构化逻辑
│
├── vector_service.py           # 向量化与向量库交互
├── connector.py                # 外部服务/数据库/向量库连接器
├── operations.py               # 主要操作流程
│
├── utils/                      # 工具函数
│   └── __init__.py
│
├── config/                     # 配置文件
│   └── config.yaml
│
├── tests/                      # 测试代码
│   └── __init__.py
│
├── docs/                       # 设计文档、开发方案、说明书等
│   ├── RAG系统开发方案.md
│   └── 构建RAG系统以实现Word和Excel表格的精准解析与检索.md
│
├── README.md                   # 项目说明
```

## 说明
- **parsers/**：存放各类文档解析器，便于扩展。
- **chunker.py**：分块与结构化逻辑。
- **vector_service.py**：内容向量化及与向量库交互。
- **connector.py**：外部服务连接。
- **operations.py**：主流程调度。
- **utils/**：通用工具函数。
- **config/**：集中管理配置。
- **tests/**：测试代码。
- **docs/**：文档资料。

如需扩展新文档类型或功能，建议在对应目录下新建模块。 