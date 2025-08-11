"""
图片分析器 - 结合上下文分析图片内容
"""

import asyncio
from typing import Dict, List, Optional
import sys
import os

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
from utils.logger import logger


class MockVisionModelClient:
    """Mock视觉模型客户端，用于测试"""

    async def analyze_image(self, image_path: str, prompt: str) -> Dict:
        """模拟图片分析"""
        # 返回项目管理员提供的Mock数据
        return {
            "description": "这是一张销售数据图表，显示了2023年各季度销售额变化趋势",
            "keywords": ["销售数据", "季度报表", "趋势图", "2023年"],
            "image_type": "chart",
            "context_relation": "图表展示了文档中提到的销售业绩数据",
            "key_information": ["Q1销售额最高", "Q3出现下滑", "整体呈上升趋势"],
        }


class ImageAnalyzer:
    """图片分析器"""

    def __init__(self, vision_model, context_collector):
        """
        初始化图片分析器

        Args:
            vision_model: 视觉模型客户端（VisionModelClient或MockVisionModelClient）
            context_collector: 上下文收集器
        """
        self.vision_model = vision_model
        self.context_collector = context_collector
        logger.debug("初始化ImageAnalyzer")

    async def analyze_image_with_context(self, image_path: str, context: Dict) -> Dict:
        """
        结合上下文分析图片

        Args:
            image_path: 图片文件路径
            context: 上下文信息字典，包含preceding, following, document_title, image_position

        Returns:
            分析结果字典
        """
        try:
            # 将image_path添加到context中
            context_with_path = context.copy()
            context_with_path["image_path"] = image_path

            # 构建上下文感知的提示词
            prompt = self.build_image_analysis_prompt(context_with_path)

            # 调用视觉模型
            analysis_result = await self.vision_model.analyze_image(image_path, prompt)

            # 验证和清理结果
            validated_result = self.validate_analysis_result(analysis_result)

            logger.debug(f"图片分析完成: {image_path}")
            return validated_result

        except Exception as e:
            logger.error(f"图片分析失败: {image_path}, 错误: {str(e)}")
            return self.get_fallback_result()

    def build_image_analysis_prompt(self, context: Dict) -> str:
        """
        构建上下文感知的图片分析提示词

        Args:
            context: 上下文信息字典，包含preceding, following, document_title, image_position

        Returns:
            构建的提示词字符串
        """
        from utils.chunk_prompts import STRUCTURED_PROMPTS_WITH_CONTEXT

        # 获取标准化的提示词模板
        prompt_template = STRUCTURED_PROMPTS_WITH_CONTEXT["image"]

        # 准备格式化数据
        format_data = {
            "image_path": context.get("image_path", ""),
            "context": self._format_context(context),
        }

        # 格式化提示词
        formatted_prompt = prompt_template.format(**format_data)

        logger.debug(f"构建分析提示词: {formatted_prompt[:200]}...")
        return formatted_prompt

    def _format_context(self, context: Dict) -> str:
        """格式化上下文信息"""
        parts = []
        if context.get("document_title"):
            parts.append(f"文档标题：{context['document_title']}")
        if context.get("preceding"):
            parts.append(f"前文：{context['preceding']}")
        if context.get("following"):
            parts.append(f"后文：{context['following']}")
        if context.get("image_position"):
            parts.append(f"图片位置：{context['image_position']}")

        return "，".join(parts) if parts else "无上下文信息"

    def validate_analysis_result(self, result: Dict) -> Dict:
        """
        验证分析结果

        Args:
            result: 原始分析结果

        Returns:
            验证后的结果字典
        """
        required_fields = [
            "description",
            "keywords",
            "image_type",
            "context_relation",
            "key_information",
        ]

        for field in required_fields:
            if field not in result:
                if field == "keywords":
                    result[field] = []
                elif field == "key_information":
                    result[field] = []
                else:
                    result[field] = ""

        # 确保keywords和key_information是列表类型
        if not isinstance(result.get("keywords"), list):
            result["keywords"] = []
        if not isinstance(result.get("key_information"), list):
            result["key_information"] = []

        # 确保其他字段是字符串类型
        for field in ["description", "image_type", "context_relation"]:
            if not isinstance(result.get(field), str):
                result[field] = str(result.get(field, ""))

        logger.debug(f"验证分析结果: {result}")
        return result

    def get_fallback_result(self) -> Dict:
        """
        获取回退结果

        Returns:
            默认的分析结果字典
        """
        return {
            "description": "图片分析失败，无法获取详细信息",
            "keywords": ["图片", "分析失败"],
            "image_type": "unknown",
            "context_relation": "无法确定与文档的关系",
            "key_information": [],
        }


