"""Mock Confluence API server for testing."""

from typing import List, Dict, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse


# Sample Confluence pages with incident-related content
MOCK_PAGES = [
    {
        "id": "12345",
        "type": "page",
        "status": "current",
        "title": "Database Connection Timeout Issues",
        "space": {"key": "TECH", "name": "Technical Documentation"},
        "version": {"number": 5, "when": "2024-01-15T10:30:00Z"},
        "metadata": {
            "labels": {
                "results": [
                    {"name": "incident"},
                    {"name": "database"},
                    {"name": "troubleshooting"},
                ]
            }
        },
        "body": {
            "storage": {
                "value": """
                    <h2>Database Connection Timeout Issues</h2>
                    <p><strong>Problem:</strong> Applications experiencing database connection timeouts,
                    especially during peak hours (9 AM - 11 AM EST).</p>

                    <h3>Symptoms:</h3>
                    <ul>
                        <li>Connection timeout errors in application logs</li>
                        <li>Slow query performance</li>
                        <li>Connection pool exhaustion warnings</li>
                        <li>HTTP 504 Gateway Timeout responses</li>
                    </ul>

                    <h3>Root Cause:</h3>
                    <p>Insufficient database connection pool size combined with long-running queries
                    that hold connections.</p>

                    <h3>Resolution Steps:</h3>
                    <ol>
                        <li>Increase connection pool max_connections from 100 to 200</li>
                        <li>Set connection timeout to 30 seconds</li>
                        <li>Enable connection pool monitoring</li>
                        <li>Optimize slow queries identified in pg_stat_statements</li>
                        <li>Implement connection pooling at application level using PgBouncer</li>
                    </ol>

                    <h3>Prevention:</h3>
                    <ul>
                        <li>Regular query performance reviews</li>
                        <li>Connection pool size monitoring and alerting</li>
                        <li>Implement circuit breakers for database connections</li>
                    </ul>
                """,
                "representation": "storage",
            }
        },
    },
    {
        "id": "12346",
        "type": "page",
        "status": "current",
        "title": "API Rate Limiting 429 Errors",
        "space": {"key": "SUPPORT", "name": "Support Documentation"},
        "version": {"number": 3, "when": "2024-01-18T14:20:00Z"},
        "metadata": {
            "labels": {
                "results": [
                    {"name": "incident"},
                    {"name": "api"},
                    {"name": "rate-limiting"},
                ]
            }
        },
        "body": {
            "storage": {
                "value": """
                    <h2>API Rate Limiting 429 Errors</h2>
                    <p><strong>Problem:</strong> External API integration receiving HTTP 429
                    (Too Many Requests) errors, causing data sync failures.</p>

                    <h3>Symptoms:</h3>
                    <ul>
                        <li>HTTP 429 errors in integration logs</li>
                        <li>Retry-After headers indicating rate limit exceeded</li>
                        <li>Data synchronization delays</li>
                        <li>User complaints about stale data</li>
                    </ul>

                    <h3>Root Cause:</h3>
                    <p>Application not respecting API rate limits and not implementing
                    exponential backoff retry strategy.</p>

                    <h3>Resolution Steps:</h3>
                    <ol>
                        <li>Implement token bucket algorithm for rate limiting</li>
                        <li>Add exponential backoff with jitter for retries</li>
                        <li>Respect Retry-After headers from API responses</li>
                        <li>Implement request queuing to smooth out burst traffic</li>
                        <li>Add monitoring for rate limit consumption</li>
                    </ol>

                    <h3>Code Example:</h3>
                    <code>
                    from tenacity import retry, wait_exponential, stop_after_attempt

                    @retry(wait=wait_exponential(multiplier=1, min=4, max=60),
                           stop=stop_after_attempt(5))
                    def make_api_call():
                        response = requests.get(url, headers=headers)
                        if response.status_code == 429:
                            retry_after = int(response.headers.get('Retry-After', 60))
                            time.sleep(retry_after)
                            raise Exception("Rate limited")
                        return response
                    </code>
                """,
                "representation": "storage",
            }
        },
    },
    {
        "id": "12347",
        "type": "page",
        "status": "current",
        "title": "Memory Leak in Python Service",
        "space": {"key": "TECH", "name": "Technical Documentation"},
        "version": {"number": 7, "when": "2024-01-20T09:15:00Z"},
        "metadata": {
            "labels": {
                "results": [
                    {"name": "incident"},
                    {"name": "memory-leak"},
                    {"name": "python"},
                ]
            }
        },
        "body": {
            "storage": {
                "value": """
                    <h2>Memory Leak in Python Service</h2>
                    <p><strong>Problem:</strong> Python microservice memory usage grows continuously,
                    eventually causing OOM (Out of Memory) errors and service crashes.</p>

                    <h3>Symptoms:</h3>
                    <ul>
                        <li>Steadily increasing memory usage over time</li>
                        <li>OOMKilled events in Kubernetes</li>
                        <li>Frequent pod restarts</li>
                        <li>Performance degradation before crashes</li>
                    </ul>

                    <h3>Root Cause:</h3>
                    <p>Circular references in cache objects preventing garbage collection,
                    combined with unbounded cache growth.</p>

                    <h3>Resolution Steps:</h3>
                    <ol>
                        <li>Use memory_profiler to identify leak source</li>
                        <li>Implement LRU cache with size limits using functools.lru_cache</li>
                        <li>Break circular references using weakref</li>
                        <li>Add periodic cache cleanup tasks</li>
                        <li>Set memory limits in Kubernetes with appropriate reserves</li>
                        <li>Enable memory monitoring and alerting</li>
                    </ol>

                    <h3>Diagnostic Commands:</h3>
                    <code>
                    # Profile memory usage
                    python -m memory_profiler your_script.py

                    # Check for circular references
                    import gc
                    gc.collect()
                    print(gc.garbage)
                    </code>

                    <h3>Prevention:</h3>
                    <ul>
                        <li>Always set maximum sizes for caches</li>
                        <li>Use weak references for circular dependencies</li>
                        <li>Regular memory profiling in CI/CD</li>
                        <li>Implement health checks that monitor memory usage</li>
                    </ul>
                """,
                "representation": "storage",
            }
        },
    },
    {
        "id": "12348",
        "type": "page",
        "status": "current",
        "title": "SSL Certificate Expiration",
        "space": {"key": "OPS", "name": "Operations"},
        "version": {"number": 2, "when": "2024-01-22T16:45:00Z"},
        "metadata": {
            "labels": {
                "results": [
                    {"name": "incident"},
                    {"name": "ssl"},
                    {"name": "certificate"},
                ]
            }
        },
        "body": {
            "storage": {
                "value": """
                    <h2>SSL Certificate Expiration</h2>
                    <p><strong>Problem:</strong> SSL certificate expired causing all HTTPS
                    traffic to fail with certificate validation errors.</p>

                    <h3>Symptoms:</h3>
                    <ul>
                        <li>Browser warning "Your connection is not private"</li>
                        <li>NET::ERR_CERT_DATE_INVALID errors</li>
                        <li>API clients failing with SSL verification errors</li>
                        <li>Complete service outage for web traffic</li>
                    </ul>

                    <h3>Root Cause:</h3>
                    <p>Lack of automated certificate renewal and monitoring, combined with
                    expired certificate notification emails going to unmonitored inbox.</p>

                    <h3>Immediate Resolution:</h3>
                    <ol>
                        <li>Generate new SSL certificate immediately</li>
                        <li>Update certificate on load balancer/web server</li>
                        <li>Restart web server/reload configuration</li>
                        <li>Verify certificate installation with SSL checker tools</li>
                        <li>Clear browser caches if needed</li>
                    </ol>

                    <h3>Long-term Prevention:</h3>
                    <ol>
                        <li>Implement Let's Encrypt with auto-renewal using certbot</li>
                        <li>Set up certificate expiration monitoring (30, 14, 7 days before)</li>
                        <li>Create alerts to monitored channels (Slack, PagerDuty)</li>
                        <li>Document certificate renewal process</li>
                        <li>Set calendar reminders as backup</li>
                    </ol>

                    <h3>Commands:</h3>
                    <code>
                    # Check certificate expiration
                    openssl s_client -connect domain.com:443 | openssl x509 -noout -dates

                    # Auto-renew with certbot
                    certbot renew --dry-run
                    </code>
                """,
                "representation": "storage",
            }
        },
    },
    {
        "id": "12349",
        "type": "page",
        "status": "current",
        "title": "Disk Space Full on Production Server",
        "space": {"key": "OPS", "name": "Operations"},
        "version": {"number": 4, "when": "2024-01-25T11:30:00Z"},
        "metadata": {
            "labels": {
                "results": [
                    {"name": "incident"},
                    {"name": "disk-space"},
                    {"name": "infrastructure"},
                ]
            }
        },
        "body": {
            "storage": {
                "value": """
                    <h2>Disk Space Full on Production Server</h2>
                    <p><strong>Problem:</strong> Production server disk usage at 100%, causing
                    application failures and preventing log writes.</p>

                    <h3>Symptoms:</h3>
                    <ul>
                        <li>"No space left on device" errors</li>
                        <li>Application unable to write files</li>
                        <li>Database transaction failures</li>
                        <li>Log rotation failures</li>
                        <li>Deployment failures</li>
                    </ul>

                    <h3>Root Cause:</h3>
                    <p>Log files growing without rotation, combined with temp files not being
                    cleaned up and lack of disk usage monitoring.</p>

                    <h3>Immediate Resolution:</h3>
                    <ol>
                        <li>Identify largest directories: <code>du -sh /* | sort -h</code></li>
                        <li>Clean up old log files: <code>find /var/log -name "*.log" -mtime +30 -delete</code></li>
                        <li>Clear temp files: <code>rm -rf /tmp/*</code></li>
                        <li>Clean package manager cache: <code>apt-get clean</code> or <code>yum clean all</code></li>
                        <li>Remove old Docker images: <code>docker system prune -a</code></li>
                    </ol>

                    <h3>Long-term Prevention:</h3>
                    <ol>
                        <li>Implement log rotation with logrotate</li>
                        <li>Set up disk usage monitoring (alert at 80%, critical at 90%)</li>
                        <li>Implement automated cleanup scripts for temp files</li>
                        <li>Use centralized logging (ELK, Splunk) to reduce local storage</li>
                        <li>Regularly review and clean up unused files</li>
                        <li>Increase disk size if growth is legitimate</li>
                    </ol>

                    <h3>Monitoring Script:</h3>
                    <code>
                    #!/bin/bash
                    THRESHOLD=80
                    USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
                    if [ $USAGE -gt $THRESHOLD ]; then
                        echo "Disk usage is above $THRESHOLD%: $USAGE%"
                        # Send alert
                    fi
                    </code>
                """,
                "representation": "storage",
            }
        },
    },
]


