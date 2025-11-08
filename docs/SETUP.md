# AION Setup Guide

Complete guide to set up and run AION - AI Personal Assistant with Long-Term Memory.

## Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose
- Poetry (Python dependency manager)
- Git

## Quick Start

### 1. Clone and Setup Environment

```bash
# Clone the repository (if not already done)
cd AION

# Install Poetry if you haven't already
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

### 2. Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
nano .env  # or use your preferred editor
```

**Required Configuration:**

```env
# OpenRouter API (Required)
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Neo4j (Required)
NEO4J_PASSWORD=your_secure_password_here

# PostgreSQL (Required)
POSTGRES_PASSWORD=your_postgres_password_here

# GitHub (Required for Obsidian sync)
GITHUB_TOKEN=your_github_token_here
GITHUB_REPO_OWNER=your_username
GITHUB_REPO_NAME=your_obsidian_vault_repo

# Security (Required - change in production)
SECRET_KEY=your-secret-key-change-this-in-production
ENCRYPTION_KEY=your-encryption-key-change-this
```

### 3. Start Infrastructure Services

```bash
# Start all services (Qdrant, Neo4j, PostgreSQL)
docker-compose up -d

# Verify services are running
docker-compose ps
```

You should see:
- `aion_qdrant` on port 6333
- `aion_neo4j` on ports 7474 (HTTP) and 7687 (Bolt)
- `aion_postgres` on port 5432

### 4. Initialize Databases

```bash
# Run initialization script
poetry run python scripts/init_db.py
```

This will:
- Create PostgreSQL tables for conversations
- Initialize Qdrant collections (memories, kb_documents)
- Set up Neo4j constraints and indexes

### 5. Start the Application

```bash
# Development mode (with auto-reload)
poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Or using the main script
poetry run python -m src.main
```

The API will be available at `http://localhost:8000`

### 6. Verify Installation

```bash
# Check health endpoint
curl http://localhost:8000/api/v1/health

# Check API documentation
open http://localhost:8000/docs
```

## Access Service UIs

- **API Documentation**: http://localhost:8000/docs
- **Neo4j Browser**: http://localhost:7474 (username: `neo4j`, password: from .env)
- **Qdrant Dashboard**: http://localhost:6333/dashboard

## Development Workflow

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src --cov-report=html

# Run specific test file
poetry run pytest tests/unit/test_memory.py

# Open coverage report
open htmlcov/index.html
```

### Code Quality

```bash
# Format code with Black
poetry run black src tests

# Lint with Ruff
poetry run ruff check src tests

# Type check with mypy
poetry run mypy src

# Run all quality checks
poetry run black src tests && poetry run ruff check src tests && poetry run mypy src
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks
poetry run pre-commit install

# Run hooks manually
poetry run pre-commit run --all-files
```

## Docker Deployment

### Build and Run with Docker Compose

```bash
# Build and start all services including API
docker-compose up --build -d

# View logs
docker-compose logs -f api

# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes all data)
docker-compose down -v
```

## Troubleshooting

### Port Conflicts

If ports are already in use:

```bash
# Check what's using a port
lsof -i :8000  # For API
lsof -i :6333  # For Qdrant
lsof -i :7687  # For Neo4j
lsof -i :5432  # For PostgreSQL

# Change ports in docker-compose.yml or .env
```

### Database Connection Issues

```bash
# Restart services
docker-compose restart

# Check service logs
docker-compose logs qdrant
docker-compose logs neo4j
docker-compose logs postgres

# Verify connectivity
docker-compose exec postgres psql -U aion_user -d aion_metadata -c "SELECT 1;"
```

### OpenRouter API Issues

- Verify your API key is valid: https://openrouter.ai/keys
- Check your OpenRouter balance
- Review logs for specific error messages

### Clear All Data

```bash
# WARNING: This deletes all data
docker-compose down -v
rm -rf qdrant_storage neo4j_data neo4j_logs postgres_data

# Reinitialize
docker-compose up -d
poetry run python scripts/init_db.py
```

## Environment Variables Reference

See `.env.example` for complete list of configuration options.

### Critical Settings

- **OPENROUTER_API_KEY**: Required for LLM and embeddings
- **OPENROUTER_EMBEDDING_MODEL**: Default: `openai/text-embedding-3-small`
- **OPENROUTER_LLM_MODEL**: Default: `anthropic/claude-3.5-sonnet`
- **QDRANT_VECTOR_SIZE**: Must match embedding model (default: 1536)

### Memory Settings

- **MEMORY_MAX_LENGTH**: Max characters per memory (default: 150)
- **MEMORY_RETRIEVAL_LIMIT**: Memories retrieved per query (default: 5)
- **DOCUMENT_RETRIEVAL_LIMIT**: Documents retrieved per query (default: 10)

### Sync Settings

- **AUTO_SYNC_ENABLED**: Enable automatic Obsidian sync (default: true)
- **SYNC_INTERVAL_HOURS**: Hours between syncs (default: 1)
- **CHUNK_SIZE**: Document chunk size in tokens (default: 500)
- **CHUNK_OVERLAP**: Chunk overlap in tokens (default: 50)

## Next Steps

1. **Set up GitHub sync**: Configure your Obsidian vault repository
2. **Test the API**: Use the interactive docs at `/docs`
3. **Create your first memory**: POST to `/api/v1/memories`
4. **Start chatting**: POST to `/api/v1/chat`

## Getting Help

- Check the main [README.md](../README.md) for architecture overview
- Review API documentation at `/docs` when running
- Check logs in `logs/aion.log`

## Security Notes

**Before deploying to production:**

1. Change all default passwords in `.env`
2. Generate strong `SECRET_KEY` and `ENCRYPTION_KEY`
3. Disable debug mode (`DEBUG=false`)
4. Set `ENVIRONMENT=production`
5. Disable API docs in production (automatic)
6. Set up proper CORS origins
7. Enable HTTPS/TLS
8. Use environment-specific `.env` files
9. Never commit `.env` to git
