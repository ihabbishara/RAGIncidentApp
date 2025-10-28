#!/usr/bin/env python3
"""
Confluence ingestion script.

This script fetches Confluence pages and loads them into the vector database.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger

from src.config import get_settings
from src.config.logging_config import setup_logging
from src.ingestion.confluence_client import ConfluenceClient
from src.ingestion.document_processor import DocumentProcessor
from src.ingestion.embedder import Embedder
from src.rag.vector_store import VectorStore


async def main():
    """Main ingestion workflow."""
    # Initialize settings and logging
    settings = get_settings()
    setup_logging(settings)

    logger.info("=" * 80)
    logger.info("Starting Confluence Data Ingestion")
    logger.info("=" * 80)

    try:
        # Step 1: Initialize components
        logger.info("\n[1/6] Initializing components...")

        confluence_client = ConfluenceClient(settings)
        document_processor = DocumentProcessor(settings)
        embedder = Embedder(settings)
        vector_store = VectorStore(settings)

        logger.info("✅ Components initialized")

        # Step 2: Fetch Confluence documents
        logger.info("\n[2/6] Fetching Confluence documents...")
        logger.info(f"  - Space keys: {settings.confluence_spaces_list}")
        logger.info(f"  - Labels: {settings.confluence_labels_list}")

        documents = await confluence_client.ingest_documents()

        if not documents:
            logger.warning("⚠️  No documents fetched from Confluence")
            logger.info("Please check:")
            logger.info("  - Confluence URL is correct")
            logger.info("  - Credentials are valid")
            logger.info("  - Space keys and labels are configured")
            return

        logger.info(f"✅ Fetched {len(documents)} documents")

        # Step 3: Process and chunk documents
        logger.info("\n[3/6] Processing and chunking documents...")
        logger.info(f"  - Chunk size: {settings.rag_chunk_size}")
        logger.info(f"  - Chunk overlap: {settings.rag_chunk_overlap}")

        chunks = document_processor.process_documents(documents)

        logger.info(f"✅ Created {len(chunks)} chunks from {len(documents)} documents")

        # Step 4: Generate embeddings
        logger.info("\n[4/6] Generating embeddings...")
        logger.info(f"  - Model: {settings.embedding_model}")
        logger.info(f"  - Device: {settings.embedding_device}")
        logger.info(f"  - Batch size: {settings.embedding_batch_size}")

        # Prepare texts for embedding (with metadata enrichment)
        texts = [
            document_processor.create_metadata_text(chunk) for chunk in chunks
        ]

        # Generate embeddings in batch
        embeddings = embedder.embed_batch(texts)

        logger.info(f"✅ Generated {len(embeddings)} embeddings")

        # Step 5: Store in vector database
        logger.info("\n[5/6] Storing in vector database...")
        logger.info(f"  - Collection: {settings.vectordb_collection_name}")
        logger.info(f"  - Path: {settings.vectordb_path}")

        # Prepare data for vector store
        ids = [chunk["chunk_id"] for chunk in chunks]
        documents_content = [chunk["content"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]

        # Add to vector store
        vector_store.add_documents(
            documents=documents_content,
            metadatas=metadatas,
            ids=ids,
            embeddings=embeddings,
        )

        logger.info(f"✅ Stored {len(chunks)} chunks in vector database")

        # Step 6: Verify storage
        logger.info("\n[6/6] Verifying storage...")

        total_docs = vector_store.count()
        logger.info(f"✅ Vector database now contains {total_docs} total documents")

        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("Ingestion Complete!")
        logger.info("=" * 80)
        logger.info(f"📄 Documents fetched: {len(documents)}")
        logger.info(f"📦 Chunks created: {len(chunks)}")
        logger.info(f"🔢 Embeddings generated: {len(embeddings)}")
        logger.info(f"💾 Total in database: {total_docs}")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"\n❌ Ingestion failed: {e}")
        logger.exception("Full error details:")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
