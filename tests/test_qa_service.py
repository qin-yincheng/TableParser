#!/usr/bin/env python3
"""
问答服务测试脚本（支持 Markdown 输出）
"""

import asyncio
import json
from qa_service import QAService
from utils.logger import logger


def print_markdown_result(result: dict):
    """格式化输出结果，支持 Markdown"""
    print(f"\n=== 问题 ===\n{result.get('question')}")
    print(f"\n=== 答案 (Markdown) ===\n{result.get('answer')}\n")  # 直接输出 Markdown，不转义
    print(f"\n=== 来源信息 (前3个) ===")
    for i, src in enumerate(result.get("sources", []), 1):
        print(f"\n来源 {i}:")
        print(f"  内容: {src.get('content', '')[:200]}...")
        print(f"  类型: {src.get('chunk_type', '')}")
        print(f"  相似度分数: {src.get('similarity_score', 0):.3f}")
        print(f"  来源信息: {src.get('source_info', {})}")


async def test_basic_qa():
    """测试基础问答功能"""
    logger.info("=== 测试基础问答功能 ===")

    with QAService() as qa_service:
        try:
            questions = [
                "近十年人均发电量是4730.25（千瓦小时）的是哪一年？",
                "2024年居民人均粮食消耗量是多少？",
                "2024年全国的地级市数有多少个？",
                "2021年全国的乡镇级区划数有多少个？",
            ]
            kb_id = 1

            for i, question in enumerate(questions, 1):
                logger.info(f"测试问题 {i}: {question}")

                result = await qa_service.answer_question(
                    question=question, kb_id=kb_id, limit=8
                )

                print(f"\n=== 问题 {i} 结果 ===")
                # 打印完整的 JSON 结果
                print(f"问题: {question}")
                print(
                    f"原始结果 (JSON): {json.dumps(result, ensure_ascii=False, indent=2)}"
                )

                # 如果成功，再用更友好的格式打印
                if result.get("success"):
                    print(f"\n--- 格式化输出 ---")
                    print_markdown_result(result)
                else:
                    print(f"问题 {i} 没有找到相关结果或出现错误: {result.get('error')}")

        except Exception as e:
            logger.error(f"基础问答测试失败: {str(e)}")


async def test_table_qa():
    """测试表格相关问答"""
    logger.info("=== 测试表格相关问答 ===")

    with QAService() as qa_service:
        try:
            # 测试表格数据问题
            question = "表格中显示了哪些大学的招生数据？"
            kb_id = 1

            result = await qa_service.answer_question(question=question, kb_id=kb_id)
            if result.get("success"):
                print_markdown_result(result)
            else:
                print(f"错误: {result.get('error')}")

        except Exception as e:
            logger.error(f"表格问答测试失败: {str(e)}")


async def test_error_cases():
    """测试错误情况"""
    logger.info("=== 测试错误情况 ===")

    with QAService() as qa_service:
        try:
            # 测试空问题
            logger.info("测试空问题")
            result1 = await qa_service.answer_question(question="", kb_id=1)
            print(f"空问题结果: {json.dumps(result1, ensure_ascii=False, indent=2)}")

            # 测试不存在的知识库
            logger.info("测试不存在的知识库")
            result2 = await qa_service.answer_question(question="测试问题", kb_id=999)
            print(f"不存在知识库结果: {json.dumps(result2, ensure_ascii=False, indent=2)}")

            # 测试无相关信息的问题
            logger.info("测试无相关信息的问题")
            result3 = await qa_service.answer_question(
                question="火星上有多少人口？", kb_id=1
            )
            print(f"无相关信息结果: {json.dumps(result3, ensure_ascii=False, indent=2)}")

        except Exception as e:
            logger.error(f"错误情况测试失败: {str(e)}")


async def test_qa_performance():
    """测试问答性能"""
    logger.info("=== 测试问答性能 ===")

    with QAService() as qa_service:
        try:
            import time

            questions = [
                "Cedar 大学在2005年招收了多少名本科新生？",
                "表格中显示了哪些大学的招生数据？",
                "为什么选择Cedar大学？",
                "招生数据统计表包含哪些信息？",
            ]

            total_time = 0
            success_count = 0

            for i, question in enumerate(questions, 1):
                logger.info(f"测试问题 {i}: {question}")

                start_time = time.time()
                result = await qa_service.answer_question(question=question, kb_id=1)
                end_time = time.time()

                question_time = end_time - start_time
                total_time += question_time

                if result.get("success"):
                    success_count += 1
                    logger.info(f"问题 {i} 成功，耗时: {question_time:.2f}秒")
                else:
                    logger.warning(f"问题 {i} 失败: {result.get('error')}")

            avg_time = total_time / len(questions)
            success_rate = success_count / len(questions) * 100

            print(f"性能测试结果:")
            print(f"  总问题数: {len(questions)}")
            print(f"  成功数: {success_count}")
            print(f"  成功率: {success_rate:.1f}%")
            print(f"  平均耗时: {avg_time:.2f}秒")
            print(f"  总耗时: {total_time:.2f}秒")

        except Exception as e:
            logger.error(f"性能测试失败: {str(e)}")


async def main():
    """主测试函数"""
    logger.info("开始问答服务测试")

    # 运行所有测试
    await test_basic_qa()
    # await test_table_qa()
    # await test_error_cases()
    # await test_qa_performance()

    logger.info("问答服务测试完成")


if __name__ == "__main__":
    asyncio.run(main())
