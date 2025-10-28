# RAG Incident Management System

**Automated incident creation using RAG (Retrieval-Augmented Generation), email triggers, and ServiceNow integration.**

## 🎯 Overview

This system automatically creates ServiceNow incidents from incoming emails by:
1. Receiving emails via SMTP server
2. Searching a knowledge base (Confluence) using RAG
3. Generating incident summaries with LLM (Ollama)
4. Creating incidents in ServiceNow with relevant context

## 🏗️ Architecture

```
┌─────────────┐     ┌──────────────┐     ┌───────────────┐
│   Email     │────▶│     SMTP     │────▶│   Workflow    │
│  (Trigger)  │     │    Server    │     │ Orchestrator  │
└─────────────┘     └──────────────┘     └───────┬───────┘
                                                  │
                    ┌─────────────────────────────┼─────────────────────────┐
                    │                             │                         │
                    ▼                             ▼                         ▼
            ┌──────────────┐            ┌─────────────────┐      ┌────────────────┐
            │     RAG      │            │       LLM       │      │   ServiceNow   │
            │  Retrieval   │            │    (Ollama)     │      │     Client     │
            └──────┬───────┘            └─────────────────┘      └────────────────┘
                   │
                   ▼
            ┌──────────────┐
            │  Vector DB   │
            │  (ChromaDB)  │
            └──────────────┘
```

## ✨ Features

- **📧 Email Trigger**: SMTP server receives and validates emails
- **🔍 RAG Search**: Searches Confluence knowledge base for relevant articles
- **🤖 LLM Generation**: Uses Ollama (Mistral 7B) to generate incident summaries
- **🎫 Auto-Ticketing**: Creates ServiceNow incidents automatically
- **📊 Monitoring**: Health checks and metrics endpoints
- **🧪 Mock Services**: Built-in mocks for testing without external dependencies
- **📈 Observability**: Structured logging with Loguru

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- ~8GB disk space (for Ollama model)

### Option 1: Docker Compose (Recommended)

```bash
# 1. Clone and navigate to project
cd DemoRAG

# 2. Copy environment configuration
cp .env.example .env

# 3. Start all services
docker-compose up -d

# 4. Pull Ollama model (first time only, ~10 minutes)
docker exec rag-ollama ollama pull mistral:7b-instruct

# 5. Create test data
docker exec rag-incident-app python scripts/create_test_data.py

# 6. Verify system health
curl http://localhost:8000/health
```

### Option 2: Local Development

```bash
# 1. Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy environment configuration
cp .env.example .env
# Edit .env for local URLs (localhost instead of service names)

# 4. Start external services (Ollama, mocks)
docker-compose up -d ollama confluence-mock servicenow-mock maildev

# 5. Run application
python src/main.py

# 6. In another terminal, create test data
python scripts/create_test_data.py
```

## 📝 Usage

### Send Test Email

```bash
# Using test script
python scripts/test_email.py

# Or manually via SMTP
# Send email to localhost:1025
```

### API Endpoints

```bash
# Health check
curl http://localhost:8000/health

# System stats
curl http://localhost:8000/stats

# Test email processing (without SMTP)
curl -X POST http://localhost:8000/api/test-email \
  -H "Content-Type: application/json" \
  -d '{
    "from": "xyz@test.com",
    "subject": "Database timeout issues",
    "body": "We are experiencing connection timeouts..."
  }'
```

### Check Created Incidents

```bash
# View all incidents in mock ServiceNow
curl http://localhost:8002/api/now/table/incident

# View specific incident
curl http://localhost:8002/api/now/table/incident/{sys_id}
```

### Monitor Email (MailDev UI)

Open http://localhost:1080 in your browser to see email capture interface.

## 🧪 Testing

### Run All Tests

```bash
# Using Docker
docker exec rag-incident-app pytest

# Using local environment
source .venv/bin/activate
pytest

# With coverage
pytest --cov=src --cov-report=html

# Specific test categories
pytest tests/unit/          # Unit tests only
pytest tests/integration/   # Integration tests only
pytest tests/e2e/           # End-to-end tests only
```

