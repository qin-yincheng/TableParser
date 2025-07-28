import os
import json
from parsers.xlsx_parser import XlsxFileParser, enhance_all_chunks
import asyncio

TEST_FILE = os.path.join(os.path.dirname(__file__), "../test_data/testData.xlsx")
OUTPUT_FILE = os.path.join(
    os.path.dirname(__file__), "../test_data/test_xlsx_result.json"
)
LLM_OUTPUT_FILE = os.path.join(
    os.path.dirname(__file__), "../test_data/test_xlsx_llm_result.json"
)


def test_xlsx_parser_basic(file_path, output_file):
    parser = XlsxFileParser()
    chunks = parser.parse(file_path)
    assert isinstance(chunks, list)
    assert len(chunks) > 0, "解析结果应包含至少一个分块"
    for chunk in chunks:
        assert isinstance(chunk, dict)
        assert "type" in chunk
        assert "content" in chunk
        assert "metadata" in chunk
        assert "doc_id" in chunk["metadata"]
        assert "sheet" in chunk["metadata"]
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    print(f"测试通过，分块数量：{len(chunks)}，结果已保存到 {output_file}")


def test_xlsx_parser_llm_enhance(file_path, output_file):
    parser = XlsxFileParser()
    chunks = parser.parse(file_path)
    enhanced_chunks = asyncio.run(enhance_all_chunks(chunks))
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(enhanced_chunks, f, ensure_ascii=False, indent=2)
    print(
        f"LLM增强测试通过，分块数量：{len(enhanced_chunks)}，结果已保存到 {output_file}"
    )


if __name__ == "__main__":
    # test_xlsx_parser_basic(TEST_FILE, OUTPUT_FILE)
    test_xlsx_parser_llm_enhance(TEST_FILE, LLM_OUTPUT_FILE)
