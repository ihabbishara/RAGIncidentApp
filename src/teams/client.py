"""Microsoft Teams client for sending incident notifications."""

from typing import Dict, Any, List, Optional
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from loguru import logger

from src.config import Settings


class TeamsClient:
    """Microsoft Teams webhook client."""

    def __init__(self, settings: Settings):
        """
        Initialize Teams client.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.webhook_url = settings.teams_webhook_url
        self.enabled = settings.teams_enabled

        if not self.enabled:
            logger.info("Microsoft Teams notifications are disabled")
        elif not self.webhook_url or self.webhook_url == "https://your-webhook-url-here":
            logger.warning("Microsoft Teams webhook URL not configured")
            self.enabled = False
        else:
            logger.info("Microsoft Teams client initialized")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
    )
    async def send_incident_notification(
        self,
        incident_data: Dict[str, Any],
        llm_summary: Optional[Dict[str, Any]] = None,
        kb_sources: Optional[List[Dict[str, Any]]] = None,
    ) -> bool:
        """
        Send incident notification to Teams channel using Adaptive Cards.

        Args:
            incident_data: ServiceNow incident data
            llm_summary: LLM-generated summary (optional)
            kb_sources: Knowledge base sources (optional)

        Returns:
            True if notification sent successfully, False otherwise
        """
        if not self.enabled:
            logger.debug("Teams notifications disabled, skipping")
            return False

        try:
            # Build Adaptive Card
            card = self._build_adaptive_card(incident_data, llm_summary, kb_sources)

            # Send to Teams
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.webhook_url,
                    json=card,
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()

            logger.info(
                f"Successfully sent Teams notification for incident {incident_data.get('number', 'Unknown')}"
            )
            return True

        except httpx.HTTPStatusError as e:
            logger.error(f"Teams API error: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Teams request error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error sending Teams notification: {e}")
            return False

    def _build_adaptive_card(
        self,
        incident_data: Dict[str, Any],
        llm_summary: Optional[Dict[str, Any]] = None,
        kb_sources: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Build Adaptive Card for Teams notification.

        Args:
            incident_data: ServiceNow incident data
            llm_summary: LLM-generated summary
            kb_sources: Knowledge base sources

        Returns:
            Adaptive Card JSON
        """
        incident_number = incident_data.get("number", "Unknown")
        short_description = incident_data.get("short_description", "No description")
        priority = incident_data.get("priority", 3)
        urgency = incident_data.get("urgency", 3)
        impact = incident_data.get("impact", 3)
        caller_id = incident_data.get("caller_id", "Unknown")
        category = incident_data.get("category", "Incident")

        # Determine priority color
        priority_color = self._get_priority_color(priority)

        # Build facts section
        facts = [
            {"title": "Incident Number", "value": incident_number},
            {"title": "Priority", "value": f"P{priority}"},
            {"title": "Urgency", "value": str(urgency)},
            {"title": "Impact", "value": str(impact)},
            {"title": "Category", "value": category},
            {"title": "Caller", "value": caller_id},
        ]

        # Build card body
        card_body = [
            {
                "type": "TextBlock",
                "text": f"🚨 New Incident: {incident_number}",
                "weight": "Bolder",
                "size": "Large",
                "color": priority_color,
            },
            {
                "type": "TextBlock",
                "text": short_description,
                "wrap": True,
                "size": "Medium",
                "spacing": "Medium",
            },
            {
                "type": "FactSet",
                "facts": facts,
                "spacing": "Medium",
            },
        ]

        # Add LLM-generated insights if available
        if llm_summary:
            description = llm_summary.get("description", "")
            recommended_actions = llm_summary.get("recommended_actions", [])
            kb_references = llm_summary.get("kb_references", [])

            if description:
                card_body.append({
                    "type": "TextBlock",
                    "text": "**Analysis:**",
                    "weight": "Bolder",
                    "spacing": "Medium",
                })
                card_body.append({
                    "type": "TextBlock",
                    "text": description,
                    "wrap": True,
                    "isSubtle": True,
                })

            if recommended_actions:
                card_body.append({
                    "type": "TextBlock",
                    "text": "**Recommended Actions:**",
                    "weight": "Bolder",
                    "spacing": "Medium",
                })
                actions_text = "\n".join([f"• {action}" for action in recommended_actions])
                card_body.append({
                    "type": "TextBlock",
                    "text": actions_text,
                    "wrap": True,
                })

            if kb_references:
                card_body.append({
                    "type": "TextBlock",
                    "text": "**Knowledge Base References:**",
                    "weight": "Bolder",
                    "spacing": "Medium",
                })
                kb_text = "\n".join([f"• {ref}" for ref in kb_references])
                card_body.append({
                    "type": "TextBlock",
                    "text": kb_text,
                    "wrap": True,
                    "isSubtle": True,
                })

        # Add KB sources if available
        if kb_sources and len(kb_sources) > 0:
            card_body.append({
                "type": "TextBlock",
                "text": f"📚 {len(kb_sources)} relevant KB articles found",
                "weight": "Bolder",
                "spacing": "Medium",
            })
            for source in kb_sources[:3]:  # Show top 3 sources
                score = source.get("score", 0)
                url = source.get("url", "")
                card_body.append({
                    "type": "TextBlock",
                    "text": f"• [{url}]({url}) (Score: {score:.2f})",
                    "wrap": True,
                    "isSubtle": True,
                })

        # Build complete Adaptive Card
        adaptive_card = {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "contentUrl": None,
                    "content": {
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "type": "AdaptiveCard",
                        "version": "1.4",
                        "body": card_body,
                        "msteams": {
                            "width": "Full"
                        }
                    }
                }
            ]
        }

        return adaptive_card

    def _get_priority_color(self, priority: int) -> str:
        """
        Get color based on priority level.

        Args:
            priority: Priority level (1-5)

        Returns:
            Color name for Adaptive Card
        """
        if priority == 1:
            return "Attention"  # Red
        elif priority == 2:
            return "Warning"    # Orange
        elif priority == 3:
            return "Accent"     # Blue
        else:
            return "Default"    # Gray

    async def check_health(self) -> bool:
        """
        Check Teams webhook health.

        Returns:
            True if webhook is accessible, False otherwise
        """
        if not self.enabled:
            return True  # Not enabled, so not unhealthy

        try:
            # Test webhook with minimal payload
            test_card = {
                "type": "message",
                "text": "Health check from RAG Incident System"
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.webhook_url,
                    json=test_card,
                    headers={"Content-Type": "application/json"},
                )
                response.raise_for_status()

            logger.debug("Teams webhook health check passed")
            return True

        except Exception as e:
            logger.error(f"Teams webhook health check failed: {e}")
            return False
