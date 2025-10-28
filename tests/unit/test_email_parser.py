"""Unit tests for Email Parser."""

import pytest
from email.message import EmailMessage
from src.email_receiver.email_parser import EmailParser


class TestEmailParser:
    """Test EmailParser class."""

    def test_parse_simple_email(self):
        """Test parsing simple text email."""
        # Create email message
        msg = EmailMessage()
        msg["From"] = "test@example.com"
        msg["To"] = "support@example.com"
        msg["Subject"] = "Test Subject"
        msg.set_content("Test email body content.")

        parser = EmailParser()
        parsed = parser.parse_email(msg.as_bytes())

        assert parsed["from"] == "test@example.com"
        assert parsed["subject"] == "Test Subject"
        assert "Test email body content" in parsed["body"]

    def test_parse_multipart_email(self):
        """Test parsing multipart email."""
        msg = EmailMessage()
        msg["From"] = "sender@example.com"
        msg["To"] = "recipient@example.com"
        msg["Subject"] = "Multipart Test"
        msg.set_content("Plain text body.")
        msg.add_alternative("<html><body><p>HTML body</p></body></html>", subtype="html")

        parser = EmailParser()
        parsed = parser.parse_email(msg.as_bytes())

        assert parsed["from"] == "sender@example.com"
        assert "Plain text body" in parsed["body"]

    def test_extract_from_address(self):
        """Test extracting from address."""
        msg = EmailMessage()
        msg["From"] = "John Doe <john@example.com>"
        msg["Subject"] = "Test"
        msg.set_content("Body")

        parser = EmailParser()
        parsed = parser.parse_email(msg.as_bytes())

        assert parsed["from"] == "john@example.com"

    def test_clean_body(self):
        """Test body cleaning."""
        parser = EmailParser()

        # Test with HTML content
        html_body = "<html><body><p>Line 1</p><br/><br/><p>Line 2</p></body></html>"
        cleaned = parser._strip_html(html_body)

        assert "<html>" not in cleaned
        assert "<p>" not in cleaned
        assert "Line 1" in cleaned
        assert "Line 2" in cleaned

    def test_parse_with_missing_fields(self):
        """Test parsing email with missing fields."""
        msg = EmailMessage()
        msg.set_content("Just a body, no headers.")

        parser = EmailParser()
        parsed = parser.parse_email(msg.as_bytes())

        # Should have default/empty values
        assert "from" in parsed
        assert "subject" in parsed
        assert "body" in parsed

    def test_parse_empty_email(self):
        """Test parsing empty email."""
        parser = EmailParser()

        # Empty email should parse successfully with empty values
        parsed = parser.parse_email(b"")

        assert "from" in parsed
        assert "subject" in parsed
        assert "body" in parsed
