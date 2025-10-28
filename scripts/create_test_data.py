#!/usr/bin/env python3
"""
Create test data for mock services and populate vector database.

This script creates sample Confluence pages in the mock service
and ingests them into the vector database.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger

from src.config import get_settings
from src.ingestion.document_processor import DocumentProcessor
from src.ingestion.embedder import Embedder
from src.rag.vector_store import VectorStore


SAMPLE_DOCUMENTS = [
    {
        "id": "page_001",
        "title": "Database Connection Troubleshooting",
        "content": """
# Database Connection Troubleshooting

## Overview
This guide helps troubleshoot common database connection issues in our infrastructure.

## Common Issues

### Connection Timeouts
Connection timeouts often occur due to:
1. **Network latency**: High latency between application and database servers
2. **Database server overload**: Too many concurrent connections or queries
3. **Misconfigured connection pools**: Insufficient pool size or timeout settings
4. **Firewall rules**: Blocking database ports or limiting connections

### Connection Pool Exhaustion
When the application can't get new connections from the pool:
- Check current pool utilization metrics
- Review pool configuration (min, max, timeout)
- Look for connection leaks (connections not properly released)
- Monitor long-running queries that hold connections

## Solutions

### Immediate Actions
1. **Increase connection pool size**: Temporary relief for high load
2. **Add connection retry logic**: Implement exponential backoff
3. **Monitor database performance**: Check CPU, memory, disk I/O
4. **Review slow queries**: Use query analyzer to identify bottlenecks

### Long-term Fixes
- Implement connection pooling best practices
- Set up database read replicas for read-heavy workloads
- Use caching to reduce database load
- Implement circuit breakers for graceful degradation

## Monitoring
Key metrics to watch:
- Active connections count
- Connection pool utilization percentage
- Average query execution time
- Database server CPU and memory usage
- Connection wait time

## Related Articles
- Connection Pool Best Practices
- Database Performance Optimization
- Monitoring and Alerting Setup
        """,
        "space": "TECH",
        "url": "https://confluence.example.com/display/TECH/db-troubleshooting",
        "labels": ["database", "troubleshooting", "performance"],
    },
    {
        "id": "page_002",
        "title": "Connection Pool Best Practices",
        "content": """
# Connection Pool Best Practices

## Configuration Guidelines

### Pool Sizing
- **Minimum pool size**: 5 connections
  - Ensures availability during startup
  - Prevents cold start delays
- **Maximum pool size**: 20 connections
  - Based on database server capacity
  - Consider: (core_count * 2) + effective_spindle_count
- **Connection timeout**: 30 seconds
  - Prevents indefinite waits
  - Alert if timeouts are frequent
- **Idle timeout**: 10 minutes
  - Releases unused connections
  - Helps with resource cleanup

### Validation
- **Test on borrow**: Validate connection before use
- **Test while idle**: Check idle connections periodically
- **Validation query**: Use lightweight query (e.g., SELECT 1)
- **Validation timeout**: 5 seconds max

## Implementation Patterns

### Java (HikariCP)
```java
HikariConfig config = new HikariConfig();
config.setJdbcUrl("jdbc:postgresql://localhost/db");
config.setMinimumIdle(5);
config.setMaximumPoolSize(20);
config.setConnectionTimeout(30000);
config.setIdleTimeout(600000);
HikariDataSource ds = new HikariDataSource(config);
```

### Python (psycopg2)
```python
from psycopg2 import pool
connection_pool = pool.SimpleConnectionPool(
    minconn=5,
    maxconn=20,
    host="localhost",
    database="db",
    user="user",
    password="pass"
)
```

## Monitoring
Monitor these key metrics:
- **Active connections**: Current in-use connections
- **Idle connections**: Available in pool
- **Pool utilization**: (active / max) * 100
- **Wait time**: Time spent waiting for connection
- **Timeout count**: Number of connection timeouts

## Common Pitfalls
1. **Pool too small**: Causes connection waits and timeouts
2. **Pool too large**: Wastes resources, overloads database
3. **No validation**: Uses broken connections, causes errors
4. **Missing timeouts**: Can cause indefinite hangs
5. **Connection leaks**: Forgotten close() calls exhaust pool

## Troubleshooting
If experiencing pool issues:
1. Check pool metrics in monitoring dashboard
2. Review application logs for connection errors
3. Verify database server has capacity
4. Look for connection leaks in code
5. Consider increasing pool size temporarily
6. Review and optimize slow queries

## Best Practices Checklist
- ✅ Set appropriate min/max pool sizes
- ✅ Configure reasonable timeouts
- ✅ Enable connection validation
- ✅ Implement proper connection closing (try-with-resources)
- ✅ Monitor pool metrics continuously
- ✅ Set up alerts for high utilization
- ✅ Document pool configuration decisions
        """,
        "space": "TECH",
        "url": "https://confluence.example.com/display/TECH/connection-pools",
        "labels": ["database", "best-practices", "connection-pool"],
    },
    {
        "id": "page_003",
        "title": "HTTP 504 Gateway Timeout Troubleshooting",
        "content": """
