class Chunker:
    """文件分片器，负责将文本内容分割成适当大小的片段"""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        初始化分片器

        Args:
            chunk_size: 分片大小（字符数）
            chunk_overlap: 分片重叠部分大小（字符数）
        """
        if chunk_size <= 0:
            raise ValueError("chunk_size 必须大于 0")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap 不能为负数")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap 必须小于 chunk_size")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(self, text: str) -> list[str]:
        """
        将文本分割成片段（优化 overlap 分割避免截断句子）

        Args:
            text: 要分割的文本

        Returns:
            分片后的文本列表
        """
        if not text:
            return []

        chunks = []

        if len(text) <= self.chunk_size:
            chunks.append(text)
            return chunks

        punctuation_priority = {
            "。": 3,
            "！": 3,
            "？": 3,
            ")": 3,
            "）": 3,
            ";": 2,
            "；": 2,
            "…": 2,
            ":": 2,
            "：": 2,
            ",": 1,
            "，": 1,
            "\n": 4,
            "\t": 1,
            " ": 1,
            "!": 3,
            "?": 3,
            ".": 1,
        }

        start = 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            best_end = end

            if end < len(text):
                search_end = min(end + 100, len(text))
                search_start = max(end - 100, start)
                best_score = -1

                for i in range(search_end - 1, search_start - 1, -1):
                    char = text[i]
                    if char in punctuation_priority:
                        score = punctuation_priority[char]
                        if score > best_score:
                            best_score = score
                            best_end = i + 1
                            if score == 4:
                                # 优先级最高，直接使用
                                break
                            elif score == 3:
                                break

                # 若未找到合适标点，仍可尝试向后延伸到空白字符
                if best_end == end:
                    for i in range(end, search_end):
                        if text[i].isspace() or i + 1 >= len(text):
                            best_end = i + 1
                            break

            # 分片
            chunk = text[start:best_end]
            if chunk.strip():
                chunks.append(chunk)

            if best_end >= len(text):
                break

            # 计算下一次 start：
            # 1) 找到 chunk 中距离末尾 <= chunk_overlap 的最佳标点以避免截断句子
            overlap_region_start = max(best_end - self.chunk_overlap, start)
            overlap_best_start = best_end - self.chunk_overlap

            best_overlap_score = -1
            for i in range(best_end - 1, overlap_region_start - 1, -1):
                char = text[i]
                if char in punctuation_priority:
                    score = punctuation_priority[char]
                    if score > best_overlap_score:
                        best_overlap_score = score
                        overlap_best_start = i + 1
                        if score == 3:
                            break

            if overlap_best_start <= start:
                start = best_end  # 避免死循环
            else:
                start = overlap_best_start

        return chunks
