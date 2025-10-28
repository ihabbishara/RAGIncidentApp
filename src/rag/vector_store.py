"""Vector store implementation using ChromaDB."""

from typing import List, Dict, Any, Optional
from pathlib import Path

import chromadb
from chromadb.config import Settings as ChromaSettings
from loguru import logger

from src.config import Settings


class VectorStore:
    """Vector database operations using ChromaDB."""

    def __init__(self, settings: Settings):
        """
        Initialize ChromaDB vector store.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.collection_name = settings.vectordb_collection_name
        self.persist_directory = settings.vectordb_path

        # Ensure persist directory exists
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)

        logger.info(f"Initializing ChromaDB at {self.persist_directory}")

        # Initialize ChromaDB client
        try:
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                ),
            )

            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},  # Use cosine similarity
            )

            logger.info(f"ChromaDB collection '{self.collection_name}' ready")
            logger.info(f"Collection contains {self.collection.count()} documents")

        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise

    def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str],
        embeddings: Optional[List[List[float]]] = None,
    ) -> None:
        """
        Add documents to the vector store.

        Args:
            documents: List of text documents
            metadatas: List of metadata dictionaries
            ids: List of unique document IDs
            embeddings: Optional pre-computed embeddings (if None, ChromaDB will compute)
        """
        if not documents:
            logger.warning("No documents to add")
            return

        if len(documents) != len(metadatas) or len(documents) != len(ids):
            raise ValueError("documents, metadatas, and ids must have same length")

        try:
            logger.info(f"Adding {len(documents)} documents to ChromaDB")

            # Prepare metadata (ChromaDB requires all values to be strings, ints, or floats)
            processed_metadatas = []
            for metadata in metadatas:
                processed_metadata = {}
                for key, value in metadata.items():
                    if isinstance(value, (str, int, float, bool)):
                        processed_metadata[key] = value
                    elif isinstance(value, list):
                        # Convert lists to comma-separated strings
                        processed_metadata[key] = ",".join(str(v) for v in value)
                    else:
                        processed_metadata[key] = str(value)
                processed_metadatas.append(processed_metadata)

            # Add to collection
            if embeddings:
                self.collection.add(
                    documents=documents,
                    metadatas=processed_metadatas,
                    ids=ids,
                    embeddings=embeddings,
                )
            else:
                self.collection.add(
                    documents=documents, metadatas=processed_metadatas, ids=ids
                )

            logger.info(f"Successfully added {len(documents)} documents")
            logger.info(f"Total documents in collection: {self.collection.count()}")

        except Exception as e:
            logger.error(f"Error adding documents to ChromaDB: {e}")
            raise

    def query(
        self,
        query_texts: Optional[List[str]] = None,
        query_embeddings: Optional[List[List[float]]] = None,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Query the vector store for similar documents.

        Args:
            query_texts: Text queries
            query_embeddings: Pre-computed query embeddings
            n_results: Number of results to return
            where: Metadata filter
            where_document: Document content filter

        Returns:
            Query results containing documents, metadatas, distances, and ids
        """
        if not query_texts and not query_embeddings:
            raise ValueError("Must provide either query_texts or query_embeddings")

        try:
            logger.debug(f"Querying ChromaDB for {n_results} results")

            results = self.collection.query(
                query_texts=query_texts,
                query_embeddings=query_embeddings,
                n_results=n_results,
                where=where,
                where_document=where_document,
            )

            logger.debug(f"Query returned {len(results.get('ids', [[]])[0])} results")
            return results

        except Exception as e:
            logger.error(f"Error querying ChromaDB: {e}")
            raise

    def get_by_ids(self, ids: List[str]) -> Dict[str, Any]:
        """
        Get documents by their IDs.

        Args:
            ids: List of document IDs

        Returns:
            Documents and their metadata
        """
        try:
            results = self.collection.get(ids=ids)
            return results
        except Exception as e:
            logger.error(f"Error getting documents by IDs: {e}")
            raise

    def delete_by_ids(self, ids: List[str]) -> None:
        """
        Delete documents by their IDs.

        Args:
            ids: List of document IDs to delete
        """
        try:
            self.collection.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} documents")
        except Exception as e:
            logger.error(f"Error deleting documents: {e}")
            raise

    def count(self) -> int:
        """
        Get the total number of documents in the collection.

        Returns:
            Document count
        """
        return self.collection.count()

    def clear(self) -> None:
        """Clear all documents from the collection."""
        try:
            # Delete the collection and recreate it
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(f"Cleared collection '{self.collection_name}'")
        except Exception as e:
            logger.error(f"Error clearing collection: {e}")
            raise

    def reset(self) -> None:
        """Reset the entire ChromaDB database."""
        try:
            self.client.reset()
            # Recreate collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            logger.warning("ChromaDB database has been reset")
        except Exception as e:
            logger.error(f"Error resetting ChromaDB: {e}")
            raise
