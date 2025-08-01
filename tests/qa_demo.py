#!/usr/bin/env python3
"""
问答演示脚本 - 交互式问答功能
"""

import asyncio
import json
from qa_service import QAService
from utils.logger import logger


class QADemo:
    """问答演示类"""

    def __init__(self):
        """初始化演示"""
        self.qa_service = QAService()
        self.kb_id = 4  # 默认知识库ID

    async def interactive_qa(self):
        """交互式问答"""
        print("=" * 60)
        print("欢迎使用智能文档问答系统！")
        print("=" * 60)
        print("系统功能：")
        print("1. 基于文档内容的智能问答")
        print("2. 支持文本和表格数据查询")
        print("3. 提供答案来源和相似度分数")
        print("4. 输入 'quit' 或 'exit' 退出")
        print("=" * 60)

        while True:
            try:
                # 获取用户输入
                question = input("\n请输入您的问题: ").strip()

                # 检查退出命令
                if question.lower() in ["quit", "exit", "退出", "q"]:
                    print("感谢使用，再见！")
                    break

                # 检查空输入
                if not question:
                    print("请输入有效的问题。")
                    continue

                print(f"\n正在为您查找答案...")

                # 调用问答服务
                result = await self.qa_service.answer_question(
                    question=question, kb_id=self.kb_id
                )

                # 显示结果
                self._display_result(result)

            except KeyboardInterrupt:
                print("\n\n程序被用户中断，正在退出...")
                break
            except Exception as e:
                logger.error(f"问答过程中发生错误: {str(e)}")
                print(f"抱歉，处理您的问题时出现了错误: {str(e)}")

    def _display_result(self, result: dict):
        """显示问答结果"""
        print("\n" + "=" * 60)

        if result.get("success"):
            print("✅ 答案生成成功！")
            print("-" * 60)
            print(f"问题: {result.get('question', '')}")
            print("-" * 60)
            print(f"答案: {result.get('answer', '')}")
            print("-" * 60)

            # 显示来源信息
            sources = result.get("sources", [])
            if sources:
                print("📚 答案来源:")
                for i, source in enumerate(sources[:3], 1):  # 只显示前3个来源
                    print(f"  {i}. {source.get('content', '')[:100]}...")
                    print(f"     类型: {source.get('chunk_type', '')}")
                    print(f"     相似度分数: {source.get('similarity_score', 0):.3f}")

            # 显示元数据
            metadata = result.get("metadata", {})
            if metadata:
                print("-" * 60)
                print(f"总来源数: {metadata.get('total_sources', 0)}")
        else:
            print("❌ 答案生成失败")
            print("-" * 60)
            print(f"错误信息: {result.get('error', '未知错误')}")

        print("=" * 60)

    async def batch_qa_demo(self):
        """批量问答演示"""
        print("=" * 60)
        print("批量问答演示")
        print("=" * 60)

        demo_questions = [
            "2025年5月8日的融券余额和融券余量分别是多少？",
            "找出融资余额占流通市值比最高的那一天，并提供其交易日期和对应的融资余额占流通市值比。",
            "在2025年3月10日和2025年3月11日之间，融资净买入是增加了还是减少了？具体变化了多少？",
            "请列出2025年7月所有融资净买入为负值的日期及其对应的融资净买入金额。",
        ]

        for i, question in enumerate(demo_questions, 1):
            print(f"\n问题 {i}: {question}")
            print("-" * 40)

            result = await self.qa_service.answer_question(
                question=question, kb_id=self.kb_id
            )

            if result.get("success"):
                print(f"答案: {result.get('answer', '')[:500]}...")
                print(f"来源数: {result.get('metadata', {}).get('total_sources', 0)}")
            else:
                print(f"失败: {result.get('error', '')}")

            # 添加延迟，避免API调用过于频繁
            await asyncio.sleep(1)

        print("\n批量演示完成！")

    def close(self):
        """关闭服务"""
        self.qa_service.close()


async def main():
    """主函数"""
    demo = QADemo()

    try:
        print("请选择演示模式:")
        print("1. 交互式问答")
        print("2. 批量演示")

        choice = input("请输入选择 (1 或 2): ").strip()

        if choice == "2":
            await demo.batch_qa_demo()
        else:
            await demo.interactive_qa()

    except Exception as e:
        logger.error(f"演示程序错误: {str(e)}")
        print(f"程序错误: {str(e)}")
    finally:
        demo.close()


if __name__ == "__main__":
    asyncio.run(main())
