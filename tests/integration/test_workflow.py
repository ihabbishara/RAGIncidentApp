"""Integration tests for complete workflow."""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from src.orchestrator.workflow import WorkflowOrchestrator
from src.config import Settings


class TestWorkflowIntegration:
    """Test complete workflow integration."""

    @pytest.mark.asyncio
    async def test_health_check(self, settings: Settings):
        """Test health check integration."""
        # Create mocked components
        retriever = Mock()
        retriever.vector_store = Mock()
        retriever.vector_store.count = Mock(return_value=10)

        generator = Mock()
        generator.check_health = AsyncMock(return_value=True)

        servicenow_client = Mock()
        servicenow_client.check_health = AsyncMock(return_value=True)

        incident_builder = Mock()

        # Create orchestrator
        orchestrator = WorkflowOrchestrator(
            settings=settings,
            retriever=retriever,
            generator=generator,
            servicenow_client=servicenow_client,
            incident_builder=incident_builder,
        )

        # Run health check
        health = await orchestrator.health_check()

        assert health["overall"] == "healthy"
        assert health["components"]["llm"] == "healthy"
        assert health["components"]["servicenow"] == "healthy"
        assert health["components"]["vector_store"]["status"] == "healthy"
        assert health["components"]["vector_store"]["document_count"] == 10

    @pytest.mark.asyncio
    async def test_process_email_workflow(
        self, settings: Settings, sample_email_data: dict, sample_llm_output: dict
    ):
        """Test complete email processing workflow."""
        # Create mocked components
        retriever = Mock()
        retriever.retrieve_with_context = Mock(
            return_value={
                "context": "Sample context from knowledge base",
                "sources": [{"title": "KB Article 1", "url": "http://kb.com/1"}],
            }
        )

        generator = Mock()
        generator.generate_incident_summary = AsyncMock(return_value=sample_llm_output)

        servicenow_client = Mock()
        servicenow_client.create_incident = AsyncMock(
            return_value={"number": "INC0001", "sys_id": "abc123"}
        )

        incident_builder = Mock()
        incident_builder.build_from_llm_output = Mock(
            return_value={"short_description": "Test incident"}
        )

        # Create orchestrator
        orchestrator = WorkflowOrchestrator(
            settings=settings,
            retriever=retriever,
            generator=generator,
            servicenow_client=servicenow_client,
            incident_builder=incident_builder,
        )

        # Process email
        result = await orchestrator.process_email(sample_email_data)

        # Verify result
        assert result["success"] is True
        assert result["incident_number"] == "INC0001"
        assert result["incident_sys_id"] == "abc123"
        assert result["has_kb_match"] is True
        assert result["kb_sources_count"] == 1

        # Verify components were called
        retriever.retrieve_with_context.assert_called_once()
        generator.generate_incident_summary.assert_called_once()
        servicenow_client.create_incident.assert_called_once()
        incident_builder.build_from_llm_output.assert_called_once()

    @pytest.mark.asyncio
    async def test_workflow_fallback_on_error(self, settings: Settings, sample_email_data: dict):
        """Test workflow fallback when main process fails."""
        # Create mocked components that fail
        retriever = Mock()
        retriever.retrieve_with_context = Mock(side_effect=Exception("Retrieval failed"))

        generator = Mock()
        servicenow_client = Mock()
        servicenow_client.create_incident = AsyncMock(
            return_value={"number": "INC0002", "sys_id": "xyz456"}
        )

        incident_builder = Mock()
        incident_builder.build_from_email = Mock(
            return_value={"short_description": "Fallback incident"}
        )

        # Create orchestrator
        orchestrator = WorkflowOrchestrator(
            settings=settings,
            retriever=retriever,
            generator=generator,
            servicenow_client=servicenow_client,
            incident_builder=incident_builder,
        )

        # Process email (should trigger fallback)
        result = await orchestrator.process_email(sample_email_data)

        # Verify fallback was used
        assert result["success"] is True
        assert result["fallback"] is True
        assert "error" in result
        assert result["incident_number"] == "INC0002"
