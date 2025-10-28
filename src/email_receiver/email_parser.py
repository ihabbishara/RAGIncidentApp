"""Email parsing module."""

import email
from email import policy
from email.message import EmailMessage
from typing import Dict, Any
import re

from loguru import logger


class EmailParser:
    """Parse email messages and extract relevant information."""

    @staticmethod
    def parse_email(raw_email: bytes) -> Dict[str, Any]:
        """
        Parse raw email data into structured format.

        Args:
            raw_email: Raw email bytes

        Returns:
            Dictionary with parsed email data
        """
        try:
            # Parse email
            msg = email.message_from_bytes(raw_email, policy=policy.default)

            # Extract headers
            email_from = EmailParser._extract_email_address(msg.get("From", ""))
            email_to = EmailParser._extract_email_address(msg.get("To", ""))
            subject = msg.get("Subject", "No Subject")
            date = msg.get("Date", "")
            message_id = msg.get("Message-ID", "")

            # Extract body
            body = EmailParser._extract_body(msg)

            parsed_data = {
                "from": email_from,
                "to": email_to,
                "subject": subject,
                "body": body,
                "date": date,
                "message_id": message_id,
                "raw_headers": dict(msg.items()),
            }

            logger.info(f"Parsed email from {email_from}: {subject}")
            return parsed_data

        except Exception as e:
            logger.error(f"Error parsing email: {e}")
            raise

    @staticmethod
    def _extract_email_address(header: str) -> str:
        """
        Extract email address from header field.

        Args:
            header: Email header (e.g., "John Doe <john@example.com>")

        Returns:
            Email address only
        """
        if not header:
            return ""

        # Try to extract email from angle brackets
        match = re.search(r"<([^>]+)>", header)
        if match:
            return match.group(1).strip().lower()

        # If no angle brackets, assume entire string is email
        return header.strip().lower()

    @staticmethod
    def _extract_body(msg: EmailMessage) -> str:
        """
        Extract email body (preferring plain text).

        Args:
            msg: Email message object

        Returns:
            Email body text
        """
        body = ""

        try:
            # Try to get plain text first
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition", ""))

                    # Skip attachments
                    if "attachment" in content_disposition:
                        continue

                    if content_type == "text/plain":
                        try:
                            body = part.get_payload(decode=True).decode()
                            break
                        except Exception as e:
                            logger.warning(f"Could not decode text/plain part: {e}")
                            continue

                # If no plain text found, try HTML
                if not body:
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        if content_type == "text/html":
                            try:
                                html_body = part.get_payload(decode=True).decode()
                                # Strip HTML tags (simple approach)
                                body = EmailParser._strip_html(html_body)
                                break
                            except Exception as e:
                                logger.warning(f"Could not decode text/html part: {e}")
                                continue
            else:
                # Not multipart, get payload directly
                body = msg.get_payload(decode=True).decode()

        except Exception as e:
            logger.error(f"Error extracting email body: {e}")
            body = ""

        return body.strip()

    @staticmethod
    def _strip_html(html: str) -> str:
        """
        Strip HTML tags from text.

        Args:
            html: HTML content

        Returns:
            Plain text
        """
        # Remove HTML tags
        text = re.sub(r"<[^>]+>", " ", html)

        # Decode HTML entities
        text = text.replace("&nbsp;", " ")
        text = text.replace("&amp;", "&")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&quot;", '"')

        # Remove multiple spaces
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    @staticmethod
    def extract_incident_info(parsed_email: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract incident-related information from parsed email.

        Args:
            parsed_email: Parsed email data

        Returns:
            Incident information
        """
        subject = parsed_email.get("subject", "")
        body = parsed_email.get("body", "")

        # Combine subject and body for full context
        full_content = f"{subject}\n\n{body}"

        return {
            "sender": parsed_email.get("from", ""),
            "subject": subject,
            "content": full_content,
            "body": body,
            "timestamp": parsed_email.get("date", ""),
        }
