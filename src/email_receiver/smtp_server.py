"""SMTP server for receiving incident emails."""

import asyncio
from typing import Callable, Awaitable
from aiosmtpd.controller import Controller
from aiosmtpd.smtp import SMTP as SMTPProtocol, Session, Envelope

from loguru import logger

from src.config import Settings
from src.email_receiver.email_parser import EmailParser
from src.email_receiver.trigger_validator import TriggerValidator


class SMTPHandler:
    """Handle incoming SMTP messages."""

    def __init__(
        self,
        settings: Settings,
        email_callback: Callable[[dict], Awaitable[None]],
    ):
        """
        Initialize SMTP handler.

        Args:
            settings: Application settings
            email_callback: Async callback function for processing emails
        """
        self.settings = settings
        self.email_callback = email_callback
        self.parser = EmailParser()
        self.validator = TriggerValidator(settings)

        logger.info("Initialized SMTP handler")

    async def handle_DATA(
        self, server: SMTPProtocol, session: Session, envelope: Envelope
    ) -> str:
        """
        Handle incoming email data.

        Args:
            server: SMTP server instance
            session: SMTP session
            envelope: Email envelope

        Returns:
            SMTP response code
        """
        try:
            logger.info(
                f"Received email from {envelope.mail_from} to {envelope.rcpt_tos}"
            )

            # Parse email
            parsed_email = self.parser.parse_email(envelope.content)

            # Validate if email should trigger workflow
            if self.validator.should_process_email(parsed_email):
                logger.info(f"Processing email from {parsed_email['from']}")

                # Call the callback function asynchronously
                asyncio.create_task(self.email_callback(parsed_email))

                return "250 Message accepted for delivery"
            else:
                reason = self.validator.get_rejection_reason(parsed_email)
                logger.info(f"Email rejected: {reason}")
                return "250 Message accepted but not processed (validation failed)"

        except Exception as e:
            logger.error(f"Error handling email: {e}")
            return "451 Requested action aborted: local error in processing"


class SMTPServer:
    """SMTP server for receiving emails."""

    def __init__(
        self,
        settings: Settings,
        email_callback: Callable[[dict], Awaitable[None]],
    ):
        """
        Initialize SMTP server.

        Args:
            settings: Application settings
            email_callback: Async callback for processing emails
        """
        self.settings = settings
        self.host = settings.smtp_host
        self.port = settings.smtp_port

        # Create handler
        self.handler = SMTPHandler(settings, email_callback)

        # Create controller
        self.controller = Controller(
            self.handler,
            hostname=self.host,
            port=self.port,
        )

        logger.info(f"SMTP server configured on {self.host}:{self.port}")

    def start(self) -> None:
        """Start the SMTP server."""
        try:
            self.controller.start()
            logger.info(f"SMTP server started on {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Failed to start SMTP server: {e}")
            raise

    def stop(self) -> None:
        """Stop the SMTP server."""
        try:
            self.controller.stop()
            logger.info("SMTP server stopped")
        except Exception as e:
            logger.error(f"Error stopping SMTP server: {e}")
