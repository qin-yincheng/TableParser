"""
混合查询使用示例
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from query_service import QueryService
from vector_service import VectorService
from utils.logger import logger


async def example_hybrid_query():
    """混合查询使用示例"""
    
    # 初始化服务
    query_service = QueryService()
    vector_service = VectorService()
    
    try:
        # 示例问题
        questions = [
            "什么是机器学习？",
            "深度学习与传统机器学习的区别是什么？",
            "神经网络的基本原理是什么？",
            "如何评估机器学习模型的性能？"
        ]
        
        kb_id = 1  # 假设知识库ID为1
        
        logger.info("=== 混合查询示例 ===")
        
        for i, question in enumerate(questions, 1):
            logger.info(f"\n问题 {i}: {question}")
            
            # 使用QueryService进行混合查询
            result = await query_service.query_by_semantic(
                question=question,
                kb_id=kb_id,
                limit=3
            )
            
            if result.get("success"):
                results = result.get("results", [])
                logger.info(f"找到 {len(results)} 个相关结果:")
                
                for j, item in enumerate(results, 1):
                    score = item.get("score", "N/A")
                    content = item.get("properties", {}).get("content", "")
                    chunk_type = item.get("properties", {}).get("chunk_type", "")
                    
                    logger.info(f"  结果 {j}:")
                    logger.info(f"    分数: {score}")
                    logger.info(f"    类型: {chunk_type}")
                    logger.info(f"    内容: {content[:100]}...")
            else:
                logger.error(f"查询失败: {result.get('error')}")
                
    except Exception as e:
        logger.error(f"示例执行失败: {e}")
    finally:
        # 关闭连接
        query_service.close()
        vector_service.close()


def example_direct_vector_service():
    """直接使用VectorService的混合查询示例"""
    
    vector_service = VectorService()
    
    try:
        logger.info("\n=== 直接使用VectorService混合查询示例 ===")
        
        # 测试问题
        test_question = "人工智能的发展历程"
        kb_id = 1
        
        logger.info(f"问题: {test_question}")
        
        # 直接调用混合查询
        results = vector_service.query_by_hybrid(
            kb_id=kb_id,
            question=test_question,
            limit=5,
            distance_threshold=0.8  # 设置距离阈值
        )
        
        if results:
            logger.info(f"找到 {len(results)} 个结果:")
            for i, item in enumerate(results, 1):
                score = item.get("score", "N/A")
                content = item.get("properties", {}).get("content", "")
                doc_id = item.get("properties", {}).get("doc_id", "")
                
                logger.info(f"  结果 {i}:")
                logger.info(f"    文档ID: {doc_id}")
                logger.info(f"    相似度分数: {score}")
                logger.info(f"    内容预览: {content[:80]}...")
        else:
            logger.info("没有找到相关结果")
            
    except Exception as e:
        logger.error(f"VectorService示例失败: {e}")
    finally:
        vector_service.close()


async def main():
    """主函数"""
    logger.info("开始混合查询示例...")
    
    # 示例1: 使用QueryService
    await example_hybrid_query()
    
    # 示例2: 直接使用VectorService
    example_direct_vector_service()
    
    logger.info("\n示例完成!")


if __name__ == "__main__":
    asyncio.run(main()) 