# HTTP 504 Gateway Timeout Troubleshooting

## What is a 504 Error?
A 504 Gateway Timeout error occurs when a gateway or proxy server doesn't receive a timely response from an upstream server.

## Common Causes

### Application Layer
1. **Slow database queries**: Queries taking longer than timeout
2. **External API calls**: Third-party services responding slowly
3. **Resource exhaustion**: CPU, memory, or thread pool saturation
4. **Deadlocks**: Database or application-level deadlocks

### Infrastructure Layer
1. **Load balancer timeout**: Default timeout too short
2. **Network issues**: Packet loss or high latency
3. **Server overload**: Too many concurrent requests
4. **DNS resolution**: Slow or failing DNS lookups

## Diagnosis Steps

### 1. Check Application Logs
```bash
# Look for slow query logs
grep "Query took" /var/log/app/application.log

# Check for timeout errors
grep -i "timeout" /var/log/app/error.log

# Review recent exceptions
tail -1000 /var/log/app/exceptions.log | grep "504"
```

### 2. Monitor Database
- Check active query count
- Review slow query log
- Look for lock waits
- Examine connection pool utilization

### 3. Review Load Balancer
- Check backend server health
- Review timeout configuration
- Monitor request queue depth
- Verify SSL handshake times

### 4. Application Metrics
- Response time percentiles (p50, p95, p99)
- Thread pool utilization
- Memory usage
- CPU usage

## Solutions

### Quick Fixes
1. **Increase timeout**: Adjust load balancer/proxy timeout
2. **Restart affected services**: Clear hung processes
3. **Scale horizontally**: Add more application instances
4. **Enable caching**: Reduce database load

### Long-term Solutions
1. **Optimize slow queries**: Add indexes, rewrite queries
2. **Implement timeouts**: Set reasonable timeouts for all external calls
3. **Add circuit breakers**: Prevent cascade failures
4. **Use async processing**: Move slow operations to background jobs
5. **Implement rate limiting**: Protect from overload

## Prevention

### Application Best Practices
- Set explicit timeouts for all external calls
- Implement proper connection pooling
- Use database query optimization
- Add comprehensive monitoring and alerting

### Infrastructure Best Practices
- Configure appropriate load balancer timeouts
- Set up auto-scaling policies
- Implement health checks
- Use CDN for static content

## Monitoring Setup
Create alerts for:
- 504 error rate > 1%
- Average response time > 3 seconds
- P95 response time > 5 seconds
- Database connection pool > 80%
- Thread pool utilization > 90%

## Related Documentation
- Database Connection Troubleshooting
- Load Balancer Configuration
- Application Performance Monitoring
- Incident Response Playbook
        """,
        "space": "OPS",
        "url": "https://confluence.example.com/display/OPS/504-troubleshooting",
        "labels": ["http", "troubleshooting", "gateway", "timeout"],
    },
    {
        "id": "page_004",
        "title": "Production Incident Response Playbook",
        "content": """
# Production Incident Response Playbook

## Incident Severity Levels

### Severity 1 (Critical)
- Complete service outage
- Data loss or corruption
- Security breach
- **Response Time**: Immediate
- **Update Frequency**: Every 30 minutes

### Severity 2 (High)
- Partial service degradation
- Performance issues affecting majority of users
- Workaround available but not ideal
- **Response Time**: Within 15 minutes
- **Update Frequency**: Every hour

### Severity 3 (Medium)
- Minor feature not working
- Small percentage of users affected
- Acceptable workaround exists
- **Response Time**: Within 1 hour
- **Update Frequency**: Daily

## Response Workflow

### 1. Detection and Alert
- Monitor alert channels (PagerDuty, Slack)
- Acknowledge incident within SLA
- Create incident ticket in ServiceNow
- Notify on-call engineer

### 2. Initial Assessment
- Determine severity level
- Identify affected services/users
- Check monitoring dashboards
- Review recent deployments
- Gather relevant logs

### 3. Communication
- Post initial update in #incidents channel
- Notify stakeholders based on severity
- Update status page if customer-facing
- Set up war room if Severity 1/2

### 4. Investigation
- Review application logs
- Check database performance
- Examine infrastructure metrics
- Verify external dependencies
- Look for recent changes

### 5. Mitigation
- Implement immediate fix if known
- Consider rollback if recent deployment
- Scale resources if capacity issue
- Enable circuit breakers if dependency issue
- Apply workaround if fix not immediately available

