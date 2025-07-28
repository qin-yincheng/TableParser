import os
from parsers.doc_parser import DocFileParser


def test_docx():
    parser = DocFileParser()
    # 假设有一个测试docx文件 test_data/test.docx
    input_path = os.path.join(os.path.dirname(__file__), "../test_data/testData.docx")
    result = parser.process(input_path)
    output_path = os.path.join(
        os.path.dirname(__file__), "../test_data/test_docx_result.json"
    )
    import json

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"docx解析结果已保存到: {output_path}")


def test_doc():
    parser = DocFileParser()
    # 假设有一个测试doc文件 test_data/test.doc
    input_path = os.path.join(os.path.dirname(__file__), "../test_data/testData.doc")
    result = parser.process(input_path)
    output_path = os.path.join(
        os.path.dirname(__file__), "../test_data/test_doc_result.json"
    )
    import json

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"doc解析结果已保存到: {output_path}")


if __name__ == "__main__":
    # test_docx()
    test_doc()
