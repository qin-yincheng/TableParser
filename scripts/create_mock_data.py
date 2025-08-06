#!/usr/bin/env python3
"""
Mock数据创建脚本
用于生成测试和开发所需的模拟数据
"""

import os
import json
import yaml
from PIL import Image, ImageDraw, ImageFont
import random


class MockDataCreator:
    def __init__(self, base_path="tests/mock_data"):
        self.base_path = base_path
        self.ensure_directories()

    def ensure_directories(self):
        """确保所有必需的目录存在"""
        directories = ["images", "documents", "responses", "configs"]

        for dir_name in directories:
            dir_path = os.path.join(self.base_path, dir_name)
            os.makedirs(dir_path, exist_ok=True)
            print(f"✓ 创建目录: {dir_path}")

    def create_mock_images(self):
        """创建模拟图片文件"""
        images_config = [
            {
                "name": "chart1.png",
                "type": "chart",
                "description": "销售数据图表",
                "size": (800, 600),
                "color": (70, 130, 180),
            },
            {
                "name": "photo1.jpg",
                "type": "photo",
                "description": "产品照片",
                "size": (640, 480),
                "color": (255, 165, 0),
            },
            {
                "name": "screenshot1.png",
                "type": "screenshot",
                "description": "软件界面截图",
                "size": (1024, 768),
                "color": (128, 128, 128),
            },
            {
                "name": "handwriting1.png",
                "type": "handwriting",
                "description": "手写笔记",
                "size": (600, 800),
                "color": (255, 255, 224),
            },
        ]

        for config in images_config:
            self._create_mock_image(config)

    def _create_mock_image(self, config):
        """创建单个模拟图片"""
        img = Image.new("RGB", config["size"], config["color"])
        draw = ImageDraw.Draw(img)

        # 添加文字说明
        text = f"Mock {config['type']}: {config['description']}"
        draw.text((10, 10), text, fill=(255, 255, 255))

        # 保存图片
        image_path = os.path.join(self.base_path, "images", config["name"])
        img.save(image_path)
        print(f"✓ 创建图片: {image_path}")

    def create_mock_responses(self):
        """创建模拟API响应"""
        responses = {
            "vision_responses.json": {
                "chart1.png": {
                    "description": "这是一张销售数据图表，显示了2023年各季度销售额变化趋势",
                    "keywords": ["销售数据", "季度报表", "趋势图", "2023年"],
                    "image_type": "chart",
                    "context_relation": "图表展示了文档中提到的销售业绩数据",
                    "key_information": ["Q1销售额最高", "Q3出现下滑", "整体呈上升趋势"],
                },
                "photo1.jpg": {
                    "description": "这是一张产品展示照片，清晰展示了产品的外观和细节",
                    "keywords": ["产品展示", "外观", "细节", "高质量"],
                    "image_type": "photo",
                    "context_relation": "照片展示了文档中描述的产品特征",
                    "key_information": ["产品外观", "细节清晰", "展示效果"],
                },
            },
            "context_responses.json": {
                "sample_context": {
                    "preceding": "本报告详细分析了2023年各季度的销售情况",
                    "following": "从图表可以看出，第一季度表现最佳",
                    "document_title": "2023年销售业绩报告",
                    "image_position": "第3个内容块",
                }
            },
            "analysis_responses.json": {
                "sample_analysis": {
                    "description": "销售数据图表，显示2023年各季度销售额",
                    "keywords": ["销售数据", "季度报表", "2023年"],
                    "image_type": "chart",
                    "context_relation": "展示文档中的销售业绩数据",
                    "key_information": ["Q1最高", "Q3下滑", "整体上升"],
                }
            },
        }

        for filename, data in responses.items():
            file_path = os.path.join(self.base_path, "responses", filename)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"✓ 创建响应文件: {file_path}")

    def create_mock_configs(self):
        """创建模拟配置文件"""
        configs = {
            "mock_config.yaml": {
                "image_processing": {
                    "enabled": True,
                    "storage_path": "storage/images",
                    "vision_model": "glm-4v-plus",
                    "api_key": "${ZHIPUAI_API_KEY}",
                    "context_window": 3,
                    "max_concurrent": 5,
                    "timeout": 30,
                    "retry_count": 3,
                    "cache_enabled": True,
                    "cache_ttl": 3600,
                }
            },
            "test_config.yaml": {
                "image_processing": {
                    "enabled": True,
                    "storage_path": "tests/mock_data/images",
                    "vision_model": "mock",
                    "api_key": "test_key",
                    "context_window": 2,
                    "max_concurrent": 2,
                    "timeout": 10,
                    "retry_count": 1,
                    "cache_enabled": False,
                    "cache_ttl": 60,
                }
            },
        }

        for filename, config in configs.items():
            file_path = os.path.join(self.base_path, "configs", filename)
            with open(file_path, "w", encoding="utf-8") as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            print(f"✓ 创建配置文件: {file_path}")


def main():
    """主函数"""
    print("开始创建Mock数据...")

    creator = MockDataCreator()
    creator.create_mock_images()
    creator.create_mock_responses()
    creator.create_mock_configs()

    print("\n✓ Mock数据创建完成！")
    print("\n目录结构:")
    os.system(f"tree {creator.base_path}")


if __name__ == "__main__":
    main()