### 6. Resolution
- Verify fix resolves issue
- Monitor for recurrence
- Update incident ticket
- Notify stakeholders of resolution
- Update status page

### 7. Post-Incident
- Schedule post-mortem within 48 hours
- Document timeline and actions taken
- Identify root cause
- Create action items for prevention
- Update runbooks and playbooks

## Common Scenarios

### Database Issues
1. Check connection pool utilization
2. Review slow query log
3. Verify database server health
4. Consider read replica failover
5. Scale database if needed

### Application Crashes
1. Review application logs
2. Check memory usage
3. Verify thread pool status
4. Restart affected instances
5. Scale if capacity issue

### External API Failures
1. Check API status page
2. Enable circuit breaker
3. Use cached data if available
4. Notify users of degraded functionality
5. Contact vendor if prolonged

## Communication Templates

### Initial Update
```
[INCIDENT] Severity X: <Brief Description>
Status: Investigating
Impact: <User/Service Impact>
Started: <Time>
ETA: <Estimated Resolution Time>
Next Update: <Time>
```

### Resolution
```
[RESOLVED] Severity X: <Brief Description>
Status: Resolved
Resolution: <What was done>
Duration: <Total Time>
Root Cause: <Brief explanation>
Post-Mortem: <Link when available>
```

## On-Call Responsibilities
- Respond to pages within 5 minutes
- Provide status updates per schedule
- Escalate if cannot resolve within 1 hour
- Document all actions taken
- Hand off cleanly if shift changes during incident

## Useful Commands

### Check application status
```bash
kubectl get pods -n production
docker ps | grep app
systemctl status application
```

### View logs
```bash
kubectl logs -f pod-name -n production
docker logs --tail=100 -f container-id
tail -f /var/log/application/error.log
```

### Database queries
```sql
-- Active connections
SELECT count(*) FROM pg_stat_activity;

-- Slow queries
SELECT pid, query, query_start
FROM pg_stat_activity
WHERE state = 'active'
AND query_start < now() - interval '1 minute';
```

## Escalation Path
1. On-call engineer (first responder)
2. Engineering lead
3. Engineering manager
4. VP of Engineering
5. CTO (Severity 1 only)

## Resources
- Monitoring Dashboard: https://grafana.example.com
- Status Page: https://status.example.com
- Runbooks: https://wiki.example.com/runbooks
- Post-Mortems: https://wiki.example.com/post-mortems
        """,
        "space": "OPS",
        "url": "https://confluence.example.com/display/OPS/incident-response",
        "labels": ["incident", "playbook", "operations", "oncall"],
    },
]


def main():
    """Main function to create test data."""
    logger.info("=" * 80)
    logger.info("Creating Test Data")
    logger.info("=" * 80)

    try:
        # Initialize settings
        settings = get_settings()

        # Initialize components
        logger.info("\n[1/4] Initializing components...")
        document_processor = DocumentProcessor(settings)
        embedder = Embedder(settings)
        vector_store = VectorStore(settings)
        logger.info("✅ Components initialized")

        # Process documents
        logger.info("\n[2/4] Processing documents...")
        logger.info(f"  - Documents: {len(SAMPLE_DOCUMENTS)}")
        chunks = document_processor.process_documents(SAMPLE_DOCUMENTS)
        logger.info(f"✅ Created {len(chunks)} chunks")

        # Generate embeddings
        logger.info("\n[3/4] Generating embeddings...")
        texts = [document_processor.create_metadata_text(chunk) for chunk in chunks]
        embeddings = embedder.embed_batch(texts)
        logger.info(f"✅ Generated {len(embeddings)} embeddings")

        # Store in vector database
        logger.info("\n[4/4] Storing in vector database...")
        ids = [chunk["chunk_id"] for chunk in chunks]
        documents_content = [chunk["content"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]

        vector_store.add_documents(
            documents=documents_content,
            metadatas=metadatas,
            ids=ids,
            embeddings=embeddings,
        )

        total_docs = vector_store.count()
        logger.info(f"✅ Vector database now contains {total_docs} documents")

        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("Test Data Creation Complete!")
        logger.info("=" * 80)
        logger.info(f"📄 Sample documents: {len(SAMPLE_DOCUMENTS)}")
        logger.info(f"📦 Chunks created: {len(chunks)}")
        logger.info(f"💾 Total in database: {total_docs}")
        logger.info("=" * 80)

        logger.info("\nYou can now test the system:")
        logger.info("  1. Send test email: python scripts/test_email.py")
        logger.info("  2. Check API: curl http://localhost:8000/health")
        logger.info("  3. View incidents: curl http://localhost:8002/api/now/table/incident")

    except Exception as e:
        logger.error(f"\n❌ Failed to create test data: {e}")
        logger.exception("Full error details:")
        sys.exit(1)


if __name__ == "__main__":
    main()
