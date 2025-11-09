# AION - AI Personal Assistant with Long-Term Memory

AION is an intelligent personal assistant that maintains long-term memory across conversations, integrates with your Obsidian knowledge base, and provides contextually rich responses through semantic understanding.

## Features

- **Long-Term Memory**: Remembers key facts, preferences, and conversations across sessions
- **Obsidian Integration**: Seamlessly syncs and searches your Obsidian vault from GitHub
- **Calendar & Email Integration**: Connect Google and Microsoft accounts for contextual assistance
  - **Google**: Access Calendar events and Gmail messages
  - **Microsoft**: Access Outlook Calendar and Email
  - **Secure OAuth 2.0**: Encrypted token storage with automatic refresh
- **Semantic Search**: RAG pipeline for intelligent context retrieval
- **Entity Relationships**: Knowledge graph using Neo4j for advanced reasoning
- **Function Calling / Tool Use**: LLM can use external tools for enhanced capabilities
  - **Web Search**: Search the internet using DuckDuckGo
  - **Code Executor**: Run Python code in a sandboxed environment
  - **Calculator**: Perform complex mathematical calculations
  - **Knowledge Base Search**: Query memories and documents
- **Manual Tool Control**: Force specific tools or disable them entirely
- **Multi-Agent Architecture**: Specialized agents for memory, retrieval, and synchronization
- **Privacy-First**: All data encrypted at rest, complete user control

## Architecture

AION follows Clean Architecture principles with clear separation of concerns:

```
src/
├── domain/           # Business entities and rules
├── application/      # Use cases and business logic
├── infrastructure/   # External services (Qdrant, Neo4j, OpenRouter)
├── presentation/     # API layer (FastAPI)
└── shared/          # Common utilities
```

### Tech Stack

- **Backend**: FastAPI + Python
- **Vector Store**: Qdrant
- **Graph Database**: Neo4j
- **Relational DB**: PostgreSQL
- **LLM Provider**: OpenRouter (Claude 3.5 Sonnet)
- **Embeddings**: OpenRouter (configurable models)
- **Function Calling**: Native OpenRouter API integration
- **Web Search**: DuckDuckGo (no API key required)

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Poetry (for dependency management)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd AION
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

3. **Start services with Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Install dependencies (for local development)**
   ```bash
   poetry install
   poetry shell
   ```

5. **Run database migrations**
   ```bash
   poetry run python scripts/init_db.py
   ```

6. **Start the development server**
   ```bash
   poetry run uvicorn src.main:app --reload
   ```

The API will be available at `http://localhost:8000`

## Configuration

### Required Environment Variables

- `OPENROUTER_API_KEY`: Your OpenRouter API key
- `GITHUB_TOKEN`: GitHub personal access token for Obsidian sync
- `NEO4J_PASSWORD`: Neo4j database password
- `POSTGRES_PASSWORD`: PostgreSQL password

### Optional Environment Variables (for OAuth Integrations)

- `GOOGLE_CLIENT_ID`: Google OAuth client ID
- `GOOGLE_CLIENT_SECRET`: Google OAuth client secret
- `MICROSOFT_CLIENT_ID`: Microsoft OAuth client ID
- `MICROSOFT_CLIENT_SECRET`: Microsoft OAuth client secret
- `OAUTH_ENCRYPTION_KEY`: Fernet encryption key for token storage

See `.env.example` for complete configuration options.

**Note**: For detailed OAuth setup instructions, see [docs/OAUTH_SETUP.md](docs/OAUTH_SETUP.md).

## Project Structure

```
AION/
├── src/
│   ├── config/              # Application configuration
│   ├── domain/              # Business entities and interfaces
│   │   ├── entities/        # Memory, Document, Conversation, Tool
│   │   ├── repositories/    # Repository interfaces
│   │   └── services/        # Domain services
│   ├── application/         # Use cases
│   │   ├── use_cases/       # Business logic
│   │   └── dtos/            # Data transfer objects
│   ├── infrastructure/      # External integrations
│   │   ├── vector_store/    # Qdrant implementation
│   │   ├── graph_db/        # Neo4j implementation
│   │   ├── llm/             # OpenRouter LLM client
│   │   ├── embeddings/      # Embedding service
│   │   ├── tools/           # Function calling tools
│   │   │   ├── calculator_tool.py
│   │   │   ├── web_search_tool.py
│   │   │   ├── code_executor_tool.py
│   │   │   └── knowledge_base_tool.py
│   │   └── github_sync/     # Obsidian vault sync
│   ├── presentation/        # API layer
│   │   ├── api/             # FastAPI routes
│   │   └── schemas/         # Pydantic schemas
│   └── shared/              # Utilities and helpers
├── tests/                   # Test suite
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── docs/                    # Documentation
├── scripts/                 # Utility scripts
└── docker-compose.yml       # Service orchestration
```

## Development

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src --cov-report=html

# Run specific test file
poetry run pytest tests/unit/test_memory.py
```

### Code Quality

```bash
# Format code
poetry run black src tests

# Lint code
poetry run ruff check src tests

