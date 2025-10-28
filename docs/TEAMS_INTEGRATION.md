# Microsoft Teams Integration

This document explains how to configure and use the Microsoft Teams integration for incident notifications.

## Overview

The RAG Incident System can send rich, formatted notifications to Microsoft Teams channels when incidents are created. Notifications include:

- Incident details (number, priority, urgency, impact, category)
- LLM-generated analysis and description
- Recommended actions
- Knowledge base references
- Links to relevant KB articles with similarity scores

## Features

- **Adaptive Cards**: Beautiful, interactive cards with structured information
- **Priority-based Coloring**: Visual indication of incident severity
- **Automatic Notifications**: Sent immediately after incident creation
- **Graceful Fallback**: Won't fail incident creation if Teams notification fails
- **Health Monitoring**: Teams webhook health check included in system health endpoint

## Setup Instructions

### 1. Create a Teams Webhook

1. Open Microsoft Teams and navigate to the channel where you want to receive notifications
2. Click the **three dots** (⋯) next to the channel name
3. Select **Connectors** or **Workflows** > **Incoming Webhook**
4. Click **Add** or **Configure**
5. Provide a name for the webhook (e.g., "RAG Incident Notifications")
6. Optionally upload a custom image
7. Click **Create**
8. **Copy the webhook URL** - you'll need this for configuration

### 2. Configure the Application

Update your `.env` file with the Teams webhook URL:

```bash
# Microsoft Teams Configuration
TEAMS_WEBHOOK_URL=https://your-organization.webhook.office.com/webhookb2/...
TEAMS_ENABLED=true
```

### 3. Restart the Application

```bash
# If using Docker
docker-compose restart app

# Or restart the entire stack
docker-compose down && docker-compose up -d
```

### 4. Verify Configuration

Check the health endpoint to confirm Teams is enabled:

```bash
curl http://localhost:8000/health | python3 -m json.tool
```

You should see:
```json
{
    "overall": "healthy",
    "components": {
        "llm": "healthy",
        "servicenow": "healthy",
        "vector_store": {
            "status": "healthy",
            "document_count": 16
        },
        "teams": "healthy"
    }
}
```

## Testing

### Test with the API endpoint:

```bash
curl -X POST http://localhost:8000/api/test-email \
  -H "Content-Type: application/json" \
  -d '{
    "from": "test@example.com",
    "subject": "Database connection issues",
    "body": "We are experiencing database timeouts in production. Multiple users affected."
  }'
```

### Expected Result

You should receive a Teams notification with:

1. **Header**: Incident number with priority-based color
2. **Description**: LLM-generated incident summary
3. **Incident Details**: Priority, urgency, impact, category, caller
4. **Analysis**: Root cause analysis from LLM
5. **Recommended Actions**: Actionable steps to resolve
6. **KB References**: Relevant knowledge base articles with links

## Notification Format

### Adaptive Card Structure

```
┌─────────────────────────────────────────┐
│ 🚨 New Incident: INC0000001             │ <- Priority Color
├─────────────────────────────────────────┤
│ Database Connection Timeout Issues      │ <- Short Description
├─────────────────────────────────────────┤
│ Incident Number: INC0000001             │
│ Priority: P4                            │
│ Urgency: 3                              │
│ Impact: 5                               │
│ Category: Database Connectivity Issues  │
│ Caller: xyz@test.com                    │
├─────────────────────────────────────────┤
│ Analysis:                               │
│ Multiple users reporting HTTP 504...    │
├─────────────────────────────────────────┤
│ Recommended Actions:                    │
│ • Increase connection pool size         │
│ • Add connection retry logic            │
│ • Monitor database performance          │
├─────────────────────────────────────────┤
│ Knowledge Base References:              │
│ • Database Connection Troubleshooting   │
│ • HTTP 504 Gateway Timeout Guide        │
├─────────────────────────────────────────┤
│ 📚 3 relevant KB articles found         │
│ • [url] (Score: 0.85)                   │
│ • [url] (Score: 0.84)                   │
│ • [url] (Score: 0.84)                   │
└─────────────────────────────────────────┘
```