### Run Quality Checks

```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type checking
mypy src/
```

## 📂 Project Structure

```
DemoRAG/
├── src/
│   ├── config/              # Configuration and settings
│   ├── ingestion/           # Confluence client, document processing, embeddings
│   ├── rag/                 # Vector store, retriever, LLM generator
│   ├── servicenow/          # ServiceNow client and incident builder
│   ├── email_receiver/      # SMTP server and email parsing
│   ├── orchestrator/        # Main workflow orchestration
│   ├── mocks/               # Mock services for testing
│   └── main.py              # FastAPI application entry point
├── scripts/
│   ├── ingest_confluence.py    # Ingest Confluence documents
│   ├── test_email.py           # Send test emails
│   └── create_test_data.py     # Create sample test data
├── tests/
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   └── e2e/                 # End-to-end tests
├── data/
│   ├── chromadb/            # Vector database storage
│   └── ollama/              # Ollama model storage
├── docker-compose.yml       # Service orchestration
├── Dockerfile               # Main application image
├── Dockerfile.mock          # Mock services image
├── requirements.txt         # Python dependencies
├── pyproject.toml           # Project metadata and tool configuration
└── .env                     # Environment variables (copy from .env.example)
```

## ⚙️ Configuration

### Environment Variables

Key configuration in `.env`:

```bash
# Application
ENVIRONMENT=development
APP_HOST=0.0.0.0
APP_PORT=8000

# Confluence
CONFLUENCE_URL=http://confluence-mock:8001
CONFLUENCE_USERNAME=admin
CONFLUENCE_API_TOKEN=your_token
CONFLUENCE_SPACE_KEYS=TECH,SUPPORT,OPS
CONFLUENCE_LABELS=incident,troubleshooting,knowledgebase

# SMTP
SMTP_HOST=0.0.0.0
SMTP_PORT=1025
SMTP_ALLOWED_SENDERS=xyz@test.com,admin@test.com

# ServiceNow
SERVICENOW_URL=http://servicenow-mock:8002
SERVICENOW_USERNAME=admin
SERVICENOW_PASSWORD=your_password

# LLM (Ollama)
LLM_PROVIDER=ollama
LLM_MODEL=mistral:7b-instruct
LLM_BASE_URL=http://ollama:11434
LLM_TEMPERATURE=0.3

# Vector Database
VECTORDB_TYPE=chromadb
VECTORDB_PATH=/data/chromadb
VECTORDB_COLLECTION_NAME=confluence_docs

# Embeddings
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DEVICE=cpu

# RAG
RAG_CHUNK_SIZE=800
RAG_CHUNK_OVERLAP=200
RAG_TOP_K_RESULTS=5
RAG_SIMILARITY_THRESHOLD=0.7
```

### Customization

- **Add Ollama Models**: Use different models by changing `LLM_MODEL`
- **Adjust Chunk Size**: Modify `RAG_CHUNK_SIZE` for different document granularity
- **Change Embeddings**: Use different embedding models via `EMBEDDING_MODEL`
- **Customize Incident Fields**: Modify `src/servicenow/incident_builder.py`

## 🐳 Docker Services

| Service | Port | Purpose |
|---------|------|---------|
| **app** | 8000 | Main FastAPI application |
| **ollama** | 11434 | LLM inference server |
| **confluence-mock** | 8001 | Mock Confluence API |
| **servicenow-mock** | 8002 | Mock ServiceNow API |
| **maildev** | 1080 (UI), 1025 (SMTP) | Email testing interface |

### Service Management

```bash
# View logs
docker-compose logs -f app
docker-compose logs -f ollama

# Restart services
docker-compose restart app

# Stop all services
docker-compose down

# Remove volumes (clean state)
docker-compose down -v

# Rebuild images
docker-compose build --no-cache
```

## 🔍 Troubleshooting

### Common Issues

**1. Ollama model not found**
```bash
# Pull the model
docker exec rag-ollama ollama pull mistral:7b-instruct

# List available models
docker exec rag-ollama ollama list
```

