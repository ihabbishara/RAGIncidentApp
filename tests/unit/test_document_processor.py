"""Unit tests for DocumentProcessor."""

import pytest
from src.ingestion.document_processor import DocumentProcessor
from src.config import Settings


class TestDocumentProcessor:
    """Test DocumentProcessor class."""

    def test_processor_initialization(self, settings: Settings):
        """Test processor initialization."""
        processor = DocumentProcessor(settings)
        assert processor.chunk_size == settings.rag_chunk_size
        assert processor.chunk_overlap == settings.rag_chunk_overlap

    def test_process_single_document(self, settings: Settings, sample_confluence_docs: list):
        """Test processing single document."""
        processor = DocumentProcessor(settings)
        documents = [sample_confluence_docs[0]]

        chunks = processor.process_documents(documents)

        assert len(chunks) > 0
        assert all("content" in chunk for chunk in chunks)
        assert all("metadata" in chunk for chunk in chunks)
        assert all("chunk_id" in chunk for chunk in chunks)

    def test_process_multiple_documents(self, settings: Settings, sample_confluence_docs: list):
        """Test processing multiple documents."""
        processor = DocumentProcessor(settings)

        chunks = processor.process_documents(sample_confluence_docs)

        assert len(chunks) > 0
        # Should create multiple chunks from multiple documents
        assert len(chunks) >= len(sample_confluence_docs)

    def test_chunk_metadata(self, settings: Settings, sample_confluence_docs: list):
        """Test chunk metadata contains required fields."""
        processor = DocumentProcessor(settings)

        chunks = processor.process_documents(sample_confluence_docs)

        for chunk in chunks:
            metadata = chunk["metadata"]
            # Check metadata fields
            assert "space_key" in metadata
            assert "url" in metadata
            assert "chunk_index" in metadata
            assert "total_chunks" in metadata
            # Check chunk-level fields
            assert "title" in chunk
            assert "document_id" in chunk

    def test_chunk_size_limit(self, settings: Settings):
        """Test that chunks respect size limits."""
        processor = DocumentProcessor(settings)
        # Create a very long document
        long_doc = {
            "id": "test_001",
            "title": "Long Document",
            "content": "This is a sentence. " * 1000,  # Very long content
            "space": "TEST",
            "url": "https://test.com",
            "labels": ["test"],
        }

        chunks = processor.process_documents([long_doc])

        # Should split into multiple chunks
        assert len(chunks) > 1
        # Each chunk should be roughly within size limit (with some tolerance)
        for chunk in chunks:
            assert len(chunk["content"]) <= settings.rag_chunk_size * 1.5

    def test_create_metadata_text(self, settings: Settings, sample_confluence_docs: list):
        """Test metadata text creation for embedding."""
        processor = DocumentProcessor(settings)
        chunks = processor.process_documents(sample_confluence_docs)

        metadata_text = processor.create_metadata_text(chunks[0])

        assert isinstance(metadata_text, str)
        assert chunks[0]["content"] in metadata_text
        assert chunks[0]["title"] in metadata_text
