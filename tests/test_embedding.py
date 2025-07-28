# test_embedding.py
"""
测试嵌入模型配置和功能
"""

import asyncio
import os
from utils.config import EMBEDDING_CONFIG, LLM_CONFIG
from utils.zhipu_client import zhipu_embedding_async
from embedding_service import EmbeddingService
from utils.logger import logger


async def test_embedding_config():
    """测试嵌入模型配置"""
    print("=== 嵌入模型配置测试 ===")
    print(f"EMBEDDING_BINDING: {EMBEDDING_CONFIG['binding']}")
    print(f"EMBEDDING_MODEL: {EMBEDDING_CONFIG['model']}")
    print(f"EMBEDDING_DIM: {EMBEDDING_CONFIG['dim']}")
    print(f"EMBEDDING_BINDING_HOST: {EMBEDDING_CONFIG['host']}")
    print(f"API Key: {'已配置' if EMBEDDING_CONFIG['api_key'] else '未配置'}")
    print()


async def test_single_embedding():
    """测试单个文本的向量化"""
    print("=== 单个文本向量化测试 ===")

    test_text = "这是一个测试文本，用于验证嵌入模型是否正常工作。"

    try:
        vector = await zhipu_embedding_async(
            text=test_text,
            api_key=EMBEDDING_CONFIG["api_key"],
            model=EMBEDDING_CONFIG["model"],
        )

        print(f"输入文本: {test_text}")
        print(f"向量维度: {len(vector)}")
        print(f"向量前5个值: {vector[:5]}")
        print("✅ 单个文本向量化测试成功")
        print()

        return vector

    except Exception as e:
        print(f"❌ 单个文本向量化测试失败: {str(e)}")
        print()
        return None


async def test_chunk_embedding():
    """测试分块向量化"""
    print("=== 分块向量化测试 ===")

    # 创建一个测试分块
    test_chunk = {
        "chunk_id": "test_chunk_1",
        "type": "text",
        "content": "这是一个测试段落，包含一些重要的信息。",
        "metadata": {
            "doc_id": "test_doc.docx",
            "description": "测试段落描述",
            "keywords": ["测试", "段落", "信息"],
        },
        "context": "上下文信息",
    }

    try:
        service = EmbeddingService()

        # 获取向量化文本
        embedding_text = service.get_embedding_text_for_chunk(test_chunk)
        print(f"向量化文本: {embedding_text}")
        print()

        # 生成向量
        vector = await service.generate_embedding(test_chunk)

        if vector:
            print(f"分块向量维度: {len(vector)}")
            print(f"分块向量前5个值: {vector[:5]}")
            print("✅ 分块向量化测试成功")
        else:
            print("❌ 分块向量化测试失败")
        print()

        return vector

    except Exception as e:
        print(f"❌ 分块向量化测试失败: {str(e)}")
        print()
        return None


async def test_batch_embedding():
    """测试批量向量化"""
    print("=== 批量向量化测试 ===")

    # 创建多个测试分块
    test_chunks = [
        {
            "chunk_id": "test_chunk_1",
            "type": "text",
            "content": "第一个测试段落。",
            "metadata": {"description": "第一个段落描述", "keywords": ["第一", "段落"]},
        },
        {
            "chunk_id": "test_chunk_2",
            "type": "table_full",
            "content": "| 列1 | 列2 |\n|-----|-----|\n| 数据1 | 数据2 |",
            "metadata": {"description": "测试表格描述", "keywords": ["表格", "数据"]},
        },
    ]

    try:
        service = EmbeddingService()
        vectors = await service.generate_embeddings_batch(test_chunks)

        successful_count = sum(1 for v in vectors if v is not None)
        print(f"成功生成向量: {successful_count}/{len(test_chunks)}")

        for i, vector in enumerate(vectors):
            if vector:
                print(f"分块 {i+1} 向量维度: {len(vector)}")
            else:
                print(f"分块 {i+1} 向量化失败")

        print("✅ 批量向量化测试完成")
        print()

        return vectors

    except Exception as e:
        print(f"❌ 批量向量化测试失败: {str(e)}")
        print()
        return None


async def main():
    """主测试函数"""
    print("开始嵌入模型测试...")
    print()

    # 1. 测试配置
    await test_embedding_config()

    # 2. 测试单个文本向量化
    await test_single_embedding()

    # 3. 测试分块向量化
    await test_chunk_embedding()

    # 4. 测试批量向量化
    await test_batch_embedding()

    print("嵌入模型测试完成！")


if __name__ == "__main__":
    asyncio.run(main())
