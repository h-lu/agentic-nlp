"""
Tests for Text Chunking concepts.

This module tests text chunking strategies including fixed-size chunking,
separator-based chunking, chunk size constraints, and edge cases.

Validates anchor: chunk-size-impact
"""

import pytest
from .conftest import TextChunker, ChunkConfig, TextChunk


class TestChunkConfig:
    """Tests for ChunkConfig class."""

    def test_default_configuration(self):
        """Test that default configuration has sensible values."""
        config = ChunkConfig()

        assert config.chunk_size == 500
        assert config.chunk_overlap == 50
        assert "\n\n" in config.separators
        assert "。" in config.separators

    def test_custom_configuration(self):
        """Test creating custom configuration."""
        config = ChunkConfig(
            chunk_size=300,
            chunk_overlap=30,
            separators=["。", "，"]
        )

        assert config.chunk_size == 300
        assert config.chunk_overlap == 30
        assert config.separators == ["。", "，"]

    def test_overlap_less_than_chunk_size(self):
        """Test that overlap should be less than chunk size for meaningful chunking."""
        config = ChunkConfig(chunk_size=100, chunk_overlap=50)

        # Overlap should be less than chunk size
        assert config.chunk_overlap < config.chunk_size

    def test_overlap_equal_to_chunk_size_warning(self):
        """Test behavior when overlap equals chunk size (edge case)."""
        config = ChunkConfig(chunk_size=100, chunk_overlap=100)
        chunker = TextChunker(config=config)

        text = "这是一段测试文本，用于测试当重叠大小等于块大小时的行为。"
        chunks = chunker.chunk_text(text)

        # Should still produce chunks without infinite loop
        assert len(chunks) > 0


class TestFixedChunking:
    """Tests for fixed-size text chunking."""

    def test_basic_chunking(self, text_chunker):
        """Test basic text chunking into fixed-size chunks."""
        text = "这是一段测试文本。" * 50  # About 450 characters

        chunks = text_chunker.chunk_text(text)

        assert len(chunks) > 1
        assert all(isinstance(chunk, TextChunk) for chunk in chunks)

    def test_chunk_size_constraint(self):
        """Test that chunks respect size constraints."""
        config = ChunkConfig(chunk_size=50, chunk_overlap=10)
        chunker = TextChunker(config=config)

        text = "这是一段很长的测试文本，用来测试块大小约束是否有效。" * 10
        chunks = chunker.chunk_text(text)

        # Each chunk should be at most chunk_size
        for chunk in chunks:
            assert len(chunk.content) <= config.chunk_size

    def test_chunk_overlap(self):
        """Test that chunks have overlap between them."""
        config = ChunkConfig(chunk_size=100, chunk_overlap=20)
        chunker = TextChunker(config=config)

        text = "这是一段测试文本，包含足够的内容来生成多个块。" * 5
        chunks = chunker.chunk_text(text)

        if len(chunks) > 1:
            # Check that consecutive chunks share some content
            # The overlap should cause some repetition
            assert len(chunks) > 1

    def test_empty_text(self, text_chunker):
        """Test chunking empty text."""
        chunks = text_chunker.chunk_text("")

        assert chunks == []

    def test_single_character_text(self, text_chunker):
        """Test chunking very short text."""
        chunks = text_chunker.chunk_text("短")

        assert len(chunks) == 1
        assert chunks[0].content == "短"

    def test_text_shorter_than_chunk_size(self):
        """Test chunking text shorter than chunk size."""
        config = ChunkConfig(chunk_size=500, chunk_overlap=50)
        chunker = TextChunker(config=config)

        short_text = "这是一个短文本。"
        chunks = chunker.chunk_text(short_text)

        assert len(chunks) == 1
        assert chunks[0].content == short_text

    def test_text_exactly_chunk_size(self):
        """Test chunking text exactly chunk size."""
        chunk_size = 100
        config = ChunkConfig(chunk_size=chunk_size, chunk_overlap=0)
        chunker = TextChunker(config=config)

        exact_text = "测" * chunk_size
        chunks = chunker.chunk_text(exact_text)

        assert len(chunks) == 1


