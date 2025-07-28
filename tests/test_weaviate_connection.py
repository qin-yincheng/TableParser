#!/usr/bin/env python3
"""
Weaviate连接测试脚本
用于验证Docker部署的Weaviate配置是否正确
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from connector import WeaviateConnector
from utils.logger import logger


def test_weaviate_connection():
    """测试Weaviate连接"""
    print("开始测试Weaviate连接...")

    try:
        # 创建连接器实例
        connector = WeaviateConnector()

        # 尝试连接
        print("正在连接Weaviate...")
        connector.connect()

        # 检查连接状态
        if connector.is_connected():
            print("✅ Weaviate连接成功！")

            # 获取客户端信息
            client = connector._client
            print(f"✅ 客户端就绪状态: {client.is_ready()}")

            # 测试基本操作
            try:
                collections = client.collections.list_all()
                print(f"✅ 当前集合数量: {len(collections)}")
                if collections:
                    print(f"✅ 集合列表: {list(collections.keys())}")
                else:
                    print("ℹ️  当前没有集合")
            except Exception as e:
                print(f"⚠️  获取集合列表时出错: {e}")

        else:
            print("❌ Weaviate连接失败")
            return False

    except Exception as e:
        print(f"❌ 连接测试失败: {e}")
        logger.error(f"Weaviate连接测试失败: {e}")
        return False

    finally:
        # 关闭连接
        try:
            connector.disconnect()
            print("✅ 连接已关闭")
        except Exception as e:
            print(f"⚠️  关闭连接时出错: {e}")

    return True


def test_with_custom_config():
    """使用自定义配置测试连接"""
    print("\n开始测试自定义配置连接...")

    try:
        connector = WeaviateConnector()

        # 使用自定义参数连接
        connector.connect(
            http_host="localhost",
            http_port=8089,
            grpc_host="localhost",
            grpc_port=50055,
            scheme="http",
        )

        if connector.is_connected():
            print("✅ 自定义配置连接成功！")
            connector.disconnect()
            return True
        else:
            print("❌ 自定义配置连接失败")
            return False

    except Exception as e:
        print(f"❌ 自定义配置连接测试失败: {e}")
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("Weaviate Docker连接测试")
    print("=" * 50)

    # 测试1: 使用配置文件连接
    success1 = test_weaviate_connection()

    # 测试2: 使用自定义配置连接
    success2 = test_with_custom_config()

    print("\n" + "=" * 50)
    print("测试结果总结:")
    print(f"配置文件连接: {'✅ 成功' if success1 else '❌ 失败'}")
    print(f"自定义配置连接: {'✅ 成功' if success2 else '❌ 失败'}")

    if success1 or success2:
        print("\n🎉 至少有一种连接方式成功！")
        print("💡 如果配置文件连接失败，请检查config/config.yaml文件")
        print("💡 如果自定义配置连接失败，请检查Docker容器是否正常运行")
    else:
        print("\n❌ 所有连接方式都失败了")
        print("🔧 请检查以下项目:")
        print("   1. Docker容器是否正在运行")
        print("   2. 端口映射是否正确 (8089:8080, 50055:50051)")
        print("   3. 防火墙设置")
        print("   4. 配置文件格式是否正确")

    print("=" * 50)
