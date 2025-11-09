🧠 Functional and Technical Specification Document
Project: AI Personal Assistant with Long-Term Memory and Knowledge Base

Author: David Buitrago
Department: IT / Innovation
Date: November 2025
Version: 1.0

1. Project Overview

The goal of this project is to build an AI Personal Assistant capable of maintaining long-term memory across conversations, integrating with the user’s Obsidian knowledge base (hosted on GitHub), and retrieving information from a document-based knowledge base (KB).
The assistant should use semantic understanding to recall relevant information, adapt over time based on user interactions, and provide contextually rich responses.

2. Objectives

Create a persistent, intelligent assistant that remembers key facts, preferences, and conversations.

Enable semantic search across both long-term memory and documents.

Allow the assistant to access, index, and retrieve information from an Obsidian Vault synchronized via GitHub.

Ensure scalability and maintainability through a modular architecture with Qdrant for vector storage and LangChain / n8n for orchestration.

Provide a clear development framework that allows future agents or microservices to collaborate (e.g., summarization agent, reasoning agent, document updater).

3. Functional Requirements
3.1 Core Features
ID	Feature	Description
F1	Conversation Handling	The assistant must handle multi-turn conversations, maintaining context within the current session.
F2	Long-Term Memory	Store and retrieve relevant information from previous sessions, such as preferences, facts, and tasks.
F3	Memory Extraction	Automatically summarize and store key facts after each conversation.
F4	Knowledge Base Retrieval	Search and retrieve relevant notes and documents from the Obsidian Vault or other document sources (PDFs, reports, etc.).
F5	Context Assembly for RAG	Combine relevant information from long-term memory and documents into a contextual prompt for the LLM.
F6	Knowledge Synchronization	Automatically sync and re-index Obsidian files from a GitHub repository.
F7	User Profile Learning	Continuously update user profile based on conversation patterns and explicit preferences.
F8	Memory Management UI (optional)	Allow users to review, edit, or delete stored memories.
F9	Entity Linking (optional)	Create and manage entity relationships (people, projects, concepts) using Neo4j for reasoning and explainability.
3.2 System Automation
ID	Requirement	Description
A1	Auto-Sync Scheduler	Use n8n or cron job to pull updates from GitHub every X hours.
A2	Chunking & Embedding Service	Split documents into chunks, generate embeddings, and upsert to Qdrant.
A3	Conversation Logging	Log all user interactions with timestamps and metadata.
A4	Memory Consolidation Job	Merge similar memories weekly and prune unused ones.
A5	Version Control Integration	Detect and update embeddings only for modified Obsidian files.
3.3 Security and Privacy
ID	Requirement	Description
S1	Data Ownership	All stored data (memory, documents, embeddings) belongs exclusively to the user.
S2	Encryption	Sensitive data and embeddings must be encrypted at rest.
S3	Access Control	Authentication required for modifying or reading stored memories.
S4	Data Deletion	User can delete individual memories or full history on request.
S5	Privacy Filtering	AI model must avoid outputting sensitive or personal data unless explicitly requested by the user.
4. Acceptance Criteria
ID	Criterion	Description
AC1	Persistent Recall	The assistant successfully recalls preferences or facts mentioned in past sessions (e.g., “You prefer concise answers”).
AC2	Accurate Retrieval	When asked about a topic in the Obsidian Vault, the assistant retrieves relevant chunks with >85% semantic relevance.
AC3	Memory Updates	The system automatically adds and updates memories after each session.
AC4	Document Synchronization	Changes in the GitHub Vault trigger updates in the Qdrant KB within 1 hour.
AC5	Explainable Output	The assistant can cite document sources or the memory that influenced an answer.
AC6	Low Latency	Context retrieval and generation combined should take less than 3 seconds per query.
AC7	Safe Forgetting	Deleted memories or notes are permanently removed from both Qdrant and backup storage.
AC8	Scalability	The system handles at least 50,000 document chunks and 10,000 memory entries without performance degradation.
5. Technical Architecture
5.1 System Overview
+---------------------------------------------------------------+
|                       AI PERSONAL ASSISTANT                   |
+---------------------------------------------------------------+
|  User Interface (Chat UI / Telegram / Web App / Voice)        |
+---------------------------------------------------------------+
|  Orchestration Layer (n8n / FastAPI / LangChain Agent)        |
|  ----------------------------------------------------------   |
|   - Conversation handler                                      |
|   - Memory manager                                            |
|   - RAG pipeline (retrieve, assemble, generate)               |
|   - Event triggers (sync, memory extraction)                  |
+---------------------------------------------------------------+
|  Storage Layer                                                |
|   - Qdrant: semantic vector store (memories + documents)      |
|   - Neo4j (optional): entity graph                            |
|   - PostgreSQL / SQLite: metadata + logs                      |
|   - GitHub Repo: Obsidian Vault                               |
+---------------------------------------------------------------+
|  Model Layer (LLMs + Embeddings)                              |
|   - Embedding model: OpenAI text-embedding-3 / local LLaMA    |
|   - LLM: GPT-4/5 or local model via Ollama / LM Studio        |
+---------------------------------------------------------------+

