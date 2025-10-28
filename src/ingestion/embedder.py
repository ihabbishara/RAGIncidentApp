"""Embedding generation module using sentence-transformers."""

from typing import List

from sentence_transformers import SentenceTransformer
from loguru import logger

from src.config import Settings


class Embedder:
    """Generate embeddings for text using sentence-transformers."""

    def __init__(self, settings: Settings):
        """
        Initialize embedder with specified model.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.model_name = settings.embedding_model
        self.device = settings.embedding_device
        self.batch_size = settings.embedding_batch_size

        logger.info(f"Loading embedding model: {self.model_name} on {self.device}")

        try:
            self.model = SentenceTransformer(self.model_name, device=self.device)
            logger.info(f"Successfully loaded embedding model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to load embedding model {self.model_name}: {e}")
            raise

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Input text

        Returns:
            Embedding vector as list of floats
        """
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch.

        Args:
            texts: List of input texts

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        try:
            logger.debug(f"Generating embeddings for {len(texts)} texts")

            embeddings = self.model.encode(
                texts,
                batch_size=self.batch_size,
                show_progress_bar=len(texts) > 10,
                convert_to_numpy=True,
            )

            return [emb.tolist() for emb in embeddings]

        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise

    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings produced by the model.

        Returns:
            Embedding dimension
        """
        return self.model.get_sentence_embedding_dimension()