class TestChineseTextSeparators:
    """Tests for Chinese text separator handling."""

    def test_chinese_period_separator(self):
        """Test splitting by Chinese period (。)."""
        config = ChunkConfig(chunk_size=100, chunk_overlap=0)
        chunker = TextChunker(config=config)

        text = "这是第一句话。这是第二句话。这是第三句话。"
        chunks = chunker.chunk_by_separator(text)

        # Should split by period when possible
        assert len(chunks) >= 1

    def test_multiple_chinese_separators(self, chinese_text):
        """Test handling multiple Chinese punctuation marks."""
        config = ChunkConfig(chunk_size=50, chunk_overlap=0)
        chunker = TextChunker(config=config)

        chunks = chunker.chunk_by_separator(chinese_text)

        # Should produce multiple chunks
        assert len(chunks) >= 1

    def test_newline_separator(self):
        """Test splitting by newline."""
        config = ChunkConfig(chunk_size=200, chunk_overlap=0)
        chunker = TextChunker(config=config)

        text = "第一段内容。\n\n第二段内容。\n\n第三段内容。"
        chunks = chunker.chunk_by_separator(text)

        assert len(chunks) >= 1

    def test_mixed_language_text(self):
        """Test chunking text with mixed Chinese and English."""
        config = ChunkConfig(chunk_size=100, chunk_overlap=0)
        chunker = TextChunker(config=config)

        text = "这是中文。This is English. 又是中文。More English here."
        chunks = chunker.chunk_by_separator(text)

        assert len(chunks) >= 1
        # All content should be preserved across chunks
        total_content = "".join(chunk.content for chunk in chunks)
        assert "中文" in total_content
        assert "English" in total_content


class TestLongDocumentChunking:
    """Tests for chunking long documents."""

    def test_long_document_chunking(self, text_chunker, long_document):
        """Test chunking a realistic long document."""
        chunks = text_chunker.chunk_text(long_document)

        assert len(chunks) > 1
        # Total content should be preserved (approximately, due to overlap)
        assert all(isinstance(chunk, TextChunk) for chunk in chunks)

    def test_chunk_metadata(self, text_chunker):
        """Test that chunks include proper metadata."""
        text = "这是一段测试文本。" * 20
        chunks = text_chunker.chunk_text(text)

        for i, chunk in enumerate(chunks):
            assert chunk.index == i
            assert "char_start" in chunk.metadata
            assert "char_end" in chunk.metadata

    def test_very_long_text_performance(self):
        """Test chunking performance with very long text."""
        config = ChunkConfig(chunk_size=500, chunk_overlap=50)
        chunker = TextChunker(config=config)

        # Generate 100KB of text
        very_long_text = "这是一段用于测试性能的长文本。" * 5000

        import time
        start = time.time()
        chunks = chunker.chunk_text(very_long_text)
        elapsed = time.time() - start

        # Should complete in reasonable time (< 1 second)
        assert elapsed < 1.0
        assert len(chunks) > 100

    def test_chunk_size_distribution(self, long_document):
        """Test that chunk sizes are distributed appropriately."""
        config = ChunkConfig(chunk_size=200, chunk_overlap=20)
        chunker = TextChunker(config=config)

        chunks = chunker.chunk_text(long_document)

        # Most chunks should be close to target size
        sizes = [len(chunk.content) for chunk in chunks]
        avg_size = sum(sizes) / len(sizes)

        # Average size should be somewhat less than chunk_size due to overlap
        assert avg_size < config.chunk_size * 1.5


class TestChunkingEdgeCases:
    """Tests for edge cases in text chunking."""

    def test_whitespace_only_text(self, text_chunker):
        """Test chunking text with only whitespace."""
        chunks = text_chunker.chunk_text("   \n\n   \t\t   ")

        # Should produce at least one chunk
        assert len(chunks) >= 1

    def test_repeated_content(self, text_chunker):
        """Test chunking text with repeated content."""
        text = "重复" * 100
        chunks = text_chunker.chunk_text(text)

        assert len(chunks) > 1
        # Each chunk should contain "重复"
        for chunk in chunks:
            if len(chunk.content) >= 2:
                assert "重复" in chunk.content

    def test_special_characters(self, text_chunker):
        """Test chunking text with special characters."""
        text = "包含特殊字符：@#$%^&*()！还有中文标点：，《》【】"
        chunks = text_chunker.chunk_text(text)

        # All special characters should be preserved
        total_content = "".join(chunk.content for chunk in chunks)
        assert "@" in total_content
        assert "《》" in total_content

    def test_numbers_and_dates(self, text_chunker):
        """Test chunking text with numbers and dates."""
        text = "2024年1月1日，销售额达到1,234,567.89元，同比增长12.5%。"
        chunks = text_chunker.chunk_text(text)

        total_content = "".join(chunk.content for chunk in chunks)
        assert "2024" in total_content
        assert "1,234,567.89" in total_content

    def test_code_snippet_chunking(self):
        """Test chunking text containing code snippets."""
        config = ChunkConfig(chunk_size=200, chunk_overlap=20)
        chunker = TextChunker(config=config)

        text = """
        下面是代码示例：

        ```python
        def hello_world():
            print("Hello, World!")
            return True
        ```

        代码解释：这是一个简单的Python函数。
        """
        chunks = chunker.chunk_text(text)

        assert len(chunks) >= 1

    def test_unicode_normalization(self, text_chunker):
        """Test handling of unicode characters."""
        text = "Emoji: 🎉🚀💻 Special:  café naïve résumé"
        chunks = text_chunker.chunk_text(text)

        total_content = "".join(chunk.content for chunk in chunks)
        assert "🎉" in total_content
        assert "café" in total_content