**2. Empty vector database**
```bash
# Ingest test data
docker exec rag-incident-app python scripts/create_test_data.py

# Or ingest from Confluence
docker exec rag-incident-app python scripts/ingest_confluence.py
```

**3. LLM health check fails**
```bash
# Check Ollama status
curl http://localhost:11434/api/tags

# View Ollama logs
docker logs rag-ollama
```

**4. Dependency conflicts (sentence-transformers)**
```bash
# If you see huggingface_hub import errors
pip install --upgrade sentence-transformers
```

**5. Application won't start**
```bash
# Check logs
docker-compose logs app

# Verify all containers are running
docker-compose ps

# Check port conflicts
lsof -i :8000
```

### Debug Mode

Enable detailed logging:

```bash
# In .env
LOG_LEVEL=DEBUG

# Restart
docker-compose restart app
```

## 📊 Monitoring & Observability

### Health Checks

```bash
# Overall system health
curl http://localhost:8000/health

# Response format:
{
  "overall": "healthy",
  "components": {
    "llm": "healthy",
    "servicenow": "healthy",
    "vector_store": {
      "status": "healthy",
      "document_count": 42
    }
  }
}
```

### Metrics

```bash
# System statistics
curl http://localhost:8000/stats

# Response format:
{
  "vector_store": {
    "document_count": 42,
    "collection_name": "confluence_docs"
  }
}
```

### Logs

Logs are structured with Loguru and include:
- Timestamps
- Log levels (INFO, WARNING, ERROR)
- Component names
- Contextual information

```bash
# View live logs
docker-compose logs -f app

# Search logs
docker-compose logs app | grep "ERROR"

# Export logs
docker-compose logs app > application.log
```

## 🚀 Production Deployment

### Security Considerations

1. **Change default credentials** in `.env`
2. **Use HTTPS** for all external endpoints
3. **Restrict SMTP allowed senders** to trusted domains
4. **Enable authentication** for ServiceNow API
5. **Use secrets management** (e.g., AWS Secrets Manager, HashiCorp Vault)
6. **Network isolation** via Docker networks or VPC
7. **Regular security updates** for dependencies

### Performance Tuning

```bash
# Adjust worker processes (in Dockerfile)
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# Increase embedding batch size (in .env)
EMBEDDING_BATCH_SIZE=64

# Optimize ChromaDB (in .env)
VECTORDB_PERSIST=true
```

### Scaling

- **Horizontal**: Run multiple app instances behind load balancer
- **Vertical**: Increase container resources (CPU, memory)
- **Database**: Use persistent volume for ChromaDB or switch to production vector DB
- **LLM**: Use GPU-enabled Ollama or external LLM API
- **Caching**: Add Redis for frequently accessed data

## 🤝 Contributing

### Development Workflow

1. **Create branch**: `git checkout -b feature/your-feature`
2. **Make changes**: Follow coding standards
3. **Run tests**: `pytest`
4. **Format code**: `black src/ tests/`
5. **Lint**: `ruff check src/ tests/`
6. **Commit**: Use conventional commits
7. **Push**: `git push origin feature/your-feature`
8. **PR**: Create pull request with description

### Code Standards

- **Python**: PEP 8, type hints, docstrings
- **Testing**: Minimum 80% coverage
- **Documentation**: Update README for user-facing changes
- **Commits**: Conventional commits format

## 📄 License

This project is provided as-is for demonstration purposes.

## 🙏 Acknowledgments

- **Langchain**: LLM and RAG framework
- **ChromaDB**: Vector database
- **Ollama**: Local LLM inference
- **FastAPI**: Modern Python web framework
- **Sentence Transformers**: Embedding models

## 📚 Resources

- [Langchain Documentation](https://python.langchain.com/)
- [Ollama](https://ollama.ai/)
- [ChromaDB](https://www.trychroma.com/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [ServiceNow API](https://developer.servicenow.com/)

## 🆘 Support

For issues and questions:
1. Check [Troubleshooting](#troubleshooting) section
2. Review [logs](#logs)
3. Search existing GitHub issues
4. Create new issue with details

---

**Built with ❤️ for automated incident management**
