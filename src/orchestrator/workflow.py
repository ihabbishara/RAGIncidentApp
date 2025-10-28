"""Main workflow orchestration logic."""

from typing import Dict, Any, Optional

from loguru import logger

from src.config import Settings
from src.rag.retriever import Retriever
from src.rag.generator import Generator
from src.servicenow.client import ServiceNowClient
from src.servicenow.incident_builder import IncidentBuilder
from src.teams.client import TeamsClient


class WorkflowOrchestrator:
    """Orchestrate the RAG-based incident creation workflow."""

    def __init__(
        self,
        settings: Settings,
        retriever: Retriever,
        generator: Generator,
        servicenow_client: ServiceNowClient,
        incident_builder: IncidentBuilder,
        teams_client: Optional[TeamsClient] = None,
    ):
        """
        Initialize workflow orchestrator.

        Args:
            settings: Application settings
            retriever: Retriever instance
            generator: Generator (LLM) instance
            servicenow_client: ServiceNow API client
            incident_builder: Incident builder instance
            teams_client: Microsoft Teams client (optional)
        """
        self.settings = settings
        self.retriever = retriever
        self.generator = generator
        self.servicenow_client = servicenow_client
        self.incident_builder = incident_builder
        self.teams_client = teams_client

        logger.info("Initialized WorkflowOrchestrator")

    async def process_email(self, parsed_email: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process incoming email and create ServiceNow incident.

        Workflow:
        1. Extract incident information from email
        2. Search knowledge base using RAG
        3. Generate incident summary using LLM
        4. Create ServiceNow incident
        5. Return result

        Args:
            parsed_email: Parsed email data

        Returns:
            Workflow result with incident details
        """
        email_from = parsed_email.get("from", "unknown")
        email_subject = parsed_email.get("subject", "No Subject")
        email_body = parsed_email.get("body", "")

        logger.info(f"Processing email from {email_from}: {email_subject}")

        try:
            # Step 1: Prepare query from email
            query = f"{email_subject}\n\n{email_body}"

            # Step 2: Retrieve relevant context from knowledge base
            logger.info("Retrieving relevant knowledge base articles...")
            retrieval_result = self.retriever.retrieve_with_context(query)

            context = retrieval_result.get("context", "")
            sources = retrieval_result.get("sources", [])
            has_kb_match = len(sources) > 0

            if has_kb_match:
                logger.info(f"Found {len(sources)} relevant KB articles")
            else:
                logger.warning("No relevant KB articles found")

            # Step 3: Generate incident summary using LLM
            logger.info("Generating incident summary with LLM...")
            llm_output = await self.generator.generate_incident_summary(
                email_content=query,
                context=context,
                has_kb_match=has_kb_match,
            )

            # Step 4: Build ServiceNow incident payload
            logger.info("Building ServiceNow incident...")
            incident_data = self.incident_builder.build_from_llm_output(
                llm_output=llm_output,
                email_from=email_from,
                email_subject=email_subject,
            )

            # Step 5: Create incident in ServiceNow
            logger.info("Creating incident in ServiceNow...")
            incident = await self.servicenow_client.create_incident(incident_data)

            incident_number = incident.get("number", "Unknown")
            incident_sys_id = incident.get("sys_id", "Unknown")

            logger.info(
                f"Successfully created incident {incident_number} (sys_id: {incident_sys_id})"
            )

            # Step 6: Send Teams notification (if enabled)
            if self.teams_client:
                try:
                    logger.info("Sending Teams notification...")
                    await self.teams_client.send_incident_notification(
                        incident_data=incident,
                        llm_summary=llm_output,
                        kb_sources=sources,
                    )
                except Exception as teams_error:
                    # Don't fail the whole workflow if Teams notification fails
                    logger.error(f"Failed to send Teams notification: {teams_error}")

            # Return result
            result = {
                "success": True,
                "incident_number": incident_number,
                "incident_sys_id": incident_sys_id,
                "has_kb_match": has_kb_match,
                "kb_sources_count": len(sources),
                "kb_sources": sources,
                "email_from": email_from,
                "email_subject": email_subject,
                "llm_summary": llm_output,
            }

            return result

        except Exception as e:
            logger.error(f"Error processing email workflow: {e}")

            # Try to create minimal incident as fallback
            try:
                logger.warning("Attempting fallback incident creation...")
                incident_data = self.incident_builder.build_from_email(
                    email_from=email_from,
                    email_subject=email_subject,
                    email_body=email_body,
                )

                incident = await self.servicenow_client.create_incident(incident_data)

                return {
                    "success": True,
                    "fallback": True,
                    "incident_number": incident.get("number", "Unknown"),
                    "incident_sys_id": incident.get("sys_id", "Unknown"),
                    "error": str(e),
                }

            except Exception as fallback_error:
                logger.error(f"Fallback incident creation also failed: {fallback_error}")

                return {
                    "success": False,
                    "error": str(e),
                    "fallback_error": str(fallback_error),
                }

    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of all components.

        Returns:
            Health status of all components
        """
        logger.info("Performing health check...")

        health = {
            "overall": "healthy",
            "components": {},
        }

        # Check LLM
        try:
            llm_healthy = await self.generator.check_health()
            health["components"]["llm"] = "healthy" if llm_healthy else "unhealthy"
        except Exception as e:
            logger.error(f"LLM health check failed: {e}")
            health["components"]["llm"] = "unhealthy"
            health["overall"] = "degraded"

        # Check ServiceNow
        try:
            sn_healthy = await self.servicenow_client.check_health()
            health["components"]["servicenow"] = "healthy" if sn_healthy else "unhealthy"
        except Exception as e:
            logger.error(f"ServiceNow health check failed: {e}")
            health["components"]["servicenow"] = "unhealthy"
            health["overall"] = "degraded"

        # Check Vector Store
        try:
            doc_count = self.retriever.vector_store.count()
            health["components"]["vector_store"] = {
                "status": "healthy",
                "document_count": doc_count,
            }
        except Exception as e:
            logger.error(f"Vector store health check failed: {e}")
            health["components"]["vector_store"] = {"status": "unhealthy"}
            health["overall"] = "degraded"

        # Check Teams (if enabled)
        if self.teams_client and self.teams_client.enabled:
            try:
                teams_healthy = await self.teams_client.check_health()
                health["components"]["teams"] = "healthy" if teams_healthy else "unhealthy"
                if not teams_healthy:
                    health["overall"] = "degraded"
            except Exception as e:
                logger.error(f"Teams health check failed: {e}")
                health["components"]["teams"] = "unhealthy"
                health["overall"] = "degraded"
        else:
            health["components"]["teams"] = "disabled"

        logger.info(f"Health check complete: {health['overall']}")
        return health
