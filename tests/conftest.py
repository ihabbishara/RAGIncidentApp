"""Pytest configuration and fixtures."""

import asyncio
import pytest
from typing import AsyncGenerator, Generator

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Settings, get_settings


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def settings() -> Settings:
    """Get application settings."""
    return get_settings()


@pytest.fixture
def sample_email_data() -> dict:
    """Sample email data for testing."""
    return {
        "from": "xyz@test.com",
        "subject": "Database connection timeout issues",
        "body": """We are experiencing severe database connection timeout issues.

Symptoms:
- Applications timing out when connecting to database
- Connection pool exhaustion warnings
- HTTP 504 Gateway Timeout responses
- Issues occurring during peak hours (9 AM - 11 AM EST)

This is affecting multiple services and causing user complaints.
""",
    }


@pytest.fixture
def sample_confluence_docs() -> list:
    """Sample Confluence documents for testing."""
    return [
        {
            "id": "page_001",
            "title": "Database Connection Troubleshooting",
            "content": """
# Database Connection Troubleshooting

## Common Issues

### Connection Timeouts
Connection timeouts often occur due to:
1. Network latency
2. Database server overload
3. Misconfigured connection pools

### Solutions
- Increase connection pool size
- Add connection retry logic
- Monitor database performance metrics
            """,
            "space": "TECH",
            "url": "https://confluence.example.com/display/TECH/db-troubleshooting",
            "labels": ["database", "troubleshooting"],
        },
        {
            "id": "page_002",
            "title": "Connection Pool Best Practices",
            "content": """
# Connection Pool Best Practices

## Configuration Guidelines
- Minimum pool size: 5
- Maximum pool size: 20
- Connection timeout: 30 seconds
- Idle timeout: 10 minutes

## Monitoring
Monitor these key metrics:
- Active connections
- Pool utilization
- Wait time
            """,
            "space": "TECH",
            "url": "https://confluence.example.com/display/TECH/connection-pools",
            "labels": ["database", "best-practices"],
        },
    ]


@pytest.fixture
def sample_llm_output() -> dict:
    """Sample LLM output for testing."""
    return {
        "summary": "Database connection timeout issue affecting multiple services",
        "description": "Experiencing database connection timeouts causing HTTP 504 errors during peak hours",
        "priority": "2",
        "urgency": "2",
        "impact": "2",
        "category": "Database",
        "resolution_notes": """Based on knowledge base articles:
1. Check connection pool configuration
2. Monitor database server load
3. Implement connection retry logic
4. Review connection timeout settings
""",
    }


@pytest.fixture
def sample_incident_data() -> dict:
    """Sample ServiceNow incident data for testing."""
    return {
        "short_description": "Database connection timeout issues",
        "description": "Experiencing database connection timeouts causing HTTP 504 errors",
        "urgency": "2",
        "impact": "2",
        "priority": "2",
        "category": "Database",
        "caller_id": "xyz@test.com",
        "assignment_group": "IT Support",
        "work_notes": "Knowledge base articles consulted for resolution",
    }