if __name__ == "__main__":
    """测试ImageAnalyzer功能"""
    import json

    # 创建Mock组件
    mock_vision_client = MockVisionModelClient()

    # 创建Mock ContextCollector
    class MockContextCollector:
        def collect_context_for_image(self, image_block, all_blocks):
            return {
                "preceding": "本报告详细分析了2023年各季度的销售情况",
                "following": "从图表可以看出，第一季度表现最佳",
                "document_title": "2023年销售业绩报告",
                "image_position": "第3个内容块",
            }

    mock_context_collector = MockContextCollector()

    # 创建ImageAnalyzer实例
    analyzer = ImageAnalyzer(mock_vision_client, mock_context_collector)

    # 测试提示词构建
    print("=== 测试提示词构建 ===")
    test_context = {
        "preceding": "本报告详细分析了2023年各季度的销售情况",
        "following": "从图表可以看出，第一季度表现最佳",
        "document_title": "2023年销售业绩报告",
        "image_position": "第3个内容块",
    }

    prompt = analyzer.build_image_analysis_prompt(test_context)
    print("构建的提示词:")
    print(prompt)

    # 测试结果验证
    print("\n=== 测试结果验证 ===")

    # 测试完整结果
    complete_result = {
        "description": "这是一张销售数据图表，显示了2023年各季度销售额变化趋势",
        "keywords": ["销售数据", "季度报表", "趋势图", "2023年"],
        "image_type": "chart",
        "context_relation": "图表展示了文档中提到的销售业绩数据",
        "key_information": ["Q1销售额最高", "Q3出现下滑", "整体呈上升趋势"],
    }

    validated_complete = analyzer.validate_analysis_result(complete_result)
    print("完整结果验证:")
    print(json.dumps(validated_complete, ensure_ascii=False, indent=2))

    # 测试缺失字段的结果
    incomplete_result = {"description": "这是一张图表"}

    validated_incomplete = analyzer.validate_analysis_result(incomplete_result)
    print("\n缺失字段结果验证:")
    print(json.dumps(validated_incomplete, ensure_ascii=False, indent=2))

    # 测试错误类型的结果
    wrong_type_result = {
        "description": "这是一张图表",
        "keywords": "错误的关键词类型",
        "image_type": 123,
        "context_relation": None,
        "key_information": "错误的信息类型",
    }

    validated_wrong_type = analyzer.validate_analysis_result(wrong_type_result)
    print("\n错误类型结果验证:")
    print(json.dumps(validated_wrong_type, ensure_ascii=False, indent=2))

    # 测试回退结果
    print("\n=== 测试回退结果 ===")
    fallback_result = analyzer.get_fallback_result()
    print("回退结果:")
    print(json.dumps(fallback_result, ensure_ascii=False, indent=2))

    # 测试完整的异步分析流程
    print("\n=== 测试完整分析流程 ===")

    async def test_analysis():
        image_path = "tests/mock_data/images/chart1.png"
        context = {
            "preceding": "本报告详细分析了2023年各季度的销售情况",
            "following": "从图表可以看出，第一季度表现最佳",
            "document_title": "2023年销售业绩报告",
            "image_position": "第3个内容块",
        }

        result = await analyzer.analyze_image_with_context(image_path, context)
        print("完整分析结果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))

        # 验证结果格式
        required_fields = [
            "description",
            "keywords",
            "image_type",
            "context_relation",
            "key_information",
        ]
        all_fields_present = all(field in result for field in required_fields)
        print(f"\n所有必需字段都存在: {all_fields_present}")

        # 验证字段类型
        keywords_is_list = isinstance(result["keywords"], list)
        key_info_is_list = isinstance(result["key_information"], list)
        other_fields_are_str = all(
            isinstance(result[field], str)
            for field in ["description", "image_type", "context_relation"]
        )

        print(f"关键词是列表类型: {keywords_is_list}")
        print(f"关键信息是列表类型: {key_info_is_list}")
        print(f"其他字段是字符串类型: {other_fields_are_str}")

    # 运行异步测试
    asyncio.run(test_analysis())

    print("\n测试完成！")
