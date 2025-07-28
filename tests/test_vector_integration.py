#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向量化加入库集成测试
测试从文档解析结果到向量化再到向量库存储的完整流程
"""

import asyncio
import json
import os
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

from embedding_service import EmbeddingService
from vector_service import VectorService
from utils.logger import logger


class TestVectorIntegration:
    """向量化加入库集成测试类"""

    def __init__(self):
        """初始化测试类"""
        self.embedding_service = EmbeddingService()
        self.vector_service = VectorService()
        self.test_kb_id = 999  # 测试用知识库ID
        self.test_results_dir = "test_results/vector_integration_test"

        # 确保测试结果目录存在
        os.makedirs(self.test_results_dir, exist_ok=True)

    def setup_method(self):
        """每个测试方法前的设置"""
        # 清理测试集合
        if self.vector_service.collection_exists(self.test_kb_id):
            self.vector_service.delete_collection(self.test_kb_id)

    def teardown_method(self):
        """每个测试方法后的清理"""
        # 清理测试集合
        if self.vector_service.collection_exists(self.test_kb_id):
            self.vector_service.delete_collection(self.test_kb_id)

    async def test_doc_parser_to_vector_pipeline(self):
        """测试DOC解析到向量化的完整流程"""
        logger.info("开始测试DOC解析到向量化的完整流程")

        # 加载DOC解析结果
        doc_result_file = "test_results/doc_parser_test_20250727_151620.json"
        if not os.path.exists(doc_result_file):
            logger.warning(f"DOC解析结果文件不存在: {doc_result_file}")
            return

        with open(doc_result_file, "r", encoding="utf-8") as f:
            doc_results = json.load(f)

        # 获取第一个文档的解析结果
        doc_file = list(doc_results.keys())[0]
        doc_data = doc_results[doc_file]
        chunks = doc_data.get("chunks", [])

        logger.info(f"处理文档: {doc_file}, 分块数量: {len(chunks)}")

        # 创建向量库集合
        success = self.vector_service.create_collection(self.test_kb_id)
        if not success:
            logger.error("创建向量库集合失败")
            return

        # 测试向量化和存储
        await self._test_chunks_vectorization(chunks, "doc")

        # 测试查询功能
        await self._test_vector_query()

        logger.info("DOC解析到向量化流程测试完成")

    async def test_xlsx_parser_to_vector_pipeline(self):
        """测试XLSX解析到向量化的完整流程"""
        logger.info("开始测试XLSX解析到向量化的完整流程")

        # 加载XLSX解析结果
        xlsx_result_file = "test_results/xlsx_parser_test_20250727_152437.json"
        if not os.path.exists(xlsx_result_file):
            logger.warning(f"XLSX解析结果文件不存在: {xlsx_result_file}")
            return

        with open(xlsx_result_file, "r", encoding="utf-8") as f:
            xlsx_results = json.load(f)

        # 获取第一个文档的解析结果
        xlsx_file = list(xlsx_results.keys())[0]
        xlsx_data = xlsx_results[xlsx_file]
        chunks = xlsx_data.get("chunks", [])

        logger.info(f"处理文档: {xlsx_file}, 分块数量: {len(chunks)}")

        # 创建向量库集合
        success = self.vector_service.create_collection(self.test_kb_id)
        if not success:
            logger.error("创建向量库集合失败")
            return

        # 测试向量化和存储
        await self._test_chunks_vectorization(chunks, "xlsx")

        # 测试查询功能
        await self._test_vector_query()

        logger.info("XLSX解析到向量化流程测试完成")

    async def _test_chunks_vectorization(
        self, chunks: List[Dict[str, Any]], doc_type: str
    ):
        """测试分块向量化"""
        logger.info(f"开始测试{len(chunks)}个分块的向量化")

        # 选择前10个分块进行测试（避免测试时间过长）
        test_chunks = chunks[:10]

        # 批量生成向量
        start_time = time.time()
        vectors = await self.embedding_service.generate_embeddings_batch(test_chunks)
        vector_time = time.time() - start_time

        # 统计向量化结果
        success_count = sum(1 for v in vectors if v is not None)
        logger.info(
            f"向量化完成: {success_count}/{len(test_chunks)} 成功, 耗时: {vector_time:.2f}秒"
        )

        # 存储到向量库
        start_time = time.time()
        stored_count = 0

        for i, (chunk, vector) in enumerate(zip(test_chunks, vectors)):
            if vector is None:
                continue

            # 为chunk添加doc_id字段
            chunk["doc_id"] = f"test_{doc_type}_{i}"

            try:
                object_id = self.vector_service.insert_data(
                    vector=vector, kb_id=self.test_kb_id, chunk=chunk
                )
                if object_id:
                    stored_count += 1
            except Exception as e:
                logger.error(f"存储分块 {i} 失败: {e}")

        store_time = time.time() - start_time
        logger.info(
            f"存储完成: {stored_count}/{success_count} 成功, 耗时: {store_time:.2f}秒"
        )

        # 保存测试结果
        test_result = {
            "test_time": datetime.now().isoformat(),
            "doc_type": doc_type,
            "total_chunks": len(test_chunks),
            "vectorization_success": success_count,
            "storage_success": stored_count,
            "vectorization_time": vector_time,
            "storage_time": store_time,
            "total_time": vector_time + store_time,
        }

        result_file = (
            f"{self.test_results_dir}/vector_test_{doc_type}_{int(time.time())}.json"
        )
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(test_result, f, ensure_ascii=False, indent=2)

        logger.info(f"测试结果已保存到: {result_file}")

    async def _test_vector_query(self):
        """测试向量查询功能"""
        logger.info("开始测试向量查询功能")

        # 生成测试查询向量
        test_text = "地方高校招生情况"
        test_chunk = {
            "type": "text",
            "content": test_text,
            "metadata": {
                "description": "测试查询文本",
                "keywords": ["地方高校", "招生"],
            },
        }

        # 生成查询向量
        query_vector = await self.embedding_service.generate_embedding(test_chunk)
        if query_vector is None:
            logger.warning("无法生成查询向量，跳过查询测试")
            return

        # 执行向量查询
        results = self.vector_service.query_by_vector(
            kb_id=self.test_kb_id, vector=query_vector, limit=5
        )

        logger.info(f"查询到 {len(results)} 个相关结果")

        # 输出查询结果
        for i, result in enumerate(results):
            score = result.get("score", 0)
            properties = result.get("properties", {})
            content = (
                properties.get("content", "")[:100] + "..."
                if len(properties.get("content", "")) > 100
                else properties.get("content", "")
            )
            logger.info(f"结果 {i+1}: 相似度={score:.4f}, 内容={content}")

    async def test_mixed_document_pipeline(self):
        """测试混合文档类型的向量化流程"""
        logger.info("开始测试混合文档类型的向量化流程")

        # 创建向量库集合
        success = self.vector_service.create_collection(self.test_kb_id)
        if not success:
            logger.error("创建向量库集合失败")
            return

        # 加载两种类型的解析结果
        doc_chunks = []
        xlsx_chunks = []

        # 加载DOC结果
        doc_result_file = "test_results/doc_parser_test_20250727_151620.json"
        if os.path.exists(doc_result_file):
            with open(doc_result_file, "r", encoding="utf-8") as f:
                doc_results = json.load(f)
                doc_file = list(doc_results.keys())[0]
                doc_chunks = doc_results[doc_file].get("chunks", [])[:5]  # 取前5个

        # 加载XLSX结果
        xlsx_result_file = "test_results/xlsx_parser_test_20250727_152437.json"
        if os.path.exists(xlsx_result_file):
            with open(xlsx_result_file, "r", encoding="utf-8") as f:
                xlsx_results = json.load(f)
                xlsx_file = list(xlsx_results.keys())[0]
                xlsx_chunks = xlsx_results[xlsx_file].get("chunks", [])[:5]  # 取前5个

        # 合并所有分块
        all_chunks = []
        for i, chunk in enumerate(doc_chunks):
            chunk["doc_id"] = f"test_doc_{i}"
            all_chunks.append(chunk)

        for i, chunk in enumerate(xlsx_chunks):
            chunk["doc_id"] = f"test_xlsx_{i}"
            all_chunks.append(chunk)

        logger.info(
            f"混合测试: DOC分块 {len(doc_chunks)} 个, XLSX分块 {len(xlsx_chunks)} 个"
        )

        # 批量向量化和存储
        await self._test_chunks_vectorization(all_chunks, "mixed")

        # 测试不同类型的查询
        await self._test_mixed_queries()

        logger.info("混合文档类型向量化流程测试完成")

    async def _test_mixed_queries(self):
        """测试混合查询"""
        logger.info("开始测试混合查询")

        # 测试文本查询
        text_queries = ["地方高校招生情况", "研究生教育发展", "表格数据统计"]

        for query_text in text_queries:
            logger.info(f"查询: {query_text}")

            test_chunk = {
                "type": "text",
                "content": query_text,
                "metadata": {
                    "description": f"查询: {query_text}",
                    "keywords": [query_text],
                },
            }

            query_vector = await self.embedding_service.generate_embedding(test_chunk)
            if query_vector is None:
                continue

            results = self.vector_service.query_by_vector(
                kb_id=self.test_kb_id, vector=query_vector, limit=3
            )

            logger.info(f"  找到 {len(results)} 个相关结果")
            for i, result in enumerate(results):
                score = result.get("score", 0)
                doc_id = result.get("properties", {}).get("doc_id", "")
                chunk_type = result.get("properties", {}).get("chunk_type", "")
                logger.info(
                    f"    {i+1}. 相似度={score:.4f}, 文档={doc_id}, 类型={chunk_type}"
                )

    def test_collection_management(self):
        """测试集合管理功能"""
        logger.info("开始测试集合管理功能")

        # 先清理可能存在的测试集合
        if self.vector_service.collection_exists(self.test_kb_id):
            self.vector_service.delete_collection(self.test_kb_id)
            logger.info("清理了已存在的测试集合")

        # 测试创建集合
        success = self.vector_service.create_collection(self.test_kb_id)
        if not success:
            logger.error("创建集合失败")
            return

        # 测试集合存在性检查
        exists = self.vector_service.collection_exists(self.test_kb_id)
        if not exists:
            logger.error("集合存在性检查失败")
            return

        # 测试获取集合信息
        info = self.vector_service.get_collection_info(self.test_kb_id)
        if info is None:
            logger.error("获取集合信息失败")
            return
        logger.info(f"集合信息: {info}")

        # 测试删除集合
        success = self.vector_service.delete_collection(self.test_kb_id)
        if not success:
            logger.error("删除集合失败")
            return

        # 等待一下再验证删除
        time.sleep(1)

        # 验证集合已删除
        exists = self.vector_service.collection_exists(self.test_kb_id)
        if exists:
            logger.error("集合删除验证失败")
            return

        logger.info("集合管理功能测试完成")

    def close(self):
        """关闭连接"""
        self.vector_service.close()


async def run_vector_integration_tests():
    """运行向量化集成测试"""
    logger.info("开始运行向量化集成测试")

    test_instance = TestVectorIntegration()

    try:
        # 测试集合管理
        test_instance.test_collection_management()

        # 测试DOC解析到向量化流程
        await test_instance.test_doc_parser_to_vector_pipeline()

        # 测试XLSX解析到向量化流程
        await test_instance.test_xlsx_parser_to_vector_pipeline()

        # 测试混合文档类型
        await test_instance.test_mixed_document_pipeline()

        logger.info("所有向量化集成测试完成")

    except Exception as e:
        logger.error(f"向量化集成测试失败: {e}")
        raise
    finally:
        test_instance.close()


if __name__ == "__main__":
    # 运行测试
    asyncio.run(run_vector_integration_tests())
