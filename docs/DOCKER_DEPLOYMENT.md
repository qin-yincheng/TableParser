# Weaviate Docker 部署配置指南

## 概述

本文档说明如何配置项目以连接Docker部署的Weaviate向量数据库。

## Docker 配置

### 1. Docker Compose 文件

创建 `docker-compose.yml` 文件：

```yaml
version: "3.4"

services:
  weaviate:
    image: semitechnologies/weaviate:latest
    container_name: weaviate
    ports:
      - "8089:8080"    # HTTP端口映射
      - "50055:50051"  # gRPC端口映射
    volumes:
      - weaviate_data:/var/lib/weaviate
    environment:
      PERSISTENCE_DATA_PATH: "/var/lib/weaviate"
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: "true"
      AUTHENTICATION_APIKEY_ENABLED: "false"
      AUTHENTICATION_OIDC_ENABLED: "false"
      AUTHORIZATION_ADMINLIST_ENABLED: "false"
      DEFAULT_VECTORIZER_MODULE: "none"
      ENABLE_MODULES: ""
      QUERY_DEFAULTS_LIMIT: "25"
      WEAVIATE_HOSTNAME: "weaviate"

  console:
    image: semitechnologies/weaviate-console
    container_name: weaviate-console
    ports:
      - "3000:80"
    environment:
      WCS_CONSOLE_WEAVIATE_URL: "http://weaviate:8080"
    depends_on:
      - weaviate

volumes:
  weaviate_data:
```

### 2. 启动服务

```bash
# 启动Weaviate服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs weaviate
```

## 项目配置

### 1. 配置文件

项目已配置 `config/config.yaml` 文件，包含以下设置：

```yaml
database:
  weaviate:
    host: "localhost"      # Docker主机地址
    port: 8089            # Docker映射的HTTP端口
    grpc_host: "localhost" # Docker主机地址
    grpc_port: 50055      # Docker映射的gRPC端口
    scheme: "http"         # 协议类型
    api_key: null          # Docker配置中禁用了API key
    timeout: [5, 30]       # 连接超时设置
```

### 2. 代码修改

已修改 `connector.py` 中的默认端口配置：
- HTTP端口：8080 → 8089
- gRPC端口：60051 → 50055

## 测试连接

### 1. 运行测试脚本

```bash
python test_weaviate_connection.py
```

### 2. 手动测试

#### 检查Weaviate服务状态

```bash
# 检查容器状态
docker ps | grep weaviate

# 测试HTTP连接
curl http://localhost:8089/v1/.well-known/ready

# 测试gRPC连接
telnet localhost 50055
```

#### 访问Weaviate控制台

打开浏览器访问：http://localhost:3000

## 故障排除

### 1. 连接失败

**问题：** 无法连接到Weaviate

**解决方案：**
- 检查Docker容器是否运行：`docker ps`
- 检查端口映射：`docker port weaviate`
- 检查防火墙设置
- 验证配置文件格式

### 2. 端口冲突

**问题：** 端口已被占用

**解决方案：**
- 修改Docker Compose中的端口映射
- 同时更新 `config/config.yaml` 中的端口配置

### 3. 权限问题

**问题：** 数据目录权限错误

**解决方案：**
```bash
# 修复数据目录权限
sudo chown -R 1000:1000 ./weaviate_data
```

## 使用示例

### 1. 基本连接测试

```python
from connector import WeaviateConnector

# 创建连接器
connector = WeaviateConnector()

# 连接数据库
connector.connect()

# 检查连接状态
if connector.is_connected():
    print("连接成功！")
    
# 关闭连接
connector.disconnect()
```

### 2. 创建集合

```python
from vector_service import VectorService

# 创建向量服务
vector_service = VectorService()

# 创建知识库集合
kb_id = 1
success = vector_service.create_collection(kb_id)

if success:
    print(f"知识库 {kb_id} 集合创建成功")
```

## 注意事项

1. **数据持久化**：数据存储在Docker卷中，重启容器不会丢失数据
2. **内存使用**：Weaviate默认使用较多内存，建议至少4GB可用内存
3. **网络配置**：确保Docker网络配置正确，容器间可以通信
4. **版本兼容**：确保Weaviate客户端版本与服务器版本兼容

## 相关链接

- [Weaviate官方文档](https://weaviate.io/developers/weaviate)
- [Weaviate Docker部署](https://weaviate.io/developers/weaviate/installation/docker-compose)
- [Weaviate Python客户端](https://weaviate.io/developers/weaviate/client-libraries/python) 