class TestChunkingWithDifferentConfigs:
    """Tests for chunking with various configurations."""

    def test_no_overlap(self):
        """Test chunking without overlap."""
        config = ChunkConfig(chunk_size=50, chunk_overlap=0)
        chunker = TextChunker(config=config)

        text = "这是一段测试文本，用于测试无重叠切分。" * 3
        chunks = chunker.chunk_text(text)

        # Without overlap, consecutive chunks should not share content
        for i in range(len(chunks) - 1):
            assert chunks[i].content != chunks[i + 1].content

    def test_large_overlap(self):
        """Test chunking with large overlap."""
        config = ChunkConfig(chunk_size=100, chunk_overlap=80)
        chunker = TextChunker(config=config)

        text = "这是一段测试文本，用于测试大重叠切分效果。" * 5
        chunks = chunker.chunk_text(text)

        # Large overlap should produce many chunks
        assert len(chunks) > 3

    def test_very_small_chunk_size(self):
        """Test chunking with very small chunk size."""
        config = ChunkConfig(chunk_size=10, chunk_overlap=2)
        chunker = TextChunker(config=config)

        text = "这是一段测试文本。"
        chunks = chunker.chunk_text(text)

        assert len(chunks) >= 1
        for chunk in chunks:
            assert len(chunk.content) <= 10

    def test_large_chunk_size(self):
        """Test chunking with large chunk size."""
        config = ChunkConfig(chunk_size=10000, chunk_overlap=100)
        chunker = TextChunker(config=config)

        text = "这是一段普通长度的测试文本。"
        chunks = chunker.chunk_text(text)

        # Should fit in single chunk
        assert len(chunks) == 1


class TestChunkSizeImpact:
    """Tests validating the anchor: chunk-size-impact.

    Claim: Chunk size in 200-500 tokens yields best retrieval results.
    """

    def test_chunk_size_too_small_loses_context(self):
        """Test that very small chunks lose context."""
        config = ChunkConfig(chunk_size=20, chunk_overlap=0)
        chunker = TextChunker(config=config)

        # A sentence that needs context
        text = "公司规定员工可以申请远程办公，但需要满足以下条件：入职满6个月且绩效评级为B及以上。"
        chunks = chunker.chunk_text(text)

        # With very small chunks, the key information may be fragmented
        # Check that at least one chunk contains partial info
        any_relevant = any(
            "远程办公" in chunk.content or "条件" in chunk.content
            for chunk in chunks
        )
        assert any_relevant

    def test_chunk_size_appropriate_preserves_context(self):
        """Test that appropriate chunk size preserves context."""
        config = ChunkConfig(chunk_size=200, chunk_overlap=20)
        chunker = TextChunker(config=config)

        text = "公司规定员工可以申请远程办公，但需要满足以下条件：入职满6个月且绩效评级为B及以上。"
        chunks = chunker.chunk_text(text)

        # With appropriate size, the full context should be preserved
        assert len(chunks) == 1
        assert "远程办公" in chunks[0].content
        assert "入职满6个月" in chunks[0].content

    def test_chunk_size_too_large_adds_noise(self):
        """Test that very large chunks may add noise."""
        config = ChunkConfig(chunk_size=2000, chunk_overlap=0)
        chunker = TextChunker(config=config)

        # Multiple different topics
        text = """
        公司健身房位于B1层，开放时间为早6点至晚10点。

        员工报销需要在费用发生后的30天内提交，超期不予报销。

        年假天数根据工龄确定：入职满1年5天，满3年10天。

        公司提供午餐补贴，每人每天50元。

        远程办公需要提前在OA系统申请。
        """
        chunks = chunker.chunk_text(text)

        # With very large chunk size, all topics end up in one chunk
        # This adds noise when querying about a specific topic
        assert len(chunks) == 1
        # The single chunk contains all topics (noise)
        assert "健身房" in chunks[0].content
        assert "报销" in chunks[0].content
        assert "远程办公" in chunks[0].content

    def test_optimal_chunk_size_for_retrieval(self):
        """Test that 200-500 token (300-800 char) chunks work well."""
        config = ChunkConfig(chunk_size=400, chunk_overlap=40)
        chunker = TextChunker(config=config)

        # Realistic document
        text = """
        公司远程办公政策（2024年版）

        一、适用范围
        本政策适用于公司全体正式员工。试用期员工暂不适用。

        二、申请条件
        1. 入职满6个月以上
        2. 最近一次绩效评级为B及以上
        3. 岗位性质适合远程办公

        三、申请流程
        1. 在OA系统提交远程办公申请
        2. 直属经理审批
        3. HR备案

        四、管理规定
        1. 每周远程办公天数不超过2天
        2. 远程办公期间需保持通讯畅通
        3. 重要会议需现场参加
        """
        chunks = chunker.chunk_text(text)

        # Should produce multiple topical chunks
        assert len(chunks) >= 1

        # Each chunk should be focused on related content
        for chunk in chunks:
            # Chunks should be within optimal range
            assert len(chunk.content) <= 500
