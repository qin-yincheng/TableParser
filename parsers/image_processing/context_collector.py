"""
上下文收集器 - 为图片收集上下文信息
"""

from typing import List, Dict
import sys
import os

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from utils.logger import logger


class ContextCollector:
    """为图片收集上下文信息"""

    def __init__(self, context_window: int = 3):
        """
        初始化上下文收集器

        Args:
            context_window: 上下文窗口大小，默认为3
        """
        self.context_window = context_window
        logger.debug(f"初始化ContextCollector，上下文窗口大小: {context_window}")

    def collect_context_for_image(
        self, image_block: Dict, all_blocks: List[Dict]
    ) -> Dict:
        """
        为图片收集上下文信息

        Args:
            image_block: 图片块字典
            all_blocks: 所有文档块列表

        Returns:
            包含上下文信息的字典
        """
        try:
            # 找到图片块在all_blocks中的位置
            image_index = all_blocks.index(image_block)

            # 收集前文
            preceding_blocks = []
            for i in range(max(0, image_index - self.context_window), image_index):
                if all_blocks[i]["type"] == "text":
                    preceding_blocks.append(all_blocks[i]["content"])

            # 收集后文
            following_blocks = []
            for i in range(
                image_index + 1,
                min(len(all_blocks), image_index + self.context_window + 1),
            ):
                if all_blocks[i]["type"] == "text":
                    following_blocks.append(all_blocks[i]["content"])

            context = {
                "preceding": " ".join(preceding_blocks),
                "following": " ".join(following_blocks),
                "document_title": self.get_document_title(all_blocks),
                "image_position": f"第{image_index + 1}个内容块",
            }

            logger.debug(f"为图片收集上下文: {context}")
            return context

        except Exception as e:
            logger.error(f"上下文收集失败: {str(e)}")
            return {
                "preceding": "",
                "following": "",
                "document_title": "",
                "image_position": "",
            }

    def get_document_title(self, all_blocks: List[Dict]) -> str:
        """
        获取文档标题

        Args:
            all_blocks: 所有文档块列表

        Returns:
            文档标题字符串
        """
        try:
            # 尝试从第一个文本块获取标题
            for block in all_blocks:
                if block["type"] == "text" and block["content"].strip():
                    content = block["content"].strip()
                    # 如果内容较短且包含标题特征，认为是标题
                    if len(content) < 100 and not content.endswith(
                        (".", "。", "！", "？")
                    ):
                        logger.debug(f"找到文档标题: {content}")
                        return content

            logger.debug("未找到合适的文档标题，使用默认标题")
            return "未知文档"

        except Exception as e:
            logger.error(f"获取文档标题失败: {str(e)}")
            return "未知文档"


if __name__ == "__main__":
    """测试ContextCollector功能"""
    import json

    # 创建测试数据
    mock_all_blocks = [
        {
            "type": "text",
            "content": "2023年销售业绩报告",
            "metadata": {"paragraph_index": 1},
        },
        {
            "type": "text",
            "content": "本报告详细分析了2023年各季度的销售情况",
            "metadata": {"paragraph_index": 2},
        },
        {
            "type": "image",
            "content": "storage/images/doc1/chart1.png",
            "metadata": {"image_index": 0},
        },
        {
            "type": "text",
            "content": "从图表可以看出，第一季度表现最佳",
            "metadata": {"paragraph_index": 3},
        },
        {
            "type": "text",
            "content": "建议加强第三季度的营销力度",
            "metadata": {"paragraph_index": 4},
        },
    ]

    mock_image_block = mock_all_blocks[2]  # 直接使用all_blocks中的图片块

    # 创建ContextCollector实例
    collector = ContextCollector(context_window=1)  # 使用较小的上下文窗口以匹配期望结果

    # 测试上下文收集
    print("=== 测试上下文收集 ===")
    context = collector.collect_context_for_image(mock_image_block, mock_all_blocks)
    print(f"收集的上下文: {json.dumps(context, ensure_ascii=False, indent=2)}")

    # 测试文档标题提取
    print("\n=== 测试文档标题提取 ===")
    title = collector.get_document_title(mock_all_blocks)
    print(f"文档标题: {title}")

    # 验证结果
    expected_context = {
        "preceding": "本报告详细分析了2023年各季度的销售情况",
        "following": "从图表可以看出，第一季度表现最佳",
        "document_title": "2023年销售业绩报告",
        "image_position": "第3个内容块",
    }

    print("\n=== 验证结果 ===")
    for key in expected_context:
        if context.get(key) == expected_context[key]:
            print(f"✓ {key}: 匹配")
        else:
            print(f"✗ {key}: 不匹配")
            print(f"  期望: {expected_context[key]}")
            print(f"  实际: {context.get(key)}")

    # 测试边界情况
    print("\n=== 测试边界情况 ===")

    # 测试图片在开头的场景
    blocks_start = [
        {
            "type": "image",
            "content": "storage/images/doc1/chart1.png",
            "metadata": {"image_index": 0},
        },
        {
            "type": "text",
            "content": "从图表可以看出，第一季度表现最佳",
            "metadata": {"paragraph_index": 1},
        },
        {
            "type": "text",
            "content": "建议加强第三季度的营销力度",
            "metadata": {"paragraph_index": 2},
        },
    ]
    context_start = collector.collect_context_for_image(blocks_start[0], blocks_start)
    print(
        f"图片在开头时的上下文: {context_start['preceding']} | {context_start['following']}"
    )

    # 测试图片在结尾的场景
    blocks_end = [
        {
            "type": "text",
            "content": "本报告详细分析了2023年各季度的销售情况",
            "metadata": {"paragraph_index": 1},
        },
        {
            "type": "text",
            "content": "从图表可以看出，第一季度表现最佳",
            "metadata": {"paragraph_index": 2},
        },
        {
            "type": "image",
            "content": "storage/images/doc1/chart1.png",
            "metadata": {"image_index": 0},
        },
    ]
    context_end = collector.collect_context_for_image(blocks_end[2], blocks_end)
    print(
        f"图片在结尾时的上下文: {context_end['preceding']} | {context_end['following']}"
    )

    # 测试只有图片的场景
    blocks_only_image = [
        {
            "type": "image",
            "content": "storage/images/doc1/chart1.png",
            "metadata": {"image_index": 0},
        }
    ]
    context_only = collector.collect_context_for_image(
        blocks_only_image[0], blocks_only_image
    )
    print(
        f"只有图片时的上下文: {context_only['preceding']} | {context_only['following']}"
    )

    # 测试文档标题提取
    print("\n=== 测试文档标题提取边界情况 ===")

    # 测试没有合适标题的情况
    blocks_no_title = [
        {
            "type": "text",
            "content": "这是一个很长的段落，包含了很多内容，不适合作为标题使用。",
            "metadata": {"paragraph_index": 1},
        },
        {
            "type": "image",
            "content": "storage/images/doc1/chart1.png",
            "metadata": {"image_index": 0},
        },
    ]
    title_no_title = collector.get_document_title(blocks_no_title)
    print(f"没有合适标题时的结果: {title_no_title}")

    # 测试标题以句号结尾的情况
    blocks_title_with_period = [
        {
            "type": "text",
            "content": "2023年销售业绩报告。",
            "metadata": {"paragraph_index": 1},
        },
        {
            "type": "image",
            "content": "storage/images/doc1/chart1.png",
            "metadata": {"image_index": 0},
        },
    ]
    title_with_period = collector.get_document_title(blocks_title_with_period)
    print(f"标题以句号结尾时的结果: {title_with_period}")

    print("\n测试完成！")
