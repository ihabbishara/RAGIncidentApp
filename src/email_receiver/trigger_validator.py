"""Email trigger validation module."""

from typing import Dict, Any, List

from loguru import logger

from src.config import Settings


class TriggerValidator:
    """Validate if an email should trigger workflow."""

    def __init__(self, settings: Settings):
        """
        Initialize trigger validator.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.allowed_senders = settings.smtp_allowed_senders_list

        logger.info(f"Initialized TriggerValidator with {len(self.allowed_senders)} allowed senders")

    def should_process_email(self, parsed_email: Dict[str, Any]) -> bool:
        """
        Check if email should be processed.

        Args:
            parsed_email: Parsed email data

        Returns:
            True if email should be processed, False otherwise
        """
        email_from = parsed_email.get("from", "").lower()

        if not email_from:
            logger.warning("Email has no sender, rejecting")
            return False

        # Check if sender is in allowed list
        if email_from not in self.allowed_senders:
            logger.info(f"Email from {email_from} not in allowed senders list, rejecting")
            return False

        # Check if email has content
        body = parsed_email.get("body", "")
        if not body or len(body.strip()) < 10:
            logger.warning(f"Email from {email_from} has insufficient content, rejecting")
            return False

        logger.info(f"Email from {email_from} passed validation")
        return True

    def get_rejection_reason(self, parsed_email: Dict[str, Any]) -> str:
        """
        Get reason why email was rejected.

        Args:
            parsed_email: Parsed email data

        Returns:
            Rejection reason message
        """
        email_from = parsed_email.get("from", "").lower()

        if not email_from:
            return "No sender address found"

        if email_from not in self.allowed_senders:
            return f"Sender {email_from} not in allowed list: {self.allowed_senders}"

        body = parsed_email.get("body", "")
        if not body or len(body.strip()) < 10:
            return "Email body is empty or too short"

        return "Unknown rejection reason"
