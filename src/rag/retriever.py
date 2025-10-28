"""Retrieval module for semantic search in vector store."""

from typing import List, Dict, Any

from loguru import logger

from src.config import Settings
from src.rag.vector_store import VectorStore
from src.ingestion.embedder import Embedder


class Retriever:
    """Semantic search and retrieval from vector store."""

    def __init__(self, settings: Settings, vector_store: VectorStore, embedder: Embedder):
        """
        Initialize retriever.

        Args:
            settings: Application settings
            vector_store: Vector store instance
            embedder: Embedder instance for query embedding
        """
        self.settings = settings
        self.vector_store = vector_store
        self.embedder = embedder
        self.top_k = settings.rag_top_k_results
        self.similarity_threshold = settings.rag_similarity_threshold

        logger.info(
            f"Initialized Retriever with top_k={self.top_k}, "
            f"threshold={self.similarity_threshold}"
        )

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        filters: Dict[str, Any] | None = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query.

        Args:
            query: Search query text
            top_k: Number of results to return (overrides default)
            filters: Optional metadata filters

        Returns:
            List of retrieved documents with metadata and scores
        """
        if not query or not query.strip():
            logger.warning("Empty query provided")
            return []

        n_results = top_k if top_k is not None else self.top_k

        logger.info(f"Retrieving top {n_results} documents for query: {query[:100]}...")

        try:
            # Generate query embedding
            query_embedding = self.embedder.embed_text(query)

            # Query vector store
            results = self.vector_store.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=filters,
            )

            # Process results
            documents = self._process_results(results)

            # Filter by similarity threshold
            filtered_documents = [
                doc
                for doc in documents
                if doc["score"] >= self.similarity_threshold
            ]

            logger.info(
                f"Retrieved {len(filtered_documents)}/{len(documents)} documents "
                f"above threshold {self.similarity_threshold}"
            )

            return filtered_documents

        except Exception as e:
            logger.error(f"Error during retrieval: {e}")
            raise

    def _process_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process raw ChromaDB results into structured format.

        Args:
            results: Raw results from ChromaDB

        Returns:
            List of processed documents
        """
        documents = []

        ids = results.get("ids", [[]])[0]
        docs = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for idx, doc_id in enumerate(ids):
            # Convert distance to similarity score (ChromaDB uses cosine distance)
            # Cosine distance range: [0, 2], similarity: 1 - (distance / 2)
            distance = distances[idx] if idx < len(distances) else 1.0
            similarity_score = 1.0 - (distance / 2.0)

            document = {
                "id": doc_id,
                "content": docs[idx] if idx < len(docs) else "",
                "metadata": metadatas[idx] if idx < len(metadatas) else {},
                "score": similarity_score,
                "distance": distance,
            }

            documents.append(document)

        return documents

    def retrieve_with_context(
        self,
        query: str,
        max_context_length: int | None = None,
    ) -> Dict[str, Any]:
        """
        Retrieve documents and format them as context for LLM.

        Args:
            query: Search query
            max_context_length: Maximum context length in characters

        Returns:
            Dictionary with query, context, and source documents
        """
        max_length = (
            max_context_length
            if max_context_length is not None
            else self.settings.rag_max_context_length
        )

        # Retrieve relevant documents
        documents = self.retrieve(query)

        if not documents:
            logger.warning("No relevant documents found for query")
            return {
                "query": query,
                "context": "",
                "sources": [],
                "num_sources": 0,
            }

        # Build context from documents
        context_parts = []
        sources = []
        current_length = 0

        for doc in documents:
            content = doc["content"]
            metadata = doc["metadata"]

            # Create source reference
            title = metadata.get("title", "Unknown")
            url = metadata.get("url", "")
            chunk_index = metadata.get("chunk_index", 0)

            source = {
                "title": title,
                "url": url,
                "chunk_index": chunk_index,
                "score": doc["score"],
            }

            # Add to context if within length limit
            if current_length + len(content) <= max_length:
                context_parts.append(f"[Source: {title}]\n{content}")
                sources.append(source)
                current_length += len(content)
            else:
                # Add truncated content to reach max_length
                remaining_length = max_length - current_length
                if remaining_length > 100:  # Only add if meaningful amount remains
                    truncated_content = content[:remaining_length] + "..."
                    context_parts.append(f"[Source: {title}]\n{truncated_content}")
                    sources.append(source)
                break

        context = "\n\n---\n\n".join(context_parts)

        logger.info(f"Built context with {len(sources)} sources ({len(context)} chars)")

        return {
            "query": query,
            "context": context,
            "sources": sources,
            "num_sources": len(sources),
        }

    def get_similar_documents(
        self, document_id: str, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find documents similar to a given document.

        Args:
            document_id: ID of the reference document
            top_k: Number of similar documents to return

        Returns:
            List of similar documents
        """
        try:
            # Get the document by ID
            results = self.vector_store.get_by_ids([document_id])

            if not results.get("documents"):
                logger.warning(f"Document {document_id} not found")
                return []

            # Use the document's embedding to find similar documents
            # Note: This requires getting the embedding from vector store
            # For now, we'll use the document text to query
            document_text = results["documents"][0]

            # Query for similar documents (excluding the original)
            similar_docs = self.retrieve(document_text, top_k=top_k + 1)

            # Filter out the original document
            similar_docs = [doc for doc in similar_docs if doc["id"] != document_id][:top_k]

            logger.info(f"Found {len(similar_docs)} similar documents to {document_id}")
            return similar_docs

        except Exception as e:
            logger.error(f"Error finding similar documents: {e}")
            return []
