"""Incident data builder for ServiceNow."""

from typing import Dict, Any
from datetime import datetime

from loguru import logger

from src.config import Settings


class IncidentBuilder:
    """Build ServiceNow incident payloads."""

    def __init__(self, settings: Settings):
        """
        Initialize incident builder.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.default_assignment_group = settings.servicenow_assignment_group
        self.default_category = settings.servicenow_category
        self.default_urgency = settings.servicenow_urgency
        self.default_impact = settings.servicenow_impact

        logger.info("Initialized IncidentBuilder")

    def build_from_llm_output(
        self,
        llm_output: Dict[str, Any],
        email_from: str,
        email_subject: str,
    ) -> Dict[str, Any]:
        """
        Build ServiceNow incident from LLM output.

        Args:
            llm_output: LLM-generated incident data
            email_from: Email sender address
            email_subject: Email subject

        Returns:
            ServiceNow incident payload
        """
        logger.info("Building incident from LLM output")

        # Extract data from LLM output with fallbacks
        short_description = llm_output.get(
            "short_description",
            email_subject or "Incident from automated email processing",
        )

        description = llm_output.get("description", "")

        # Add metadata to description
        metadata_parts = [
            f"Original Email From: {email_from}",
            f"Email Subject: {email_subject}",
            f"Processed At: {datetime.utcnow().isoformat()}Z",
        ]

        # Add KB references if available
        kb_references = llm_output.get("kb_references", [])
        if kb_references:
            kb_text = "\n".join(f"- {ref}" for ref in kb_references)
            metadata_parts.append(f"\nKnowledge Base References:\n{kb_text}")

        # Add recommended actions if available
        recommended_actions = llm_output.get("recommended_actions", [])
        if recommended_actions:
            actions_text = "\n".join(f"- {action}" for action in recommended_actions)
            metadata_parts.append(f"\nRecommended Actions:\n{actions_text}")

        # Combine description with metadata
        full_description = f"{description}\n\n---\n\n" + "\n".join(metadata_parts)

        # Get urgency and impact with validation
        urgency = self._validate_priority_value(
            llm_output.get("urgency", self.default_urgency)
        )
        impact = self._validate_priority_value(
            llm_output.get("impact", self.default_impact)
        )

        # Calculate priority
        priority = self._calculate_priority(urgency, impact)

        # Build incident payload
        incident_data = {
            "short_description": short_description[:160],  # ServiceNow has 160 char limit
            "description": full_description,
            "assignment_group": self.default_assignment_group,
            "category": llm_output.get("category", self.default_category),
            "urgency": urgency,
            "impact": impact,
            "priority": priority,
            "caller_id": email_from,
            "contact_type": "email",
        }

        logger.debug(f"Built incident payload: {incident_data['short_description']}")
        return incident_data

    def build_from_email(
        self,
        email_from: str,
        email_subject: str,
        email_body: str,
        urgency: int | None = None,
        impact: int | None = None,
    ) -> Dict[str, Any]:
        """
        Build ServiceNow incident directly from email (fallback method).

        Args:
            email_from: Email sender
            email_subject: Email subject
            email_body: Email body
            urgency: Optional urgency level
            impact: Optional impact level

        Returns:
            ServiceNow incident payload
        """
        logger.info("Building incident directly from email")

        short_description = email_subject[:160] or "Incident from email"

        description = f"""Email Subject: {email_subject}
Email From: {email_from}
Received: {datetime.utcnow().isoformat()}Z

Email Content:
{email_body}

---
This incident was created automatically from an email trigger.
No matching knowledge base articles were found during automated processing."""

        urgency_val = self._validate_priority_value(urgency or self.default_urgency)
        impact_val = self._validate_priority_value(impact or self.default_impact)

        incident_data = {
            "short_description": short_description,
            "description": description,
            "assignment_group": self.default_assignment_group,
            "category": self.default_category,
            "urgency": urgency_val,
            "impact": impact_val,
            "priority": self._calculate_priority(urgency_val, impact_val),
            "caller_id": email_from,
            "contact_type": "email",
        }

        return incident_data

    def _validate_priority_value(self, value: Any) -> int:
        """
        Validate and normalize priority value (urgency/impact).

        Args:
            value: Input value

        Returns:
            Valid priority value (1-5)
        """
        try:
            val = int(value)
            if 1 <= val <= 5:
                return val
            else:
                logger.warning(f"Invalid priority value {val}, using default 3")
                return 3
        except (ValueError, TypeError):
            logger.warning(f"Could not parse priority value {value}, using default 3")
            return 3

    def _calculate_priority(self, urgency: int, impact: int) -> int:
        """
        Calculate priority based on urgency and impact.

        ServiceNow priority matrix:
        - Critical (1): Urgency 1-2, Impact 1-2
        - High (2): Urgency 1-3, Impact 1-3
        - Moderate (3): Urgency 2-4, Impact 2-4
        - Low (4): Urgency 3-5, Impact 3-5
        - Planning (5): Urgency 4-5, Impact 4-5

        Args:
            urgency: Urgency level (1-5)
            impact: Impact level (1-5)

        Returns:
            Priority level (1-5)
        """
        avg = (urgency + impact) / 2

        if avg <= 2:
            return 1  # Critical
        elif avg <= 2.5:
            return 2  # High
        elif avg <= 3.5:
            return 3  # Moderate
        elif avg <= 4.5:
            return 4  # Low
        else:
            return 5  # Planning

    def add_work_note(self, note: str) -> Dict[str, Any]:
        """
        Format a work note for adding to an incident.

        Args:
            note: Work note content

        Returns:
            Update payload with work note
        """
        timestamp = datetime.utcnow().isoformat() + "Z"
        formatted_note = f"[{timestamp}] {note}"

        return {"work_notes": formatted_note}

    def add_comment(self, comment: str) -> Dict[str, Any]:
        """
        Format a comment for adding to an incident.

        Args:
            comment: Comment content

        Returns:
            Update payload with comment
        """
        timestamp = datetime.utcnow().isoformat() + "Z"
        formatted_comment = f"[{timestamp}] {comment}"

        return {"comments": formatted_comment}