# Type checking
poetry run mypy src
```

### Pre-commit Hooks

```bash
poetry run pre-commit install
poetry run pre-commit run --all-files
```

## API Documentation

Once the server is running, visit:

- **Interactive API docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Key Endpoints

### Chat & Memory
- `POST /api/v1/chat` - Send message to assistant
- `GET /api/v1/memories` - Retrieve stored memories
- `POST /api/v1/memories` - Create new memory
- `DELETE /api/v1/memories/{id}` - Delete specific memory

### Obsidian Sync
- `POST /api/v1/obsidian/sync` - Trigger Obsidian vault sync
- `GET /api/v1/obsidian/status` - Get sync status
- `POST /api/v1/obsidian/cleanup` - Clean up deleted files

### OAuth Integrations
- `GET /api/v1/integrations/google/authorize` - Start Google OAuth flow
- `GET /api/v1/integrations/google/status` - Get Google connection status
- `GET /api/v1/integrations/google/calendar/events` - Get Google Calendar events
- `GET /api/v1/integrations/google/gmail/messages` - Get Gmail messages
- `DELETE /api/v1/integrations/google/disconnect` - Disconnect Google account
- `GET /api/v1/integrations/microsoft/authorize` - Start Microsoft OAuth flow
- `GET /api/v1/integrations/microsoft/status` - Get Microsoft connection status
- `GET /api/v1/integrations/microsoft/calendar/events` - Get Outlook Calendar events
- `GET /api/v1/integrations/microsoft/email/messages` - Get Outlook Email messages
- `DELETE /api/v1/integrations/microsoft/disconnect` - Disconnect Microsoft account

### Search
- `GET /api/v1/search` - Search knowledge base

## Function Calling & Tools

AION supports **function calling** (also known as tool use), allowing the LLM to invoke external tools to enhance its capabilities. The system implements an **agentic loop** where the LLM can:

1. Analyze the user's request
2. Decide which tools to use
3. Execute tools and receive results
4. Use the results to formulate a comprehensive answer

### Available Tools

#### 1. Calculator Tool
Performs complex mathematical calculations using Python's `eval()` in a safe context.

**Use cases:**
- Mathematical operations
- Complex formulas
- Unit conversions

**Example:**
```python
# User: "What is 156 * 78 + 234?"
# Tool executes: 156 * 78 + 234
# Result: 12,402
```

#### 2. Web Search Tool
Searches the internet using DuckDuckGo (no API key required).

**Use cases:**
- Current events and news
- Real-time information
- General web searches
- Fact verification

**Parameters:**
- `query`: Search query
- `max_results`: Number of results (default: 5, max: 10)

**Example:**
```python
# User: "What's the latest news about AI?"
# Tool searches DuckDuckGo and returns top 5 results
```

#### 3. Code Executor Tool
Executes Python code in a secure sandboxed environment.

**Security features:**
- 10-second timeout
- Restricted imports (math, datetime, json, re, collections, itertools)
- No file system access
- No network access
- Captures stdout/stderr

**Use cases:**
- Data transformations
- Algorithm execution
- Sequence generation
- Complex calculations

**Example:**
```python
# User: "Generate the first 10 Fibonacci numbers"
# Tool executes Python code and returns: [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
```

#### 4. Knowledge Base Search Tool
Searches the user's personal knowledge base (memories and documents).

**Use cases:**
- Retrieving stored memories
- Searching uploaded documents
- Finding relevant context from past conversations

### Tool Choice Modes

You can control how tools are used through the `tool_choice` parameter:

```python
# Auto mode - LLM decides when to use tools (default)
{
  "message": "What is 25 + 17?",
  "use_tools": true,
  "tool_choice": "auto"
}

# Force specific tool
{
  "message": "What is 25 + 17?",
  "use_tools": true,
  "tool_choice": "calculator"
}

# Disable all tools
{
  "message": "What is 25 + 17?",
  "use_tools": true,
  "tool_choice": "none"
}
```

### Tool Response Format

When tools are used, the response includes metadata about tool execution:

```json
{
  "conversation_id": "uuid",
  "message": "The result is 12,402",
  "tools_used": [
    {
      "name": "calculator",
      "arguments": {"expression": "156 * 78 + 234"},
      "result": 12402
    }
  ],
  "metadata": {
    "context_tokens": 150,
    "confidence": 0.95
  }
}
```

## Agents

### Memory Agent
Extracts and manages long-term memories from conversations.

### Retriever Agent
Performs semantic search across memories and documents.

### Knowledge Sync Agent
Synchronizes and indexes Obsidian vault from GitHub.

### Conversation Agent
Main orchestrator that coordinates other agents and tool usage.

## Database Schema

### Qdrant Collections

#### `memories`
- Stores semantic embeddings of user memories
- Fields: memory_id, short_text, type, timestamp, relevance_score, embedding

#### `kb_documents`
- Stores chunked Obsidian documents
- Fields: doc_id, chunk_id, path, title, heading, tags, embedding

### Neo4j Graph
- Entities: Person, Project, Concept, Document
- Relationships: RELATED_TO, MENTIONED_IN, PART_OF

## Security

- All sensitive data encrypted at rest
- API key authentication required
- Rate limiting enabled by default
- User data isolation
- Complete data deletion on request

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues, questions, or contributions, please open an issue on GitHub.

## Acknowledgments

- Built with FastAPI
- Powered by OpenRouter for flexible LLM access (Claude 3.5 Sonnet)
- Vector storage by Qdrant
- Graph database by Neo4j
- Web search powered by DuckDuckGo

---

**Author**: David Buitrago
**Version**: 1.0.0
**Last Updated**: November 2025
