#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向量化服务测试脚本
利用现有的分块测试结果测试向量化服务功能
"""

import asyncio
import json
import time
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import numpy as np

from embedding_service import EmbeddingService
from utils.logger import logger
from utils.config import EMBEDDING_CONFIG


class EmbeddingServiceTester:
    """向量化服务测试类"""

    def __init__(self):
        """初始化测试器"""
        self.embedding_service = EmbeddingService()
        self.test_results = {
            "test_info": {
                "timestamp": datetime.now().isoformat(),
                "embedding_model": EMBEDDING_CONFIG["model"],
                "vector_dimension": EMBEDDING_CONFIG["dim"],
                "test_data_sources": [
                    "test_results/doc_parser_test_20250727_151620.json",
                    "test_results/xlsx_parser_test_20250727_152437.json",
                ],
            },
            "test_results": [],
            "batch_test_results": {},
            "statistics": {},
        }

    def load_test_chunks(self) -> List[Dict[str, Any]]:
        """加载测试分块数据"""
        chunks = []

        # 加载DOC文件测试结果
        doc_file = "test_results/doc_parser_test_20250727_151620.json"
        if os.path.exists(doc_file):
            with open(doc_file, "r", encoding="utf-8") as f:
                doc_data = json.load(f)
                for file_key, file_data in doc_data.items():
                    if "chunks" in file_data:
                        chunks.extend(file_data["chunks"])
                        logger.info(f"加载DOC文件分块: {len(file_data['chunks'])}个")

        # 加载XLSX文件测试结果
        xlsx_file = "test_results/xlsx_parser_test_20250727_152437.json"
        if os.path.exists(xlsx_file):
            with open(xlsx_file, "r", encoding="utf-8") as f:
                xlsx_data = json.load(f)
                for file_key, file_data in xlsx_data.items():
                    if "chunks" in file_data:
                        chunks.extend(file_data["chunks"])
                        logger.info(f"加载XLSX文件分块: {len(file_data['chunks'])}个")

        logger.info(f"总计加载分块: {len(chunks)}个")
        return chunks

    async def test_single_embedding(
        self, chunk: Dict[str, Any], chunk_id: str
    ) -> Dict[str, Any]:
        """测试单个分块的向量化"""
        start_time = time.time()

        try:
            # 生成向量
            vector = await self.embedding_service.generate_embedding(chunk)
            processing_time = time.time() - start_time

            if vector is not None:
                # 验证向量
                vector_dim = len(vector)
                vector_stats = self._analyze_vector(vector)

                result = {
                    "chunk_id": chunk_id,
                    "original_chunk": chunk,
                    "embedding_text": self.embedding_service.get_embedding_text_for_chunk(
                        chunk
                    ),
                    "vector": vector,
                    "vector_dimension": vector_dim,
                    "vector_stats": vector_stats,
                    "processing_time": processing_time,
                    "success": True,
                    "error": None,
                }
            else:
                result = {
                    "chunk_id": chunk_id,
                    "original_chunk": chunk,
                    "embedding_text": self.embedding_service.get_embedding_text_for_chunk(
                        chunk
                    ),
                    "vector": None,
                    "vector_dimension": None,
                    "vector_stats": None,
                    "processing_time": processing_time,
                    "success": False,
                    "error": "向量生成失败",
                }

        except Exception as e:
            processing_time = time.time() - start_time
            result = {
                "chunk_id": chunk_id,
                "original_chunk": chunk,
                "embedding_text": self.embedding_service.get_embedding_text_for_chunk(
                    chunk
                ),
                "vector": None,
                "vector_dimension": None,
                "vector_stats": None,
                "processing_time": processing_time,
                "success": False,
                "error": str(e),
            }

        return result

    async def test_batch_embedding(
        self, chunks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """测试批量向量化"""
        logger.info(f"开始批量向量化测试，共{len(chunks)}个分块")

        start_time = time.time()
        results = []

        # 分批处理，避免并发过多
        batch_size = 10
        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i : i + batch_size]
            batch_tasks = []

            for j, chunk in enumerate(batch_chunks):
                chunk_id = f"batch_{i+j+1}"
                task = self.test_single_embedding(chunk, chunk_id)
                batch_tasks.append(task)

            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            results.extend(batch_results)

            logger.info(
                f"完成批次 {i//batch_size + 1}/{(len(chunks)-1)//batch_size + 1}"
            )

        total_time = time.time() - start_time

        # 统计批量测试结果
        successful_count = sum(1 for r in results if r and r.get("success", False))
        failed_count = len(results) - successful_count

        self.test_results["batch_test_results"] = {
            "total_chunks": len(chunks),
            "successful_embeddings": successful_count,
            "failed_embeddings": failed_count,
            "total_processing_time": total_time,
            "average_time_per_chunk": total_time / len(chunks) if chunks else 0,
            "success_rate": successful_count / len(chunks) if chunks else 0,
        }

        return results

    def _analyze_vector(self, vector: List[float]) -> Dict[str, Any]:
        """分析向量统计信息"""
        vector_array = np.array(vector)
        return {
            "mean": float(np.mean(vector_array)),
            "std": float(np.std(vector_array)),
            "min": float(np.min(vector_array)),
            "max": float(np.max(vector_array)),
            "norm": float(np.linalg.norm(vector_array)),
        }

    def analyze_test_results(self, results: List[Dict[str, Any]]):
        """分析测试结果"""
        successful_results = [r for r in results if r and r.get("success", False)]
        failed_results = [r for r in results if r and not r.get("success", False)]

        # 按分块类型统计
        chunk_type_stats = {}
        for result in successful_results:
            chunk_type = result["original_chunk"].get("type", "unknown")
            if chunk_type not in chunk_type_stats:
                chunk_type_stats[chunk_type] = {
                    "count": 0,
                    "avg_processing_time": 0,
                    "avg_vector_norm": 0,
                }

            chunk_type_stats[chunk_type]["count"] += 1
            chunk_type_stats[chunk_type]["avg_processing_time"] += result[
                "processing_time"
            ]
            chunk_type_stats[chunk_type]["avg_vector_norm"] += result["vector_stats"][
                "norm"
            ]

        # 计算平均值
        for chunk_type in chunk_type_stats:
            count = chunk_type_stats[chunk_type]["count"]
            chunk_type_stats[chunk_type]["avg_processing_time"] /= count
            chunk_type_stats[chunk_type]["avg_vector_norm"] /= count

        # 向量维度验证
        vector_dimensions = [
            r["vector_dimension"] for r in successful_results if r["vector_dimension"]
        ]
        expected_dim = EMBEDDING_CONFIG["dim"]
        dimension_consistent = all(dim == expected_dim for dim in vector_dimensions)

        self.test_results["statistics"] = {
            "total_tested": len(results),
            "successful_count": len(successful_results),
            "failed_count": len(failed_results),
            "success_rate": len(successful_results) / len(results) if results else 0,
            "chunk_type_stats": chunk_type_stats,
            "vector_dimension_validation": {
                "expected_dimension": expected_dim,
                "actual_dimensions": list(set(vector_dimensions)),
                "consistent": dimension_consistent,
            },
            "processing_time_stats": {
                "min": (
                    min([r["processing_time"] for r in successful_results])
                    if successful_results
                    else 0
                ),
                "max": (
                    max([r["processing_time"] for r in successful_results])
                    if successful_results
                    else 0
                ),
                "avg": (
                    sum([r["processing_time"] for r in successful_results])
                    / len(successful_results)
                    if successful_results
                    else 0
                ),
            },
        }

    def save_test_results(self, results: List[Dict[str, Any]]):
        """保存测试结果"""
        self.test_results["test_results"] = results

        # 创建保存目录
        save_dir = "test_results/embedding_test_results"
        os.makedirs(save_dir, exist_ok=True)

        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"embedding_test_{timestamp}.json"
        filepath = os.path.join(save_dir, filename)

        # 保存完整结果
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)

        # 保存向量数据（用于后续存储测试）
        vectors_data = {
            "vectors": [],
            "metadata": {
                "source": "embedding_test",
                "timestamp": timestamp,
                "model": EMBEDDING_CONFIG["model"],
                "dimension": EMBEDDING_CONFIG["dim"],
            },
        }

        for result in results:
            if result and result.get("success", False):
                vectors_data["vectors"].append(
                    {
                        "id": result["chunk_id"],
                        "vector": result["vector"],
                        "text": result["embedding_text"],
                        "chunk_type": result["original_chunk"].get("type"),
                        "metadata": result["original_chunk"].get("metadata", {}),
                    }
                )

        vectors_filename = f"embedding_vectors_{timestamp}.json"
        vectors_filepath = os.path.join(save_dir, vectors_filename)

        with open(vectors_filepath, "w", encoding="utf-8") as f:
            json.dump(vectors_data, f, ensure_ascii=False, indent=2)

        logger.info(f"测试结果已保存到: {filepath}")
        logger.info(f"向量数据已保存到: {vectors_filepath}")

        return filepath, vectors_filepath

    def print_test_summary(self):
        """打印测试摘要"""
        stats = self.test_results["statistics"]
        batch_stats = self.test_results["batch_test_results"]

        print("\n" + "=" * 60)
        print("向量化服务测试摘要")
        print("=" * 60)
        print(f"测试时间: {self.test_results['test_info']['timestamp']}")
        print(f"向量模型: {self.test_results['test_info']['embedding_model']}")
        print(f"向量维度: {self.test_results['test_info']['vector_dimension']}")
        print()

        print("批量测试结果:")
        print(f"  总分块数: {batch_stats['total_chunks']}")
        print(f"  成功向量化: {batch_stats['successful_embeddings']}")
        print(f"  失败数量: {batch_stats['failed_embeddings']}")
        print(f"  成功率: {batch_stats['success_rate']:.2%}")
        print(f"  总耗时: {batch_stats['total_processing_time']:.2f}秒")
        print(f"  平均耗时: {batch_stats['average_time_per_chunk']:.3f}秒/分块")
        print()

        print("向量维度验证:")
        dim_validation = stats["vector_dimension_validation"]
        print(f"  期望维度: {dim_validation['expected_dimension']}")
        print(f"  实际维度: {dim_validation['actual_dimensions']}")
        print(f"  维度一致性: {'✓' if dim_validation['consistent'] else '✗'}")
        print()

        print("分块类型统计:")
        for chunk_type, type_stats in stats["chunk_type_stats"].items():
            print(
                f"  {chunk_type}: {type_stats['count']}个, "
                f"平均耗时: {type_stats['avg_processing_time']:.3f}秒, "
                f"平均向量范数: {type_stats['avg_vector_norm']:.3f}"
            )
        print()

        print("处理时间统计:")
        time_stats = stats["processing_time_stats"]
        print(f"  最短时间: {time_stats['min']:.3f}秒")
        print(f"  最长时间: {time_stats['max']:.3f}秒")
        print(f"  平均时间: {time_stats['avg']:.3f}秒")
        print("=" * 60)


async def main():
    """主测试函数"""
    logger.info("开始向量化服务测试")

    # 创建测试器
    tester = EmbeddingServiceTester()

    # 加载测试数据
    chunks = tester.load_test_chunks()
    if not chunks:
        logger.error("没有找到测试分块数据")
        return

    # 执行批量测试
    results = await tester.test_batch_embedding(chunks)

    # 分析结果
    tester.analyze_test_results(results)

    # 保存结果
    test_file, vectors_file = tester.save_test_results(results)

    # 打印摘要
    tester.print_test_summary()

    logger.info("向量化服务测试完成")


if __name__ == "__main__":
    asyncio.run(main())
