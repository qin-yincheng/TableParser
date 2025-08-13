import os
from dotenv import load_dotenv

load_dotenv()

LLM_CONFIG = {
    "enable_cache": os.getenv("ENABLE_LLM_CACHE", "false").lower() == "true",
    "enable_cache_extract": os.getenv("ENABLE_LLM_CACHE_FOR_EXTRACT", "false").lower()
    == "true",
    "timeout": int(os.getenv("TIMEOUT", "60")),
    "temperature": float(os.getenv("TEMPERATURE", "0")),
    "max_async": int(os.getenv("MAX_ASYNC", "4")),
    "max_tokens": int(os.getenv("MAX_TOKENS", "2048")),
    "binding": os.getenv("LLM_BINDING", "openai"),
    "model": os.getenv("LLM_MODEL", "glm-4-plus"),
    "host": os.getenv("LLM_BINDING_HOST", ""),
    "api_key": os.getenv("LLM_BINDING_API_KEY", ""),
}

EMBEDDING_CONFIG = {
    "binding": os.getenv("EMBEDDING_BINDING", "openai"),
    "model": os.getenv("EMBEDDING_MODEL", "embedding-3"),
    "dim": int(os.getenv("EMBEDDING_DIM", "2048")),
    "api_key": os.getenv("EMBEDDING_BINDING_API_KEY", ""),
    "host": os.getenv("EMBEDDING_BINDING_HOST", ""),
}

VISION_CONFIG = {
    "model": os.getenv("VISION_MODEL", "glm-4v-plus"),
    "api_key": os.getenv("VISION_BINDING_API_KEY", ""),
    "timeout": int(os.getenv("VISION_TIMEOUT", "60")),
    "max_concurrent": int(os.getenv("VISION_MAX_CONCURRENT", "5")),
    "context_window": int(os.getenv("VISION_CONTEXT_WINDOW", "1")),
    "retry_count": int(os.getenv("VISION_RETRY_COUNT", "3")),
    "cache_enabled": os.getenv("VISION_CACHE_ENABLED", "true").lower() == "true",
    "cache_ttl": int(os.getenv("VISION_CACHE_TTL", "3600")),
}
