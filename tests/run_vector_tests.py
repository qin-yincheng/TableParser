#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向量化测试运行脚本
支持快速测试、完整测试和性能测试等多种模式
"""

import argparse
import asyncio
import sys
import time
from datetime import datetime
from typing import Dict, Any

from test_vector_integration import TestVectorIntegration
from test_vector_quick import QuickVectorTest
from test_vector_config import (
    get_test_config,
    ensure_test_directories,
    create_test_result,
    get_test_file_path,
    is_test_file_exists,
)
from utils.logger import logger


class VectorTestRunner:
    """向量化测试运行器"""

    def __init__(self, test_mode: str = "full"):
        """
        初始化测试运行器

        Args:
            test_mode: 测试模式 ("quick", "full", "performance")
        """
        self.test_mode = test_mode
        self.config = get_test_config(test_mode)
        self.start_time = None
        self.test_results = {}

        # 确保测试目录存在
        ensure_test_directories()

    def start_test(self, test_name: str):
        """开始测试"""
        self.start_time = time.time()
        logger.info(f"开始测试: {test_name} (模式: {self.test_mode})")
        logger.info("=" * 60)

    def end_test(self, test_name: str) -> float:
        """结束测试"""
        if self.start_time:
            duration = time.time() - self.start_time
            logger.info("=" * 60)
            logger.info(f"测试完成: {test_name}, 耗时: {duration:.2f}秒")
            return duration
        return 0.0

    async def run_quick_test(self):
        """运行快速测试"""
        self.start_test("向量化快速测试")

        try:
            quick_test = QuickVectorTest()

            # 测试向量化服务
            logger.info("1. 测试向量化服务")
            await quick_test.test_embedding_service()

            # 测试向量库服务
            logger.info("2. 测试向量库服务")
            await quick_test.test_vector_service()

            # 测试解析结果集成
            logger.info("3. 测试解析结果集成")
            await quick_test.test_parser_integration()

            quick_test.close()

            duration = self.end_test("向量化快速测试")
            self.test_results["quick_test"] = {
                "status": "success",
                "duration": duration,
            }

        except Exception as e:
            logger.error(f"快速测试失败: {e}")
            self.test_results["quick_test"] = {"status": "failed", "error": str(e)}
            # 确保清理测试集合
            try:
                if (
                    "quick_test" in locals()
                    and quick_test.vector_service.collection_exists(
                        quick_test.test_kb_id
                    )
                ):
                    quick_test.vector_service.delete_collection(quick_test.test_kb_id)
            except:
                pass

    async def run_full_test(self):
        """运行完整测试"""
        self.start_test("向量化完整测试")

        try:
            test_instance = TestVectorIntegration()

            # 测试集合管理
            logger.info("1. 测试集合管理功能")
            test_instance.test_collection_management()

            # 测试DOC解析到向量化流程
            logger.info("2. 测试DOC解析到向量化流程")
            await test_instance.test_doc_parser_to_vector_pipeline()

            # 测试XLSX解析到向量化流程
            logger.info("3. 测试XLSX解析到向量化流程")
            await test_instance.test_xlsx_parser_to_vector_pipeline()

            # 测试混合文档类型
            logger.info("4. 测试混合文档类型向量化流程")
            await test_instance.test_mixed_document_pipeline()

            test_instance.close()

            duration = self.end_test("向量化完整测试")
            self.test_results["full_test"] = {"status": "success", "duration": duration}

        except Exception as e:
            logger.error(f"完整测试失败: {e}")
            self.test_results["full_test"] = {"status": "failed", "error": str(e)}
            # 确保清理测试集合
            try:
                if (
                    "test_instance" in locals()
                    and test_instance.vector_service.collection_exists(
                        test_instance.test_kb_id
                    )
                ):
                    test_instance.vector_service.delete_collection(
                        test_instance.test_kb_id
                    )
            except:
                pass

    async def run_performance_test(self):
        """运行性能测试"""
        self.start_test("向量化性能测试")

        try:
            # 检查测试数据文件
            doc_file = get_test_file_path("doc")
            xlsx_file = get_test_file_path("xlsx")

            if not is_test_file_exists("doc") or not is_test_file_exists("xlsx"):
                logger.warning("测试数据文件不存在，跳过性能测试")
                return

            # 创建性能测试实例
            test_instance = TestVectorIntegration()
            test_instance.test_kb_id = 777  # 性能测试专用ID

            # 加载大量测试数据
            import json

            all_chunks = []

            # 加载DOC数据
            with open(doc_file, "r", encoding="utf-8") as f:
                doc_results = json.load(f)
                doc_file_key = list(doc_results.keys())[0]
                doc_chunks = doc_results[doc_file_key].get("chunks", [])
                for i, chunk in enumerate(doc_chunks):
                    chunk["doc_id"] = f"perf_doc_{i}"
                    all_chunks.append(chunk)

            # 加载XLSX数据
            with open(xlsx_file, "r", encoding="utf-8") as f:
                xlsx_results = json.load(f)
                xlsx_file_key = list(xlsx_results.keys())[0]
                xlsx_chunks = xlsx_results[xlsx_file_key].get("chunks", [])
                for i, chunk in enumerate(xlsx_chunks):
                    chunk["doc_id"] = f"perf_xlsx_{i}"
                    all_chunks.append(chunk)

            logger.info(f"性能测试数据: {len(all_chunks)} 个分块")

            # 限制测试数据量
            max_chunks = self.config["vectorization"]["max_test_chunks"]
            if len(all_chunks) > max_chunks:
                all_chunks = all_chunks[:max_chunks]
                logger.info(f"限制测试数据量: {len(all_chunks)} 个分块")

            # 创建向量库集合
            success = test_instance.vector_service.create_collection(
                test_instance.test_kb_id
            )
            if not success:
                raise Exception("创建性能测试集合失败")

            # 批量向量化性能测试
            logger.info("开始批量向量化性能测试")
            start_time = time.time()
            vectors = await test_instance.embedding_service.generate_embeddings_batch(
                all_chunks
            )
            vector_time = time.time() - start_time

            success_count = sum(1 for v in vectors if v is not None)
            logger.info(
                f"向量化性能: {success_count}/{len(all_chunks)} 成功, 耗时: {vector_time:.2f}秒"
            )
            logger.info(f"平均每个分块向量化时间: {vector_time/len(all_chunks):.4f}秒")

            # 批量存储性能测试
            logger.info("开始批量存储性能测试")
            start_time = time.time()
            stored_count = 0

            for chunk, vector in zip(all_chunks, vectors):
                if vector is None:
                    continue

                try:
                    object_id = test_instance.vector_service.insert_data(
                        vector=vector, kb_id=test_instance.test_kb_id, chunk=chunk
                    )
                    if object_id:
                        stored_count += 1
                except Exception as e:
                    logger.error(f"存储分块失败: {e}")

            store_time = time.time() - start_time
            logger.info(
                f"存储性能: {stored_count}/{success_count} 成功, 耗时: {store_time:.2f}秒"
            )
            logger.info(f"平均每个分块存储时间: {store_time/len(all_chunks):.4f}秒")

            # 查询性能测试
            if stored_count > 0:
                logger.info("开始查询性能测试")
                query_times = []

                for i in range(5):  # 执行5次查询测试
                    query_chunk = {
                        "type": "text",
                        "content": f"测试查询{i+1}",
                        "metadata": {
                            "description": f"性能测试查询{i+1}",
                            "keywords": ["测试", "查询"],
                        },
                    }

                    query_vector = (
                        await test_instance.embedding_service.generate_embedding(
                            query_chunk
                        )
                    )
                    if query_vector:
                        start_time = time.time()
                        results = test_instance.vector_service.query_by_vector(
                            kb_id=test_instance.test_kb_id,
                            vector=query_vector,
                            limit=10,
                        )
                        query_time = time.time() - start_time
                        query_times.append(query_time)
                        logger.info(
                            f"查询{i+1}: 找到{len(results)}个结果, 耗时{query_time:.4f}秒"
                        )

                if query_times:
                    avg_query_time = sum(query_times) / len(query_times)
                    logger.info(f"平均查询时间: {avg_query_time:.4f}秒")

            # 清理
            test_instance.vector_service.delete_collection(test_instance.test_kb_id)
            test_instance.close()

            duration = self.end_test("向量化性能测试")
            self.test_results["performance_test"] = {
                "status": "success",
                "duration": duration,
                "total_chunks": len(all_chunks),
                "vectorization_time": vector_time,
                "storage_time": store_time,
                "successful_embeddings": success_count,
                "successful_stores": stored_count,
            }

        except Exception as e:
            logger.error(f"性能测试失败: {e}")
            self.test_results["performance_test"] = {
                "status": "failed",
                "error": str(e),
            }
            # 确保清理测试集合
            try:
                if (
                    "test_instance" in locals()
                    and test_instance.vector_service.collection_exists(
                        test_instance.test_kb_id
                    )
                ):
                    test_instance.vector_service.delete_collection(
                        test_instance.test_kb_id
                    )
            except:
                pass

    async def run_all_tests(self):
        """运行所有测试"""
        logger.info("开始运行向量化测试套件")
        logger.info(f"测试模式: {self.test_mode}")
        logger.info(f"测试配置: {self.config}")

        if self.test_mode == "quick":
            await self.run_quick_test()
        elif self.test_mode == "full":
            await self.run_full_test()
        elif self.test_mode == "performance":
            await self.run_performance_test()
        else:
            # 运行所有测试
            await self.run_quick_test()
            await self.run_full_test()
            await self.run_performance_test()

        self.print_test_summary()

    def print_test_summary(self):
        """打印测试摘要"""
        logger.info("=" * 60)
        logger.info("测试摘要")
        logger.info("=" * 60)

        for test_name, result in self.test_results.items():
            status = result.get("status", "unknown")
            if status == "success":
                duration = result.get("duration", 0)
                logger.info(f"✓ {test_name}: 成功 ({duration:.2f}秒)")

                # 显示性能测试详细信息
                if test_name == "performance_test":
                    total_chunks = result.get("total_chunks", 0)
                    vector_time = result.get("vectorization_time", 0)
                    storage_time = result.get("storage_time", 0)
                    successful_embeddings = result.get("successful_embeddings", 0)
                    successful_stores = result.get("successful_stores", 0)

                    logger.info(f"  - 总分块数: {total_chunks}")
                    logger.info(
                        f"  - 向量化成功: {successful_embeddings}/{total_chunks}"
                    )
                    logger.info(
                        f"  - 存储成功: {successful_stores}/{successful_embeddings}"
                    )
                    logger.info(f"  - 向量化时间: {vector_time:.2f}秒")
                    logger.info(f"  - 存储时间: {storage_time:.2f}秒")

            else:
                error = result.get("error", "未知错误")
                logger.error(f"✗ {test_name}: 失败 - {error}")

        logger.info("=" * 60)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="向量化测试运行器")
    parser.add_argument(
        "--mode",
        choices=["quick", "full", "performance", "all"],
        default="full",
        help="测试模式 (默认: full)",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")

    args = parser.parse_args()

    # 设置日志级别
    if args.verbose:
        import logging

        logging.getLogger().setLevel(logging.DEBUG)

    # 运行测试
    runner = VectorTestRunner(args.mode)
    asyncio.run(runner.run_all_tests())


if __name__ == "__main__":
    main()
