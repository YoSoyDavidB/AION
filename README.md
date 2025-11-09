# AION - AI Personal Assistant with Long-Term Memory

AION is an intelligent personal assistant that maintains long-term memory across conversations, integrates with your Obsidian knowledge base, and provides contextually rich responses through semantic understanding.

## ✨ Features

### Core Capabilities
- **Long-Term Memory**: Remembers key facts, preferences, and conversations across sessions
- **Obsidian Integration**: Seamlessly syncs and searches your Obsidian vault from GitHub
- **Semantic Search**: RAG pipeline for intelligent context retrieval
- **Entity Relationships**: Knowledge graph using Neo4j for advanced reasoning
- **Customizable AI Behavior**: Manage system prompts through the UI

### Integrations
- **Calendar & Email Integration**: Connect Google and Microsoft accounts
  - Google: Calendar events and Gmail messages
  - Microsoft: Outlook Calendar and Email
  - Secure OAuth 2.0 with encrypted token storage

### AI Tools
- **Web Search**: Search the internet using DuckDuckGo
- **Code Executor**: Run Python code in a sandboxed environment
- **Calculator**: Perform complex mathematical calculations
- **Knowledge Base Search**: Query memories and documents

## 🏗️ Architecture

AION follows Clean Architecture principles with clear separation of concerns:

```
AION/
├── src/                    # Backend (Python/FastAPI)
│   ├── domain/            # Business entities and rules
│   ├── application/       # Use cases and business logic
│   ├── infrastructure/    # External services (DB, LLM, etc.)
│   ├── presentation/      # API layer
│   └── shared/           # Common utilities
├── frontend/              # Frontend (React/TypeScript)
│   ├── src/
│   │   ├── components/   # UI components
│   │   ├── pages/        # Page components
│   │   └── lib/          # Utilities and API clients
│   └── public/
├── docs/                  # Documentation
│   ├── features/         # Feature documentation
│   ├── guides/           # Usage guides
│   ├── ARCHITECTURE.md
│   ├── SETUP.md
│   └── SPECIFICATION.md
├── scripts/              # Utility scripts
└── tests/               # Test suites
    └── manual/          # Manual test scripts
```

### Tech Stack

**Backend**
- FastAPI + Python 3.12
- PostgreSQL (user data, prompts, OAuth tokens)
- Qdrant (vector store for semantic search)
- Neo4j (knowledge graph)
- OpenRouter (LLM provider - Claude 3.5 Sonnet)

**Frontend**
- React + TypeScript
- Vite
- TanStack Query
- Tailwind CSS + shadcn/ui

**Infrastructure**
- Docker + Docker Compose
- Poetry (Python dependency management)
- npm (Frontend dependency management)

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.12+
- Node.js 18+
- Poetry
- Git

### 1. Clone and Setup

```bash
git clone <repository-url>
cd AION
cp .env.example .env
```

### 2. Configure Environment Variables

Edit `.env` with your credentials:

```bash
# LLM Configuration
OPENROUTER_API_KEY=your_key_here
EMBEDDING_MODEL=openai/text-embedding-3-small
LLM_MODEL=anthropic/claude-3.5-sonnet

# OAuth (Optional)
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
MICROSOFT_CLIENT_ID=your_client_id
MICROSOFT_CLIENT_SECRET=your_client_secret

# GitHub Integration (Optional)
GITHUB_TOKEN=your_token
GITHUB_REPO_OWNER=your_username
GITHUB_REPO_NAME=your_vault_repo
```

### 3. Start Services

```bash
# Start all services (PostgreSQL, Neo4j, Qdrant)
docker-compose up -d

# Install Python dependencies
poetry install

# Initialize database
poetry run python scripts/init_db.py
poetry run python scripts/migrate_prompts.py

# Start backend
poetry run python -m src.main

# In another terminal, start frontend
cd frontend
npm install
npm run dev
```

### 4. Access the Application

- Frontend: http://localhost:5174
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 📚 Documentation

### Core Documentation
- [Architecture](docs/ARCHITECTURE.md) - System design and components
- [Setup Guide](docs/SETUP.md) - Detailed installation instructions
- [Specification](docs/SPECIFICATION.md) - Functional and technical specs
- [Project Structure](docs/PROJECT_STRUCTURE.md) - Codebase organization

### Feature Documentation
- [Obsidian Sync](docs/features/OBSIDIAN_SYNC.md) - Sync your Obsidian vault
- [OAuth Integration](docs/features/OAUTH_INTEGRATION.md) - Google/Microsoft setup
- [Prompt Management](docs/features/PROMPT_MANAGEMENT.md) - Customize AI behavior
- [Tools & Functions](docs/features/TOOLS.md) - Available AI tools

## 🎯 Main Features

### 1. Chat Interface
Natural conversation with long-term memory and context awareness.

### 2. Memory Management
View, search, and organize extracted memories from conversations.

### 3. Document Management
Upload and manage documents for the knowledge base.

### 4. Knowledge Graph
Visualize entity relationships and connections.

### 5. Prompt Management
Customize AI behavior by editing system prompts through the UI.

### 6. Settings & Integrations
- Sync Obsidian vault from GitHub
- Connect Google/Microsoft accounts
- Manage OAuth connections

## 🛠️ Development

### Running Tests

```bash
# Backend tests
poetry run pytest

# Manual test scripts
poetry run python tests/manual/test_all_tools.py
```

### Available Scripts

```bash
# Database utilities
scripts/init_db.py              # Initialize database
scripts/migrate_prompts.py      # Migrate prompts table
scripts/check_missing_user_id.py # Check for missing user IDs
scripts/fix_missing_user_id.py  # Fix missing user IDs

# Docker commands
docker-compose up -d            # Start all services
docker-compose down             # Stop all services
docker-compose logs -f api      # View API logs
docker-compose build --no-cache # Rebuild images
```

## 🔐 Security

- All data encrypted at rest
- OAuth tokens stored with Fernet encryption
- Secure credential management with separate encryption keys
- Environment-based configuration
- Privacy-first design

## 📝 Project Status

### ✅ Completed
- Core chat functionality
- Long-term memory system
- Document management
- Knowledge graph
- Obsidian sync from GitHub
- Google/Microsoft OAuth integration
- Tool system (web search, calculator, code execution)
- Prompt management system
- Frontend UI

### 🚧 In Progress
- Enhanced entity extraction
- Improved relationship detection
- Advanced search capabilities

### 📋 Planned
- Mobile application
- Voice interface
- Multi-language support
- Plugin system
- Advanced analytics

## 🤝 Contributing

Contributions are welcome! Please read the contributing guidelines before submitting PRs.

## 📄 License

[Add your license here]

## 🙏 Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev/)
- [OpenRouter](https://openrouter.ai/)
- [Qdrant](https://qdrant.tech/)
- [Neo4j](https://neo4j.com/)
- [shadcn/ui](https://ui.shadcn.com/)

---

For more detailed information, see the [documentation](docs/).
