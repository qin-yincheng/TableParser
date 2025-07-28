#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向量化功能快速测试脚本
用于快速验证向量化服务和向量库的基本功能
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Any

from embedding_service import EmbeddingService
from vector_service import VectorService
from utils.logger import logger


class QuickVectorTest:
    """向量化功能快速测试类"""

    def __init__(self):
        """初始化测试类"""
        self.embedding_service = EmbeddingService()
        self.vector_service = VectorService()
        self.test_kb_id = 888  # 快速测试用知识库ID

    async def test_embedding_service(self):
        """测试向量化服务"""
        logger.info("开始测试向量化服务")

        # 测试文本
        test_texts = [
            "地方高校在2005年的招生及毕业情况",
            "Cedar大学本科招生人数为110人",
            "研究生教育发展情况",
            "表格数据统计分析",
        ]

        # 构建测试分块
        test_chunks = []
        for i, text in enumerate(test_texts):
            chunk = {
                "type": "text",
                "content": text,
                "metadata": {
                    "description": f"测试文本{i+1}",
                    "keywords": [text.split()[0], text.split()[-1]],
                },
            }
            test_chunks.append(chunk)

        # 批量生成向量
        start_time = time.time()
        vectors = await self.embedding_service.generate_embeddings_batch(test_chunks)
        end_time = time.time()

        # 统计结果
        success_count = sum(1 for v in vectors if v is not None)
        logger.info(
            f"向量化结果: {success_count}/{len(test_texts)} 成功, 耗时: {end_time - start_time:.2f}秒"
        )

        # 输出向量信息
        for i, (text, vector) in enumerate(zip(test_texts, vectors)):
            if vector:
                logger.info(f"文本{i+1}: 向量维度={len(vector)}, 前5个值={vector[:5]}")
            else:
                logger.error(f"文本{i+1}: 向量化失败")

        return vectors

    async def test_vector_service(self):
        """测试向量库服务"""
        logger.info("开始测试向量库服务")

        # 创建测试集合
        success = self.vector_service.create_collection(self.test_kb_id)
        if not success:
            logger.error("创建向量库集合失败")
            return False

        logger.info("向量库集合创建成功")

        # 生成测试向量
        test_chunk = {
            "type": "text",
            "content": "测试向量库功能",
            "metadata": {
                "description": "测试向量库插入和查询功能",
                "keywords": ["测试", "向量库"],
            },
        }

        vector = await self.embedding_service.generate_embedding(test_chunk)
        if not vector:
            logger.error("生成测试向量失败")
            return False

        # 插入测试数据
        test_chunk["doc_id"] = "quick_test"
        object_id = self.vector_service.insert_data(
            vector=vector, kb_id=self.test_kb_id, chunk=test_chunk
        )

        if object_id:
            logger.info(f"测试数据插入成功, ID: {object_id}")
        else:
            logger.error("测试数据插入失败")
            return False

        # 测试查询
        results = self.vector_service.query_by_vector(
            kb_id=self.test_kb_id, vector=vector, limit=5
        )

        logger.info(f"查询结果数量: {len(results)}")
        for i, result in enumerate(results):
            score = result.get("score", 0)
            content = result.get("properties", {}).get("content", "")
            logger.info(f"结果{i+1}: 相似度={score:.4f}, 内容={content}")

        # 清理测试集合
        self.vector_service.delete_collection(self.test_kb_id)
        logger.info("测试集合已清理")

        return True

    async def test_parser_integration(self):
        """测试解析结果集成"""
        logger.info("开始测试解析结果集成")

        # 加载解析结果
        doc_result_file = "test_results/doc_parser_test_20250727_151620.json"
        xlsx_result_file = "test_results/xlsx_parser_test_20250727_152437.json"

        test_chunks = []

        # 加载DOC结果
        if os.path.exists(doc_result_file):
            with open(doc_result_file, "r", encoding="utf-8") as f:
                doc_results = json.load(f)
                doc_file = list(doc_results.keys())[0]
                chunks = doc_results[doc_file].get("chunks", [])[:3]  # 取前3个
                for i, chunk in enumerate(chunks):
                    chunk["doc_id"] = f"doc_test_{i}"
                    test_chunks.append(chunk)

        # 加载XLSX结果
        if os.path.exists(xlsx_result_file):
            with open(xlsx_result_file, "r", encoding="utf-8") as f:
                xlsx_results = json.load(f)
                xlsx_file = list(xlsx_results.keys())[0]
                chunks = xlsx_results[xlsx_file].get("chunks", [])[:3]  # 取前3个
                for i, chunk in enumerate(chunks):
                    chunk["doc_id"] = f"xlsx_test_{i}"
                    test_chunks.append(chunk)

        if not test_chunks:
            logger.warning("没有找到解析结果文件，跳过集成测试")
            return False

        logger.info(f"找到 {len(test_chunks)} 个测试分块")

        # 创建向量库集合
        success = self.vector_service.create_collection(self.test_kb_id)
        if not success:
            logger.error("创建向量库集合失败")
            return False

        # 批量向量化和存储
        start_time = time.time()
        vectors = await self.embedding_service.generate_embeddings_batch(test_chunks)
        vector_time = time.time() - start_time

        success_count = sum(1 for v in vectors if v is not None)
        logger.info(
            f"向量化: {success_count}/{len(test_chunks)} 成功, 耗时: {vector_time:.2f}秒"
        )

        # 存储到向量库
        stored_count = 0
        for chunk, vector in zip(test_chunks, vectors):
            if vector is None:
                continue

            object_id = self.vector_service.insert_data(
                vector=vector, kb_id=self.test_kb_id, chunk=chunk
            )
            if object_id:
                stored_count += 1

        logger.info(f"存储: {stored_count}/{success_count} 成功")

        # 测试查询
        if stored_count > 0:
            query_chunk = {
                "type": "text",
                "content": "地方高校招生情况",
                "metadata": {
                    "description": "查询地方高校招生情况",
                    "keywords": ["地方高校", "招生"],
                },
            }

            query_vector = await self.embedding_service.generate_embedding(query_chunk)
            if query_vector:
                results = self.vector_service.query_by_vector(
                    kb_id=self.test_kb_id, vector=query_vector, limit=3
                )

                logger.info(f"查询结果: {len(results)} 个")
                for i, result in enumerate(results):
                    score = result.get("score", 0)
                    doc_id = result.get("properties", {}).get("doc_id", "")
                    chunk_type = result.get("properties", {}).get("chunk_type", "")
                    logger.info(
                        f"  {i+1}. 相似度={score:.4f}, 文档={doc_id}, 类型={chunk_type}"
                    )

        # 清理
        self.vector_service.delete_collection(self.test_kb_id)

        return True

    def close(self):
        """关闭连接"""
        self.vector_service.close()


async def run_quick_test():
    """运行快速测试"""
    logger.info("开始运行向量化快速测试")

    test_instance = QuickVectorTest()

    try:
        # 测试向量化服务
        await test_instance.test_embedding_service()

        # 测试向量库服务
        await test_instance.test_vector_service()

        # 测试解析结果集成
        await test_instance.test_parser_integration()

        logger.info("向量化快速测试完成")

    except Exception as e:
        logger.error(f"快速测试失败: {e}")
        raise
    finally:
        test_instance.close()


if __name__ == "__main__":
    import os

    # 运行快速测试
    asyncio.run(run_quick_test())
