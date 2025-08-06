import logging
import os

# 设置环境变量来控制日志级别
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()

# 创建自定义的日志格式，更简洁
if log_level == 'DEBUG':
    format_str = "%(asctime)s %(levelname)s %(name)s: %(message)s"
else:
    format_str = "%(levelname)s: %(message)s"

# 配置日志
logging.basicConfig(
    level=getattr(logging, log_level),
    format=format_str,
    datefmt='%H:%M:%S' if log_level == 'DEBUG' else None
)

# 创建logger
logger = logging.getLogger("TableParser")

# 设置第三方库的日志级别为WARNING，减少噪音
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("weaviate").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
