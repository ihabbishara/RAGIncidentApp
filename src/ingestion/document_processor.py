"""Document processing and text chunking module."""

import re
from typing import List, Dict, Any

from loguru import logger

from src.config import Settings


class DocumentProcessor:
    """Process and chunk documents for embedding generation."""

    def __init__(self, settings: Settings):
        """
        Initialize document processor.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.chunk_size = settings.rag_chunk_size
        self.chunk_overlap = settings.rag_chunk_overlap

        logger.info(
            f"Initialized DocumentProcessor with chunk_size={self.chunk_size}, "
            f"overlap={self.chunk_overlap}"
        )

    def _split_by_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.

        Args:
            text: Input text

        Returns:
            List of sentences
        """
        # Split by common sentence endings
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [s.strip() for s in sentences if s.strip()]

    def _split_by_words(self, text: str, max_words: int) -> List[str]:
        """
        Split text into chunks by word count.

        Args:
            text: Input text
            max_words: Maximum words per chunk

        Returns:
            List of text chunks
        """
        words = text.split()
        chunks = []

        for i in range(0, len(words), max_words):
            chunk = " ".join(words[i : i + max_words])
            chunks.append(chunk)

        return chunks

    def chunk_text(self, text: str) -> List[str]:
        """
        Chunk text with overlap using sentence-aware splitting.

        Strategy:
        1. Split text into sentences
        2. Group sentences into chunks of approximately chunk_size characters
        3. Add overlap by including last few sentences from previous chunk

        Args:
            text: Input text to chunk

        Returns:
            List of text chunks
        """
        if not text or len(text) < self.chunk_size:
            return [text] if text else []

        sentences = self._split_by_sentences(text)

        chunks = []
        current_chunk = []
        current_length = 0
        overlap_sentences = []

        for sentence in sentences:
            sentence_length = len(sentence)

            # If adding this sentence would exceed chunk size, save current chunk
            if current_length + sentence_length > self.chunk_size and current_chunk:
                # Save the chunk
                chunk_text = " ".join(current_chunk)
                chunks.append(chunk_text)

                # Prepare overlap: keep last sentences that fit within overlap size
                overlap_sentences = []
                overlap_length = 0

                for s in reversed(current_chunk):
                    if overlap_length + len(s) <= self.chunk_overlap:
                        overlap_sentences.insert(0, s)
                        overlap_length += len(s)
                    else:
                        break

                # Start new chunk with overlap
                current_chunk = overlap_sentences.copy()
                current_length = overlap_length

            # Add sentence to current chunk
            current_chunk.append(sentence)
            current_length += sentence_length

        # Add the last chunk if it exists
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append(chunk_text)

        logger.debug(f"Split text of {len(text)} chars into {len(chunks)} chunks")
        return chunks

    def process_document(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process a single document into chunks with metadata.

        Args:
            document: Document with 'content', 'title', 'id', and metadata

        Returns:
            List of processed chunks with metadata
        """
        doc_id = document.get("id", "unknown")
        title = document.get("title", "Untitled")
        content = document.get("content", "")

        if not content:
            logger.warning(f"Empty content for document {doc_id}")
            return []

        # Chunk the content
        chunks = self.chunk_text(content)

        # Create chunk documents with metadata
        processed_chunks = []
        for idx, chunk in enumerate(chunks):
            if not chunk.strip():
                continue

            chunk_doc = {
                "chunk_id": f"{doc_id}_chunk_{idx}",
                "document_id": doc_id,
                "chunk_index": idx,
                "title": title,
                "content": chunk,
                "metadata": {
                    "space_key": document.get("space_key", ""),
                    "space_name": document.get("space_name", ""),
                    "labels": document.get("labels", []),
                    "version": document.get("version", 1),
                    "last_updated": document.get("last_updated", ""),
                    "url": document.get("url", ""),
                    "chunk_index": idx,
                    "total_chunks": len(chunks),
                },
            }

            processed_chunks.append(chunk_doc)

        logger.debug(f"Processed document {doc_id} into {len(processed_chunks)} chunks")
        return processed_chunks

    def process_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process multiple documents into chunks.

        Args:
            documents: List of documents to process

        Returns:
            List of all processed chunks from all documents
        """
        logger.info(f"Processing {len(documents)} documents")

        all_chunks = []
        for doc in documents:
            try:
                chunks = self.process_document(doc)
                all_chunks.extend(chunks)
            except Exception as e:
                doc_id = doc.get("id", "unknown")
                logger.error(f"Error processing document {doc_id}: {e}")
                continue

        logger.info(f"Processed {len(documents)} documents into {len(all_chunks)} chunks")
        return all_chunks

    def create_metadata_text(self, chunk: Dict[str, Any]) -> str:
        """
        Create a metadata-enriched text representation for better embedding.

        Args:
            chunk: Chunk document with metadata

        Returns:
            Enriched text combining title, metadata, and content
        """
        title = chunk.get("title", "")
        content = chunk.get("content", "")
        metadata = chunk.get("metadata", {})

        labels = metadata.get("labels", [])
        space_name = metadata.get("space_name", "")

        # Create enriched text
        parts = []

        if title:
            parts.append(f"Title: {title}")

        if space_name:
            parts.append(f"Space: {space_name}")

        if labels:
            parts.append(f"Tags: {', '.join(labels)}")

        parts.append(content)

        enriched_text = "\n\n".join(parts)
        return enriched_text
