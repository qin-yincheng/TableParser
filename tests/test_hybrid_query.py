"""
测试混合查询功能
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from query_service import QueryService
from vector_service import VectorService
from utils.logger import logger


async def test_hybrid_query():
    """测试混合查询功能"""
    try:
        # 初始化服务
        query_service = QueryService()
        vector_service = VectorService()

        # 测试参数
        kb_id = 1  # 假设知识库ID为1
        test_question = "什么是人工智能？"
        
        logger.info(f"开始测试混合查询，问题: {test_question}")
        
        # 测试混合查询
        result = await query_service.query_by_semantic(
            question=test_question,
            kb_id=kb_id,
            limit=5
        )
        
        if result.get("success"):
            logger.info("混合查询成功!")
            logger.info(f"找到 {result.get('total_count', 0)} 个结果")
            
            # 显示前3个结果
            results = result.get("results", [])
            for i, item in enumerate(results[:3]):
                logger.info(f"结果 {i+1}:")
                logger.info(f"  ID: {item.get('id')}")
                logger.info(f"  分数: {item.get('score', 'N/A')}")
                logger.info(f"  内容: {item.get('properties', {}).get('content', '')[:100]}...")
                logger.info("---")
        else:
            logger.error(f"混合查询失败: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
    finally:
        # 关闭连接
        query_service.close()
        vector_service.close()


def test_vector_service_hybrid():
    """直接测试VectorService的混合查询方法"""
    try:
        vector_service = VectorService()
        
        # 测试参数
        kb_id = 1
        test_question = "机器学习的基本概念是什么？"
        
        logger.info(f"直接测试VectorService混合查询，问题: {test_question}")
        
        # 直接调用混合查询
        results = vector_service.query_by_hybrid(
            kb_id=kb_id,
            question=test_question,
            limit=3
        )
        
        if results:
            logger.info(f"找到 {len(results)} 个结果")
            for i, item in enumerate(results[:2]):
                logger.info(f"结果 {i+1}:")
                logger.info(f"  ID: {item.get('id')}")
                logger.info(f"  分数: {item.get('score', 'N/A')}")
                logger.info(f"  内容: {item.get('properties', {}).get('content', '')[:100]}...")
                logger.info("---")
        else:
            logger.info("没有找到相关结果")
            
    except Exception as e:
        logger.error(f"VectorService测试失败: {e}")
    finally:
        vector_service.close()


if __name__ == "__main__":
    logger.info("开始测试混合查询功能...")
    
    # 测试QueryService的混合查询
    asyncio.run(test_hybrid_query())
    
    print("\n" + "="*50 + "\n")
    
    # 测试VectorService的混合查询
    test_vector_service_hybrid()
    
    logger.info("测试完成!") 