app = FastAPI(title="Mock Confluence API", version="1.0.0")


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "confluence-mock"}


@app.get("/rest/api/content")
async def get_content(
    spaceKey: str = Query(None, description="Space key filter"),
    label: str = Query(None, description="Label filter"),
    start: int = Query(0, description="Pagination start"),
    limit: int = Query(25, description="Pagination limit"),
) -> Dict[str, Any]:
    """
    Get Confluence content with optional filtering.

    Mimics Confluence REST API /rest/api/content endpoint.
    """
    filtered_pages = MOCK_PAGES.copy()

    # Filter by space key
    if spaceKey:
        filtered_pages = [
            p for p in filtered_pages if p["space"]["key"] == spaceKey
        ]

    # Filter by label
    if label:
        filtered_pages = [
            p
            for p in filtered_pages
            if any(
                lbl["name"] == label
                for lbl in p["metadata"]["labels"]["results"]
            )
        ]

    # Pagination
    total = len(filtered_pages)
    paginated_pages = filtered_pages[start : start + limit]

    return {
        "results": paginated_pages,
        "start": start,
        "limit": limit,
        "size": len(paginated_pages),
        "_links": {
            "base": "http://confluence-mock:8001",
            "context": "",
            "self": f"/rest/api/content?start={start}&limit={limit}",
        },
    }


