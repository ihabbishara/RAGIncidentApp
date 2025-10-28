"""Main application entry point."""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from loguru import logger

from src.config import Settings, get_settings
from src.config.logging_config import setup_logging
from src.email_receiver.smtp_server import SMTPServer
from src.ingestion.embedder import Embedder
from src.rag.vector_store import VectorStore
from src.rag.retriever import Retriever
from src.rag.generator import Generator
from src.servicenow.client import ServiceNowClient
from src.servicenow.incident_builder import IncidentBuilder
from src.teams.client import TeamsClient
from src.orchestrator.workflow import WorkflowOrchestrator


# Global instances
smtp_server: SMTPServer | None = None
orchestrator: WorkflowOrchestrator | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting RAG Incident System...")

    settings = get_settings()
    setup_logging(settings)

    # Initialize components
    logger.info("Initializing components...")

    try:
        # Initialize embedder
        embedder = Embedder(settings)

        # Initialize vector store
        vector_store = VectorStore(settings)

        # Initialize retriever
        retriever = Retriever(settings, vector_store, embedder)

        # Initialize generator (LLM)
        generator = Generator(settings)

        # Initialize ServiceNow client
        servicenow_client = ServiceNowClient(settings)
        incident_builder = IncidentBuilder(settings)

        # Initialize Teams client (optional)
        teams_client = TeamsClient(settings)

        # Initialize orchestrator
        global orchestrator
        orchestrator = WorkflowOrchestrator(
            settings=settings,
            retriever=retriever,
            generator=generator,
            servicenow_client=servicenow_client,
            incident_builder=incident_builder,
            teams_client=teams_client,
        )

        # Start SMTP server
        global smtp_server
        smtp_server = SMTPServer(settings, email_callback=orchestrator.process_email)
        smtp_server.start()

        logger.info("✅ RAG Incident System started successfully")
        logger.info(f"SMTP server listening on {settings.smtp_host}:{settings.smtp_port}")
        logger.info(f"API server running on {settings.app_host}:{settings.app_port}")

        yield

    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise

    # Shutdown
    logger.info("Shutting down RAG Incident System...")

    if smtp_server:
        smtp_server.stop()

    logger.info("✅ RAG Incident System shut down successfully")


# Create FastAPI app
app = FastAPI(
    title="RAG Incident Management System",
    description="Automated incident creation using RAG and email triggers",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "RAG Incident Management System",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns health status of all components.
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        health = await orchestrator.health_check()
        status_code = 200 if health["overall"] == "healthy" else 503

        return JSONResponse(content=health, status_code=status_code)

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            content={"overall": "unhealthy", "error": str(e)},
            status_code=503,
        )


@app.get("/stats")
async def get_stats():
    """
    Get system statistics.

    Returns statistics about vector store and processing.
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Service not initialized")

    try:
        vector_store = orchestrator.retriever.vector_store
        doc_count = vector_store.count()

        return {
            "vector_store": {
                "document_count": doc_count,
                "collection_name": vector_store.collection_name,
            }
        }

    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/test-email")
async def test_email_processing(email_data: dict):
    """
    Test endpoint for processing email without SMTP.

    Useful for testing the workflow without sending actual emails.

    Args:
        email_data: Dictionary with 'from', 'subject', 'body'

    Returns:
        Processing result
    """
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Service not initialized")

    # Validate input
    required_fields = ["from", "subject", "body"]
    for field in required_fields:
        if field not in email_data:
            raise HTTPException(
                status_code=400, detail=f"Missing required field: {field}"
            )

    try:
        # Process email
        result = await orchestrator.process_email(email_data)

        return result

    except Exception as e:
        logger.error(f"Test email processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()

    uvicorn.run(
        "src.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
    )