6. Qdrant Collections Structure
6.1 memories Collection
Field	Type	Description
memory_id	UUID	Unique memory identifier
short_text	string	Short factual statement
type	enum	preference, fact, task, goal, profile
timestamp	datetime	When it was created
last_referenced_at	datetime	Last time it was used
relevance_score	float	Memory importance (0–1)
num_times_referenced	int	Frequency metric
sensitivity	enum	low, medium, high
embedding	vector	Semantic representation
source	string	Origin (conversation ID or file)
6.2 kb_documents Collection
Field	Type	Description
doc_id	UUID	Document ID
chunk_id	hash	Unique chunk identifier
path	string	File path in Obsidian Vault
title	string	Document title
heading	string	Markdown section heading
tags	array	Associated tags
created_at	datetime	File creation date
updated_at	datetime	Last update
language	string	en, es, etc.
embedding	vector	Chunk embedding
source_type	string	obsidian, pdf, etc.
7. Technical Rules and Development Guidelines
Rule	Description
R1	All embeddings must be deterministic (same text → same vector) for idempotent upserts.
R2	Use Cosine similarity for all Qdrant collections.
R3	Keep memory items under 150 characters for optimal retrieval.
R4	Each Obsidian file is chunked into max 500-token segments with 50-token overlap.
R5	Embed documents and memories using the same embedding model for compatibility.
R6	Store metadata and embeddings separately — keep text minimal inside payloads.
R7	Update last_referenced_at after each retrieval to allow recency weighting.
R8	Do not directly store or expose sensitive data without encryption.
R9	Memory extraction must use an LLM summarization chain producing JSON outputs.
R10	All agents must log actions with timestamps and unique identifiers for traceability.
8. Tech Stack Summary
Layer	Technology	Purpose
Frontend / UI	Telegram Bot, Web UI, or Chat Widget	User interface
Orchestration	n8n + LangChain or FastAPI	Pipeline logic
Vector Store	Qdrant	Memory + document embeddings
Graph DB (optional)	Neo4j	Entity relationships
Database (optional)	PostgreSQL / SQLite	Metadata, logs
Knowledge Base	GitHub (Obsidian Vault)	Document source
Embeddings	OpenAI text-embedding-3-small or all-MiniLM-L6-v2 (local)	Semantic encoding
LLM	GPT-4/5 via Azure OpenAI, or Ollama (LLaMA 3.2)	Generation, summarization, reasoning
Scheduler / Sync	n8n cron trigger or GitHub webhook	Auto-sync Obsidian vault
Deployment	Docker Compose	Containerized services
Security	API key auth + local encryption	Access and privacy
9. Agent Collaboration Rules
9.1 Main Agents
Agent	Responsibility
Memory Agent	Extracts, summarizes, and manages memories (Qdrant memories).
Retriever Agent	Searches Qdrant for relevant documents and memories.
Summarizer Agent	Summarizes long texts or groups of memories.
Knowledge Sync Agent	Watches GitHub repo and reindexes changes.
Conversation Agent (Core)	Interfaces with user, uses other agents to assemble responses.
9.2 Collaboration Protocol

Conversation Agent receives user message.

It sends the message to Retriever Agent, which performs:

Semantic search in memories (K=5).

Semantic search in kb_documents (K=10).

Both contexts are passed to the LLM for generation.

After the response, the Memory Agent evaluates if new memories should be stored.

Periodic tasks (e.g., Knowledge Sync Agent) run on schedule via n8n.

10. Future Enhancements

Add voice interface (Whisper + TTS).

Integrate Neo4j for entity reasoning and explainability.

Implement memory aging and semantic clustering.

Add user dashboard for reviewing stored memories.

Enable team memory sharing (with user consent).

11. Acceptance Testing Checklist
Test Case	Expected Result
Recall personal preferences	Assistant accurately recalls saved preferences.
Retrieve note from Obsidian	Assistant finds relevant note and cites file path.
Add new memory automatically	After conversation, new fact stored in Qdrant.
Delete a memory	Memory removed and not retrievable anymore.
GitHub sync	Changes appear in Qdrant within 1 hour.
Response time	< 3 seconds average retrieval and generation.