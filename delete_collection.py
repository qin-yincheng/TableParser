#!/usr/bin/env python3
"""
删除向量库集合的脚本
"""

from vector_service import VectorService
from utils.logger import logger


def delete_kb_collection(kb_id: int):
    """删除指定的知识库集合"""
    try:
        vector_service = VectorService()

        # 检查集合是否存在
        if vector_service.collection_exists(kb_id):
            logger.info(f"正在删除集合 Kb_{kb_id}...")
            success = vector_service.delete_collection(kb_id)
            if success:
                logger.info(f"成功删除集合 Kb_{kb_id}")
            else:
                logger.error(f"删除集合 Kb_{kb_id} 失败")
        else:
            logger.info(f"集合 Kb_{kb_id} 不存在")

        vector_service.close()

    except Exception as e:
        logger.error(f"删除集合时发生错误: {str(e)}")


if __name__ == "__main__":
    # 删除 Kb_1 集合
    delete_kb_collection(1)