@app.get("/rest/api/content/{content_id}")
async def get_content_by_id(content_id: str) -> Dict[str, Any]:
    """Get specific Confluence page by ID."""
    for page in MOCK_PAGES:
        if page["id"] == content_id:
            return page

    raise HTTPException(status_code=404, detail=f"Page with ID {content_id} not found")


@app.get("/rest/api/content/search")
async def search_content(
    cql: str = Query(..., description="Confluence Query Language"),
    start: int = Query(0, description="Pagination start"),
    limit: int = Query(25, description="Pagination limit"),
) -> Dict[str, Any]:
    """
    Search content using CQL.

    Simplified implementation that just returns all pages for any query.
    """
    # In a real implementation, this would parse CQL
    # For mock, just return filtered results based on simple text matching
    filtered_pages = MOCK_PAGES.copy()

    # Simple text search in title and body
    if "text" in cql.lower():
        search_term = cql.split("~")[1].strip('"').lower() if "~" in cql else ""
        if search_term:
            filtered_pages = [
                p
                for p in filtered_pages
                if search_term in p["title"].lower()
                or search_term in p["body"]["storage"]["value"].lower()
            ]

    total = len(filtered_pages)
    paginated_pages = filtered_pages[start : start + limit]

    return {
        "results": paginated_pages,
        "start": start,
        "limit": limit,
        "size": len(paginated_pages),
        "totalSize": total,
        "cqlQuery": cql,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
