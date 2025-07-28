#!/usr/bin/env python3
"""
模型回答能力测试脚本
用于测试自定义内容和问题的模型回答能力
"""

import asyncio
from utils.zhipu_client import zhipu_complete_async
from utils.logger import logger


async def test_model_answer(question: str, context: str) -> str:
    """
    测试模型回答能力

    Args:
        question: 用户问题
        context: 上下文内容

    Returns:
        str: 模型生成的答案
    """
    try:
        system_prompt = (
            "你是一个专业的文档问答助手，能够基于提供的文档内容准确回答用户问题。"
            "请遵循以下原则：\n"
            "1. 只基于提供的文档内容回答问题\n"
            "2. 如果文档中没有相关信息，请明确说明\n"
            "3. 保持答案的准确性和完整性\n"
            "4. 使用清晰、易懂的语言"
        )

        user_prompt = (
            f"用户问题：{question}\n\n"
            f"相关文档内容：\n{context}\n\n"
            "请基于上述文档内容回答用户问题。如果文档中没有相关信息，请说明无法找到相关信息。"
        )

        answer = await zhipu_complete_async(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.3,
            max_tokens=8192,
        )

        return answer.strip() if answer else "模型回答失败"

    except Exception as e:
        logger.error(f"模型回答测试失败: {str(e)}")
        return f"测试失败: {str(e)}"


async def interactive_test():
    """交互式测试模式"""
    print("=" * 60)
    print("模型回答能力测试工具")
    print("=" * 60)
    print("输入 'quit' 或 'exit' 退出")
    print("=" * 60)

    while True:
        try:
            # 获取用户输入
            print("\n请输入您的问题:")
            question = input("问题: ").strip()
            
            if question.lower() in ['quit', 'exit', '退出', 'q']:
                print("感谢使用，再见！")
                break
            
            if not question:
                print("请输入有效的问题。")
                continue

            print("\n请输入上下文内容:")
            context = input("上下文: ").strip()
            
            if not context:
                print("请输入有效的上下文内容。")
                continue

            print(f"\n正在生成答案...")
            
            # 调用模型生成答案
            answer = await test_model_answer(question, context)
            
            # 显示结果
            print("\n" + "=" * 60)
            print("模型回答:")
            print("-" * 60)
            print(answer)
            print("=" * 60)

        except KeyboardInterrupt:
            print("\n\n程序被用户中断，正在退出...")
            break
        except Exception as e:
            logger.error(f"测试过程中发生错误: {str(e)}")
            print(f"抱歉，处理时出现了错误: {str(e)}")


async def batch_test():
    """批量测试模式"""
    print("=" * 60)
    print("批量测试模式")
    print("=" * 60)

    # 预定义的测试用例
    test_cases = [
        {
            "question": "Cedar 大学在2005年招收了多少名本科新生？",
            "context": """[来源: testData.xlsx, 表格: 招生数据统计表]
描述: 2005年各大学本科新生招生数据统计表
关键词: 招生数据, 本科新生, 2005年, 大学统计
大学名称    本科新生数量    年份
Cedar大学    1250    2005
Maple大学    980    2005
Oak大学    1100    2005"""
        },
        {
            "question": "为什么选择Cedar大学？",
            "context": """[来源: testData.docx, 段落: 1]
描述: 关于选择Cedar大学的原因和优势介绍
关键词: Cedar大学, 选择原因, 优势, 教育质量
Cedar大学是一所历史悠久的高等学府，以其优秀的师资力量、完善的教学设施和丰富的校园文化而闻名。学校注重培养学生的实践能力和创新精神，为学生提供了良好的学习环境和发展平台。"""
        },
        {
            "question": "表格中显示了哪些信息？",
            "context": """[来源: testData.xlsx, 表格: 招生数据统计表]
描述: 2005年各大学本科新生招生数据统计表
关键词: 招生数据, 本科新生, 2005年, 大学统计
大学名称    本科新生数量    年份
Cedar大学    1250    2005
Maple大学    980    2005
Oak大学    1100    2005"""
        }
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}:")
        print(f"问题: {test_case['question']}")
        print(f"上下文: {test_case['context'][:100]}...")
        print("-" * 40)
        
        answer = await test_model_answer(test_case['question'], test_case['context'])
        print(f"答案: {answer}")
        
        # 添加延迟，避免API调用过于频繁
        await asyncio.sleep(1)

    print("\n批量测试完成！")


