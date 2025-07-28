#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
向量化测试配置文件
用于管理向量化测试的各种参数和设置
"""

import os
from typing import Dict, Any

# 测试配置
TEST_CONFIG = {
    # 测试知识库ID
    "test_kb_id": 999,
    "quick_test_kb_id": 888,
    # 测试结果目录
    "test_results_dir": "test_results/vector_integration_test",
    # 测试数据文件路径
    "test_data_files": {
        "doc": "test_results/doc_parser_test_20250727_151620.json",
        "xlsx": "test_results/xlsx_parser_test_20250727_152437.json",
    },
    # 向量化测试参数
    "vectorization": {
        "max_test_chunks": 10,  # 最大测试分块数量
        "batch_size": 5,  # 批量处理大小
        "timeout": 30,  # 超时时间（秒）
    },
    # 向量库测试参数
    "vector_db": {
        "query_limit": 5,  # 查询结果限制
        "distance_threshold": 0.8,  # 距离阈值
        "test_queries": [
            "地方高校招生情况",
            "研究生教育发展",
            "表格数据统计",
            "Cedar大学数据",
            "关联交易信息",
        ],
    },
    # 性能测试参数
    "performance": {
        "enable_timing": True,  # 是否启用时间统计
        "log_detailed": True,  # 是否记录详细信息
        "save_results": True,  # 是否保存测试结果
    },
    # 测试模式
    "test_modes": {
        "quick": {"max_chunks": 3, "enable_query": True, "enable_performance": False},
        "full": {"max_chunks": 10, "enable_query": True, "enable_performance": True},
        "performance": {
            "max_chunks": 50,
            "enable_query": False,
            "enable_performance": True,
        },
    },
}

# 测试数据样本
TEST_SAMPLES = {
    "text_chunks": [
        {
            "type": "text",
            "content": "地方高校在2005年的招生及毕业情况",
            "metadata": {
                "description": "2005年地方高校招生毕业情况概述",
                "keywords": ["地方高校", "招生", "毕业", "2005年"],
            },
        },
        {
            "type": "text",
            "content": "Cedar大学本科招生人数为110人，毕业人数为103人，净增7人",
            "metadata": {
                "description": "Cedar大学本科招生毕业数据",
                "keywords": ["Cedar大学", "本科", "招生", "毕业"],
            },
        },
        {
            "type": "text",
            "content": "研究生教育发展情况分析",
            "metadata": {
                "description": "研究生教育发展趋势分析",
                "keywords": ["研究生", "教育", "发展", "分析"],
            },
        },
    ],
    "table_chunks": [
        {
            "type": "table_row",
            "content": "序号:1, 交易方:浙江浙银金融租赁股份有限公司, 关联关系:其它关联关系, 交易金额:3.50亿",
            "metadata": {
                "description": "关联交易记录",
                "keywords": ["关联交易", "金融租赁", "交易金额"],
                "table_id": "table_1",
                "row": 1,
                "header": ["序号", "交易方", "关联关系", "交易金额"],
            },
        }
    ],
}

# 测试查询样本
QUERY_SAMPLES = [
    {
        "query": "地方高校招生情况",
        "expected_keywords": ["地方高校", "招生"],
        "description": "查询地方高校招生相关信息",
    },
    {
        "query": "研究生教育发展",
        "expected_keywords": ["研究生", "教育", "发展"],
        "description": "查询研究生教育发展情况",
    },
    {
        "query": "表格数据统计",
        "expected_keywords": ["表格", "数据", "统计"],
        "description": "查询表格数据统计信息",
    },
    {
        "query": "Cedar大学数据",
        "expected_keywords": ["Cedar大学", "数据"],
        "description": "查询Cedar大学相关数据",
    },
    {
        "query": "关联交易信息",
        "expected_keywords": ["关联交易", "信息"],
        "description": "查询关联交易相关信息",
    },
]


def get_test_config(mode: str = "full") -> Dict[str, Any]:
    """
    获取测试配置

    Args:
        mode: 测试模式 ("quick", "full", "performance")

    Returns:
        Dict[str, Any]: 测试配置
    """
    config = TEST_CONFIG.copy()

    if mode in config["test_modes"]:
        mode_config = config["test_modes"][mode]
        config["vectorization"]["max_test_chunks"] = mode_config["max_chunks"]
        config["enable_query"] = mode_config["enable_query"]
        config["enable_performance"] = mode_config["enable_performance"]

    return config


def get_test_samples(sample_type: str = "all") -> Dict[str, Any]:
    """
    获取测试样本

    Args:
        sample_type: 样本类型 ("text", "table", "all")

    Returns:
        Dict[str, Any]: 测试样本
    """
    if sample_type == "text":
        return {"text_chunks": TEST_SAMPLES["text_chunks"]}
    elif sample_type == "table":
        return {"table_chunks": TEST_SAMPLES["table_chunks"]}
    else:
        return TEST_SAMPLES


def get_query_samples() -> list:
    """
    获取查询样本

    Returns:
        list: 查询样本列表
    """
    return QUERY_SAMPLES


def ensure_test_directories():
    """确保测试目录存在"""
    test_results_dir = TEST_CONFIG["test_results_dir"]
    os.makedirs(test_results_dir, exist_ok=True)

    # 创建子目录
    subdirs = [
        "embedding_test_results",
        "vector_test_results",
        "integration_test_results",
    ]
    for subdir in subdirs:
        os.makedirs(os.path.join(test_results_dir, subdir), exist_ok=True)


def get_test_file_path(file_type: str) -> str:
    """
    获取测试文件路径

    Args:
        file_type: 文件类型 ("doc", "xlsx")

    Returns:
        str: 文件路径
    """
    return TEST_CONFIG["test_data_files"].get(file_type, "")


def is_test_file_exists(file_type: str) -> bool:
    """
    检查测试文件是否存在

    Args:
        file_type: 文件类型 ("doc", "xlsx")

    Returns:
        bool: 文件是否存在
    """
    file_path = get_test_file_path(file_type)
    return os.path.exists(file_path) if file_path else False


# 测试结果模板
TEST_RESULT_TEMPLATE = {
    "test_info": {
        "test_name": "",
        "test_time": "",
        "test_mode": "",
        "test_duration": 0.0,
    },
    "vectorization": {
        "total_chunks": 0,
        "successful_embeddings": 0,
        "failed_embeddings": 0,
        "embedding_time": 0.0,
        "average_embedding_time": 0.0,
    },
    "vector_db": {
        "successful_inserts": 0,
        "failed_inserts": 0,
        "insert_time": 0.0,
        "query_results": [],
    },
    "performance": {"total_time": 0.0, "memory_usage": 0.0, "throughput": 0.0},
    "errors": [],
    "warnings": [],
}


def create_test_result(test_name: str, test_mode: str = "full") -> Dict[str, Any]:
    """
    创建测试结果模板

    Args:
        test_name: 测试名称
        test_mode: 测试模式

    Returns:
        Dict[str, Any]: 测试结果模板
    """
    from datetime import datetime

    result = TEST_RESULT_TEMPLATE.copy()
    result["test_info"]["test_name"] = test_name
    result["test_info"]["test_time"] = datetime.now().isoformat()
    result["test_info"]["test_mode"] = test_mode

    return result
