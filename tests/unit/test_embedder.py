"""Unit tests for Embedder."""

import pytest
from src.ingestion.embedder import Embedder
from src.config import Settings


class TestEmbedder:
    """Test Embedder class."""

    def test_embedder_initialization(self, settings: Settings):
        """Test embedder initialization."""
        embedder = Embedder(settings)
        assert embedder.model is not None
        assert embedder.model_name == settings.embedding_model

    def test_embed_single_text(self, settings: Settings):
        """Test embedding single text."""
        embedder = Embedder(settings)
        text = "This is a test document for embedding."

        # embed_batch works for single text too
        embeddings = embedder.embed_batch([text])
        embedding = embeddings[0]

        assert embedding is not None
        assert len(embedding) > 0
        assert isinstance(embedding, list)
        assert all(isinstance(x, float) for x in embedding)

    def test_embed_batch(self, settings: Settings):
        """Test embedding batch of texts."""
        embedder = Embedder(settings)
        texts = [
            "First test document.",
            "Second test document.",
            "Third test document.",
        ]

        embeddings = embedder.embed_batch(texts)

        assert len(embeddings) == len(texts)
        assert all(len(emb) > 0 for emb in embeddings)
        assert all(isinstance(emb, list) for emb in embeddings)

    def test_embed_empty_text(self, settings: Settings):
        """Test embedding empty text."""
        embedder = Embedder(settings)

        embeddings = embedder.embed_batch([""])
        embedding = embeddings[0]

        assert embedding is not None
        assert len(embedding) > 0

    def test_embedding_dimension_consistency(self, settings: Settings):
        """Test that all embeddings have the same dimension."""
        embedder = Embedder(settings)
        texts = [
            "Short text.",
            "This is a much longer text with more words and content.",
            "Medium length text here.",
        ]

        embeddings = embedder.embed_batch(texts)

        dimensions = [len(emb) for emb in embeddings]
        assert len(set(dimensions)) == 1, "All embeddings should have same dimension"