### Priority Colors

- **Priority 1 (Critical)**: Red (Attention)
- **Priority 2 (High)**: Orange (Warning)
- **Priority 3 (Medium)**: Blue (Accent)
- **Priority 4-5 (Low)**: Gray (Default)

## Configuration Options

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TEAMS_WEBHOOK_URL` | Yes | - | Microsoft Teams incoming webhook URL |
| `TEAMS_ENABLED` | No | `false` | Enable/disable Teams notifications |

### Disabling Teams Notifications

To disable Teams notifications without removing the webhook URL:

```bash
TEAMS_ENABLED=false
```

## Troubleshooting

### Teams shows "disabled" in health check

**Cause**: Either `TEAMS_ENABLED=false` or webhook URL not configured

**Solution**:
1. Check `.env` file has `TEAMS_ENABLED=true`
2. Verify `TEAMS_WEBHOOK_URL` is set to a valid webhook URL
3. Restart the application

### Teams shows "unhealthy" in health check

**Cause**: Cannot reach Teams webhook

**Solution**:
1. Verify webhook URL is correct
2. Check network connectivity
3. Ensure webhook hasn't been deleted in Teams
4. Check application logs for detailed error messages

### Notifications not appearing in Teams

**Cause**: Various possible issues

**Solution**:
1. Check application logs: `docker-compose logs app`
2. Verify webhook URL is correct
3. Test webhook manually using curl:
   ```bash
   curl -H "Content-Type: application/json" \
        -d '{"text":"Test message"}' \
        YOUR_WEBHOOK_URL
   ```
4. Check Teams channel permissions

### Incident created but Teams notification failed

**Expected Behavior**: This is by design. The system will:
1. Create the ServiceNow incident successfully
2. Log the Teams notification failure
3. Continue processing without failing the entire workflow

**Check logs**:
```bash
docker-compose logs app | grep -i teams
```

## Architecture

### Components

1. **TeamsClient** (`src/teams/client.py`)
   - Manages webhook communication
   - Builds Adaptive Card payloads
   - Handles retries and error recovery

2. **WorkflowOrchestrator** (`src/orchestrator/workflow.py`)
   - Integrates Teams notification into incident workflow
   - Sends notification after successful incident creation
   - Graceful error handling

3. **Configuration** (`src/config/settings.py`, `.env`)
   - Teams webhook URL configuration
   - Enable/disable flag

### Notification Flow

```
Email Received
    ↓
RAG Vector Search (KB Articles)
    ↓
LLM Analysis & Summary
    ↓
ServiceNow Incident Created
    ↓
Teams Notification Sent ← (Non-blocking)
    ↓
Return Success Response
```

## Security Considerations

1. **Webhook URL Protection**
   - Keep webhook URL secret
   - Don't commit to version control
   - Use environment variables

2. **Sensitive Information**
   - Review what information is sent to Teams
   - Ensure compliance with data policies
   - Consider redacting PII if necessary

3. **Network Security**
   - Webhook uses HTTPS
   - No authentication required (URL is the secret)
   - Consider IP whitelisting if available

## Advanced Configuration

### Custom Adaptive Card Templates

You can customize the Adaptive Card format by modifying `_build_adaptive_card()` in `src/teams/client.py`.

Adaptive Card documentation: https://adaptivecards.io/

### Retry Configuration

Teams notifications use the same retry configuration as other services:

```bash
RETRY_MAX_ATTEMPTS=3
RETRY_WAIT_EXPONENTIAL_MULTIPLIER=1
RETRY_WAIT_EXPONENTIAL_MAX=10
```

## Support

For issues or questions:
1. Check application logs: `docker-compose logs app`
2. Review health endpoint: `http://localhost:8000/health`
3. Consult Microsoft Teams webhook documentation
4. Open an issue in the project repository
