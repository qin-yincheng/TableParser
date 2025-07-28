import os
import json
import asyncio
from parsers.doc_parser import DocFileParser, enhance_all_chunks, build_prompt_for_chunk

TEST_FILE = os.path.join(os.path.dirname(__file__), "../test_data/testData.docx")
OUTPUT_FILE = os.path.join(
    os.path.dirname(__file__), "../test_data/test_docx_llm_result.json"
)


def parse_and_enhance_docx(file_path: str, output_file: str):
    parser = DocFileParser()
    chunks = parser.process(file_path)
    print(f"解析完成，分块数量: {len(chunks)}，开始LLM语义增强...")
    # 使用有上下文的prompt增强
    # 由于enhance_all_chunks内部默认调用build_prompt_for_chunk(with_context=True)，无需额外修改
    enhanced_chunks = asyncio.run(enhance_all_chunks(chunks))
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(enhanced_chunks, f, ensure_ascii=False, indent=2)
    print(f"增强后分块已保存到: {output_file}")


if __name__ == "__main__":
    parse_and_enhance_docx(TEST_FILE, OUTPUT_FILE)