async def custom_test():
    """自定义测试模式"""
    print("=" * 60)
    print("自定义测试模式")
    print("=" * 60)
    
    # 您可以在这里自定义测试内容
    custom_question = "浙江华铁建筑支护技术有限公司是否曾有两笔分别为 2 亿和 5 亿的担保记录？是否都是在 2017 年？"
    custom_context = """<table border='1'>\n<tr><th>序号</th><th>交易方</th><th>关联关系</th><th>是否存在控制关系</th><th>交易金额(元)</th><th>币种</th><th>交易简介</th><th>交易方式</th><th>支付方式</th><th>该年度最新财报的营业收入(元)</th><th>该年度最新财报的净利润(元)</th><th>公告日期</th></tr>\n<tr><th></th><th></th><th></th><th></th><th></th><th></th><th></th><th></th><th></th><th></th><th></th><th></th></tr>\n<tr><th></th><th></th><th></th><th></th><th></th><th></th><th></th><th></th><th></th><th></th><th></th><th></th></tr>\n<tr><td>1</td><td>浙江浙银金融租赁股份有限公司</td><td>其它关联关系</td><td>否</td><td>3.50亿</td><td>人民币</td><td>根据业务发展需要,公司或子公...</td><td>其他流入</td><td>-</td><td>51.71亿</td><td>6.05亿</td><td>2024-12-10 00:00:00</td></tr>\n<tr><td>2</td><td>杭州热联华铁建筑服务有限公司</td><td>参股子公司</td><td>否</td><td>7722.68万</td><td>人民币</td><td>租赁服务设备买卖</td><td>租赁</td><td>-</td><td>44.44亿</td><td>8.01亿</td><td>2023-03-30 00:00:00</td></tr>\n<tr><td>3</td><td>浙江浙银金融租赁股份有限公司</td><td>其它关联关系</td><td>否</td><td>1.00亿</td><td>人民币</td><td>售后回租</td><td>租赁</td><td>-</td><td>44.44亿</td><td>8.01亿</td><td>2023-03-30 00:00:00</td></tr>\n<tr><td>4</td><td>丽水哈勃企业管理合伙企业</td><td>其它关联关系</td><td>否</td><td>-</td><td>-</td><td>公司与关联人共同出资成立控股...</td><td>建立子公司</td><td>-</td><td>32.78亿</td><td>6.40亿</td><td>2022-07-27 00:00:00</td></tr>\n<tr><td>5</td><td>浙江华铁建筑设备有限公司</td><td>联营公司</td><td>否</td><td>93.30万</td><td>人民币</td><td>租赁服务</td><td>租赁</td><td>-</td><td>32.78亿</td><td>6.40亿</td><td>2022-07-27 00:00:00</td></tr>\n<tr><td>6</td><td>浙江华铁建筑支护技术有限公司</td><td>联营公司</td><td>否</td><td>35.93万</td><td>人民币</td><td>购买设备</td><td>购买商品</td><td>-</td><td>32.78亿</td><td>6.40亿</td><td>2022-07-27 00:00:00</td></tr>\n<tr><td>7</td><td>杭州热联华铁建筑服务有限公司</td><td>参股子公司</td><td>否</td><td>1529.73万</td><td>人民币</td><td>租赁服务</td><td>租赁</td><td>-</td><td>32.78亿</td><td>6.40亿</td><td>2022-07-27 00:00:00</td></tr>\n<tr><td>8</td><td>杭州热联华铁建筑服务有限公司</td><td>参股子公司</td><td>否</td><td>1999.36万</td><td>人民币</td><td>租赁服务</td><td>租赁</td><td>-</td><td>32.78亿</td><td>6.40亿</td><td>2022-03-31 00:00:00</td></tr>\n<tr><td>9</td><td>浙江华铁建筑设备有限公司</td><td>联营公司</td><td>否</td><td>127.92万</td><td>人民币</td><td>租赁服务</td><td>租赁</td><td>-</td><td>32.78亿</td><td>6.40亿</td><td>2022-03-31 00:00:00</td></tr>\n<tr><td>10</td><td>杭州热联华铁建筑服务有限公司</td><td>参股子公司</td><td>否</td><td>6161.43万</td><td>人民币</td><td>租赁服务设备买卖</td><td>租赁</td><td>-</td><td>32.78亿</td><td>6.40亿</td><td>2022-03-31 00:00:00</td></tr>\n<tr><td>11</td><td>杭州热联华铁建筑服务有限公司</td><td>参股子公司</td><td>否</td><td>4162.07万</td><td>人民币</td><td>设备买卖</td><td>租赁</td><td>-</td><td>32.78亿</td><td>6.40亿</td><td>2022-03-31 00:00:00</td></tr>\n<tr><td>12</td><td>浙江屹圣建设工程有限公司</td><td>其它关联关系</td><td>否</td><td>1.26亿</td><td>人民币</td><td>2021年5月18日,浙江华铁应急设...</td><td>资产出售</td><td>现金</td><td>32.78亿</td><td>6.40亿</td><td>2022-02-15 00:00:00</td></tr>\n<tr><td>13</td><td>湖州昇程企业管理合伙企业</td><td>其它关联关系</td><td>否</td><td>3.43亿</td><td>人民币</td><td>浙江华铁应急设备科技股份有限...</td><td>资产收购</td><td>-</td><td>26.07亿</td><td>4.98亿</td><td>2021-12-07 00:00:00</td></tr>\n<tr><td>14</td><td>胡丹锋</td><td>实际控制人</td><td>是</td><td>-</td><td>-</td><td>浙江华铁应急设备科技股份有限...</td><td>资产出售</td><td>-</td><td>26.07亿</td><td>4.98亿</td><td>2021-04-07 00:00:00</td></tr>\n<tr><td>15</td><td>天津华铁融资租赁有限公司</td><td>参股子公司</td><td>否</td><td>1.00亿</td><td>人民币</td><td>资金拆借</td><td>借款</td><td>-</td><td>26.07亿</td><td>4.98亿</td><td>2021-03-26 00:00:00</td></tr>\n<tr><td>16</td><td>浙江华铁建筑设备有限公司</td><td>联营公司</td><td>否</td><td>2000.00万</td><td>人民币</td><td>租赁服务</td><td>租赁</td><td>-</td><td>26.07亿</td><td>4.98亿</td><td>2021-03-26 00:00:00</td></tr>\n<tr><td>17</td><td>杭州热联华铁建筑服务有限公司</td><td>参股子公司</td><td>否</td><td>8000.00万</td><td>人民币</td><td>租赁服务、设备买卖</td><td>租赁</td><td>-</td><td>26.07亿</td><td>4.98亿</td><td>2021-03-26 00:00:00</td></tr>\n<tr><td>18</td><td>天津华铁融资租赁有限公司</td><td>参股子公司</td><td>否</td><td>10.00亿</td><td>人民币</td><td>关联担保</td><td>担保</td><td>-</td><td>26.07亿</td><td>4.98亿</td><td>2021-03-26 00:00:00</td></tr>\n<tr><td>19</td><td>天津华铁融资租赁有限公司</td><td>参股子公司</td><td>否</td><td>9.00亿</td><td>人民币</td><td>关联担保</td><td>担保</td><td>-</td><td>26.07亿</td><td>4.98亿</td><td>2021-03-26 00:00:00</td></tr>\n<tr><td>20</td><td>拉萨经济技术开发区聚盛设备租...</td><td>其它关联关系</td><td>否</td><td>1.09亿</td><td>人民币</td><td>浙江华铁应急设备科技股份有限...</td><td>资产收购</td><td>-</td><td>26.07亿</td><td>4.98亿</td><td>2021-01-26 00:00:00</td></tr>\n<tr><td>21</td><td>韦向群</td><td>其它关联关系</td><td>否</td><td>1.52亿</td><td>人民币</td><td>浙江华铁应急设备科技股份有限...</td><td>资产收购</td><td>-</td><td>26.07亿</td><td>4.98亿</td><td>2021-01-26 00:00:00</td></tr>\n<tr><td>22</td><td>贾海彬</td><td>其它关联关系</td><td>否</td><td>1306.56万</td><td>人民币</td><td>浙江华铁应急设备科技股份有限...</td><td>资产收购</td><td>-</td><td>26.07亿</td><td>4.98亿</td><td>2021-01-26 00:00:00</td></tr>\n<tr><td>23</td><td>浙江恒铝科技发展有限公司</td><td>控股子公司</td><td>是</td><td>2.74亿</td><td>人民币</td><td>浙江华铁应急设备科技股份有限...</td><td>资产收购</td><td>-</td><td>26.07亿</td><td>4.98亿</td><td>2021-01-26 00:00:00</td></tr>\n<tr><td>24</td><td>天津华铁融资租赁有限公司</td><td>参股子公司</td><td>否</td><td>-</td><td>-</td><td>关联担保</td><td>担保</td><td>-</td><td>15.24亿</td><td>3.23亿</td><td>2020-08-28 00:00:00</td></tr>\n<tr><td>25</td><td>浙江华铁融资租赁有限公司</td><td>参股子公司</td><td>否</td><td>-</td><td>-</td><td>关联担保</td><td>担保</td><td>-</td><td>15.24亿</td><td>3.23亿</td><td>2020-08-28 00:00:00</td></tr>\n<tr><td>26</td><td>浙江华铁宇硕建筑支护设备有限...</td><td>全资子公司</td><td>是</td><td>4.00亿</td><td>人民币</td><td>公司为全资子公司浙江华铁宇硕...</td><td>担保</td><td>-</td><td>15.24亿</td><td>3.23亿</td><td>2020-04-15 00:00:00</td></tr>\n<tr><td>27</td><td>浙江大黄蜂建筑机械设备有限公...</td><td>全资子公司</td><td>是</td><td>1800.00万</td><td>人民币</td><td>浙江大黄蜂建筑机械设备有限公...</td><td>担保</td><td>-</td><td>15.24亿</td><td>3.23亿</td><td>2020-04-15 00:00:00</td></tr>\n<tr><td>28</td><td>浙江吉通地空建筑科技有限公司</td><td>控股子公司</td><td>是</td><td>1.00亿</td><td>人民币</td><td>公司为控股子公司浙江吉通地空...</td><td>担保</td><td>-</td><td>15.24亿</td><td>3.23亿</td><td>2020-04-15 00:00:00</td></tr>\n<tr><td>29</td><td>浙江华铁建筑支护技术有限公司</td><td>全资子公司</td><td>是</td><td>5.00亿</td><td>人民币</td><td>浙江华铁建筑支护技术有限公司...</td><td>担保</td><td>-</td><td>15.24亿</td><td>3.23亿</td><td>2020-04-15 00:00:00</td></tr>\n<tr><td>30</td><td>浙江华铁宇硕建筑支护设备有限公司</td><td>全资子公司</td><td>是</td><td>7.00亿</td><td>人民币</td><td>浙江华铁宇硕建筑支护设备有限...</td><td>担保</td><td>-</td><td>15.24亿</td><td>3.23亿</td><td>2020-04-15 00:00:00</td></tr>\n<tr><td>31</td><td>天津华铁融资租赁有限公司</td><td>参股子公司</td><td>否</td><td>1.00亿</td><td>人民币</td><td>因正常生产经营需要,公司参股...</td><td>借款</td><td>-</td><td>11.54亿</td><td>2.76亿</td><td>2019-12-05 00:00:00</td></tr>\n<tr><td>32</td><td>天津华铁融资租赁有限公司</td><td>控股子公司</td><td>是</td><td>2950.00万</td><td>人民币</td><td>天津华铁融资租赁有限公司向本...</td><td>借款</td><td>-</td><td>11.54亿</td><td>2.76亿</td><td>2019-11-09 00:00:00</td></tr>\n<tr><td>33</td><td>天津华铁融资租赁有限公司</td><td>控股子公司</td><td>是</td><td>-</td><td>-</td><td>2016年1月,华铁租赁与海安县洪...</td><td>担保</td><td>-</td><td>11.54亿</td><td>2.76亿</td><td>2019-09-28 00:00:00</td></tr>\n<tr><td>34</td><td>浙江维安建筑支护科技有限公司</td><td>参股子公司</td><td>否</td><td>2000.00万</td><td>人民币</td><td>向关联方提供房屋租赁、租赁服...</td><td>租赁</td><td>-</td><td>8.88亿</td><td>2878.82万</td><td>2018-06-16 00:00:00</td></tr>\n<tr><td>35</td><td>天津华铁融资租赁有限公司</td><td>控股子公司</td><td>是</td><td>5.00亿</td><td>人民币</td><td>天津华铁融资租赁有限公司为公...</td><td>担保</td><td>-</td><td>6.94亿</td><td>3217.65万</td><td>2017-04-26 00:00:00</td></tr>\n<tr><td>36</td><td>天津华铁商业保理有限公司</td><td>全资子公司</td><td>是</td><td>3.00亿</td><td>人民币</td><td>公司为全资子公司天津华铁商业...</td><td>担保</td><td>-</td><td>6.94亿</td><td>3217.65万</td><td>2017-04-26 00:00:00</td></tr>\n<tr><td>37</td><td>胡丹锋及其近亲属</td><td>实际控制人</td><td>是</td><td>10.00亿</td><td>人民币</td><td>胡丹锋及其近亲属为公司提供不...</td><td>担保</td><td>-</td><td>6.94亿</td><td>3217.65万</td><td>2017-04-26 00:00:00</td></tr>\n<tr><td>38</td><td>浙江华铁融资租赁有限公司</td><td>参股子公司</td><td>否</td><td>5.00亿</td><td>人民币</td><td>浙江华铁融资租赁有限公司为公...</td><td>担保</td><td>-</td><td>6.94亿</td><td>3217.65万</td><td>2017-04-26 00:00:00</td></tr>\n<tr><td>39</td><td>浙江华铁建筑设备有限公司</td><td>全资子公司</td><td>是</td><td>5.00亿</td><td>人民币</td><td>浙江华铁建筑设备有限公司为公...</td><td>担保</td><td>-</td><td>6.94亿</td><td>3217.65万</td><td>2017-04-26 00:00:00</td></tr>\n<tr><td>40</td><td>浙江华铁建筑支护技术有限公司</td><td>全资子公司</td><td>是</td><td>2.00亿</td><td>人民币</td><td>浙江华铁建筑支护技术有限公司...</td><td>担保</td><td>-</td><td>6.94亿</td><td>3217.65万</td><td>2017-04-26 00:00:00</td></tr>\n<tr><td>41</td><td>浙江华铁宇硕建筑支护设备有限公司</td><td>全资子公司</td><td>是</td><td>2.00亿</td><td>人民币</td><td>公司为全资子公司浙江华铁宇硕...</td><td>担保</td><td>-</td><td>6.94亿</td><td>3217.65万</td><td>2017-04-26 00:00:00</td></tr>\n<tr><td>42</td><td>浙江华铁宇硕建筑支护设备有限公司</td><td>全资子公司</td><td>是</td><td>3.00亿</td><td>人民币</td><td>浙江华铁宇硕建筑支护设备有限...</td><td>担保</td><td>-</td><td>6.94亿</td><td>3217.65万</td><td>2017-04-26 00:00:00</td></tr>\n<tr><td>43</td><td>天津华铁融资租赁有限公司</td><td>控股子公司</td><td>是</td><td>10.00亿</td><td>人民币</td><td>公司为控股子公司天津华铁融资...</td><td>担保</td><td>-</td><td>6.94亿</td><td>3217.65万</td><td>2017-04-26 00:00:00</td></tr>\n<tr><td>44</td><td>杭州德洋建筑设备租赁有限公司</td><td>其它关联关系</td><td>否</td><td>100.35万</td><td>人民币</td><td>建筑设备租赁服务</td><td>提供劳务</td><td>转账</td><td>4.79亿</td><td>5426.13万</td><td>2016-04-29 00:00:00</td></tr>\n<tr><td>45</td><td>杭州德洋建筑设备租赁有限公司</td><td>其它关联关系</td><td>否</td><td>3000.00万</td><td>人民币</td><td>短期借款</td><td>借款</td><td>转账</td><td>4.79亿</td><td>5426.13万</td><td>2016-04-29 00:00:00</td></tr>\n<tr><td>46</td><td>杭州德洋建筑设备租赁有限公司</td><td>其它关联关系</td><td>否</td><td>4000.00万</td><td>人民币</td><td>短期借款</td><td>借款</td><td>转账</td><td>4.79亿</td><td>5426.13万</td><td>2016-04-29 00:00:00</td></tr>\n</table>"""

    print(f"自定义问题: {custom_question}")
    print(f"自定义上下文: {custom_context[:100]}...")
    print("-" * 40)
    
    answer = await test_model_answer(custom_question, custom_context)
    print(f"模型回答: {answer}")


async def main():
    """主函数"""
    print("请选择测试模式:")
    print("1. 交互式测试")
    print("2. 批量测试")
    print("3. 自定义测试")
    
    choice = input("请输入选择 (1, 2 或 3): ").strip()
    
    try:
        if choice == "1":
            await interactive_test()
        elif choice == "2":
            await batch_test()
        elif choice == "3":
            await custom_test()
        else:
            print("无效选择，默认运行交互式测试")
            await interactive_test()
            
    except Exception as e:
        logger.error(f"测试程序错误: {str(e)}")
        print(f"程序错误: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main()) 