"""Unit tests for IncidentBuilder."""

import pytest
from src.servicenow.incident_builder import IncidentBuilder
from src.config import Settings


class TestIncidentBuilder:
    """Test IncidentBuilder class."""

    def test_builder_initialization(self, settings: Settings):
        """Test builder initialization."""
        builder = IncidentBuilder(settings)
        assert builder.settings == settings

    def test_build_from_email(self, settings: Settings):
        """Test building incident from email."""
        builder = IncidentBuilder(settings)

        incident = builder.build_from_email(
            email_from="test@example.com",
            email_subject="Test Issue",
            email_body="This is a test issue description.",
        )

        assert "short_description" in incident
        assert "description" in incident
        assert "caller_id" in incident
        assert incident["caller_id"] == "test@example.com"
        assert "Test Issue" in incident["short_description"]

    def test_build_from_llm_output(self, settings: Settings, sample_llm_output: dict):
        """Test building incident from LLM output."""
        builder = IncidentBuilder(settings)

        incident = builder.build_from_llm_output(
            llm_output=sample_llm_output,
            email_from="test@example.com",
            email_subject="Database Issues",
        )

        assert "short_description" in incident
        assert "description" in incident
        assert "priority" in incident
        assert "urgency" in incident
        assert "category" in incident
        assert incident["caller_id"] == "test@example.com"

    def test_priority_from_llm_output(self, settings: Settings, sample_llm_output: dict):
        """Test priority is set from LLM output."""
        builder = IncidentBuilder(settings)

        incident = builder.build_from_llm_output(
            llm_output=sample_llm_output,
            email_from="test@example.com",
            email_subject="Database Issues",
        )

        # Priority should be set based on urgency and impact from LLM output
        assert "priority" in incident
        assert "urgency" in incident
        assert "impact" in incident
        # Priority is returned as integer
        assert incident["priority"] in [1, 2, 3, 4, 5]

    def test_add_work_note(self, settings: Settings):
        """Test work note addition."""
        builder = IncidentBuilder(settings)

        work_note = builder.add_work_note("Test work note")

        assert "work_notes" in work_note
        assert "Test work note" in work_note["work_notes"]

    def test_priority_calculation(self, settings: Settings):
        """Test priority calculation from urgency and impact."""
        builder = IncidentBuilder(settings)

        # Test internal priority calculation logic
        # High urgency + high impact = high priority (1)
        priority_high = builder._calculate_priority(urgency=1, impact=1)
        assert priority_high == 1, f"Expected priority 1 but got {priority_high}"

        # Low urgency + low impact = low priority (4 or 5)
        priority_low = builder._calculate_priority(urgency=3, impact=3)
        assert priority_low in [3, 4, 5], f"Expected priority 3-5 but got {priority_low}"

    def test_default_values(self, settings: Settings):
        """Test default values from settings."""
        builder = IncidentBuilder(settings)

        incident = builder.build_from_email(
            email_from="test@example.com",
            email_subject="Test",
            email_body="Test body",
        )

        assert incident["assignment_group"] == settings.servicenow_assignment_group
        assert incident["category"] == settings.servicenow_category
