"""
LLM service - High-level interface for language model operations.
"""

from typing import TYPE_CHECKING, Any

from src.config.settings import get_settings
from src.domain.entities.tool import ToolCall
from src.infrastructure.llm.openrouter_client import OpenRouterClient
from src.shared.exceptions import LLMServiceError
from src.shared.logging import LoggerMixin

if TYPE_CHECKING:
    from src.infrastructure.tools.tool_registry import ToolRegistry


class LLMService(LoggerMixin):
    """
    High-level service for LLM operations.

    Provides convenient methods for common LLM tasks like:
    - Chat completions
    - Memory extraction
    - Summarization
    - Question answering
    """

    def __init__(
        self,
        client: OpenRouterClient | None = None,
        tool_registry: "ToolRegistry | None" = None,
    ) -> None:
        """
        Initialize LLM service.

        Args:
            client: OpenRouter client instance (optional, will create if not provided)
            tool_registry: Tool registry for function calling (optional)
        """
        self.settings = get_settings()
        self.client = client or OpenRouterClient()
        self.tool_registry = tool_registry
        self.default_model = self.settings.openrouter.openrouter_llm_model
        # Use faster, cheaper model for extractions
        self.extraction_model = "anthropic/claude-3-haiku"

    async def close(self) -> None:
        """Close the underlying client."""
        await self.client.close()

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> str:
        """
        Generate a chat response.

        Args:
            messages: List of message dictionaries
            model: Model to use (defaults to configured model)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Generated response text

        Raises:
            LLMServiceError: If generation fails
        """
        model = model or self.default_model

        self.logger.info(
            "chat_request",
            model=model,
            num_messages=len(messages),
        )

        response = await self.client.generate_completion(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        content = response["choices"][0]["message"]["content"]

        self.logger.info(
            "chat_response_generated",
            model=model,
            response_length=len(content),
        )

        return content

    async def extract_memories(
        self, conversation_text: str, user_profile: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Extract key memories from a conversation.

        Args:
            conversation_text: The conversation transcript
            user_profile: Optional user profile context

        Returns:
            List of extracted memories with metadata

        Raises:
            LLMServiceError: If extraction fails
        """
        self.logger.info("extracting_memories", text_length=len(conversation_text))

        system_prompt = """You are a memory extraction assistant. Analyze the conversation and extract key facts, preferences, and important information about the user.

For each memory, provide:
- short_text: A concise statement (max 150 chars)
- type: One of [preference, fact, task, goal, profile]
- relevance_score: Float between 0 and 1
- sensitivity: One of [low, medium, high]

Return ONLY a valid JSON array of memory objects. Example:
[
  {
    "short_text": "User prefers concise technical answers",
    "type": "preference",
    "relevance_score": 0.9,
    "sensitivity": "low"
  }
]

If no significant memories are found, return an empty array: []"""

        user_prompt = f"Conversation:\n{conversation_text}"
        if user_profile:
            user_prompt = f"User Profile:\n{user_profile}\n\n{user_prompt}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        response = await self.chat(
            messages, model=self.extraction_model, temperature=0.3, max_tokens=1000
        )

        # Parse JSON response
        try:
            import json

            memories = json.loads(response.strip())
            self.logger.info("memories_extracted", count=len(memories))
            return memories

        except json.JSONDecodeError as e:
            self.logger.error("memory_extraction_json_error", error=str(e), response=response)
            raise LLMServiceError(
                "Failed to parse memory extraction response",
                details={"error": str(e), "response": response},
            ) from e

    async def summarize_conversation(
        self, conversation_text: str, max_length: int = 200
    ) -> str:
        """
        Generate a summary of a conversation.

        Args:
            conversation_text: The conversation to summarize
            max_length: Maximum summary length in characters

        Returns:
            Summary text

        Raises:
            LLMServiceError: If summarization fails
        """
        self.logger.info(
            "summarizing_conversation",
            text_length=len(conversation_text),
            max_length=max_length,
        )

        system_prompt = f"Summarize the following conversation in {max_length} characters or less. Focus on key topics, decisions, and action items."

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": conversation_text},
        ]

        summary = await self.chat(messages, temperature=0.3, max_tokens=max_length // 3)

        self.logger.info("conversation_summarized", summary_length=len(summary))

        return summary

    async def answer_with_context(
        self,
        question: str,
        context: str,
        system_prompt: str | None = None,
    ) -> str:
        """
        Answer a question using provided context (RAG pattern).

        Args:
            question: User's question
            context: Retrieved context from memory/documents
            system_prompt: Optional custom system prompt

        Returns:
            Answer text

        Raises:
            LLMServiceError: If generation fails
        """
        self.logger.info(
            "answering_with_context",
            question_length=len(question),
            context_length=len(context),
        )

        if system_prompt is None:
            system_prompt = """You are AION, an intelligent personal assistant with access to the user's knowledge base and conversation history.

Use the provided context to answer the user's question accurately and concisely. If the context doesn't contain relevant information, say so honestly.

Always cite sources when referencing specific information from the context."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ]

        answer = await self.chat(messages, temperature=0.7)

        self.logger.info("answer_generated", answer_length=len(answer))

        return answer

    async def classify_intent(
        self, user_message: str, intents: list[str]
    ) -> str:
        """
        Classify user message intent.

        Args:
            user_message: User's message
            intents: List of possible intents

        Returns:
            Classified intent

        Raises:
            LLMServiceError: If classification fails
        """
        self.logger.info(
            "classifying_intent",
            message_length=len(user_message),
            num_intents=len(intents),
        )

        system_prompt = f"""Classify the user's message into one of these intents:
{', '.join(intents)}

Respond with ONLY the intent name, nothing else."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        intent = await self.chat(messages, temperature=0.1, max_tokens=50)

        self.logger.info("intent_classified", intent=intent.strip())

        return intent.strip()

    async def generate_entity_description(
        self, entity_name: str, entity_type: str, context: str
    ) -> str:
        """
        Generate a description for a knowledge graph entity.

        Args:
            entity_name: Name of the entity
            entity_type: Type of entity
            context: Context in which entity appears

        Returns:
            Entity description

        Raises:
            LLMServiceError: If generation fails
        """
        self.logger.info(
            "generating_entity_description",
            entity_name=entity_name,
            entity_type=entity_type,
        )

        system_prompt = "Generate a concise description (max 100 words) for the entity based on the context provided."

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Entity: {entity_name}\nType: {entity_type}\nContext: {context}",
            },
        ]

        description = await self.chat(messages, temperature=0.5, max_tokens=150)

        self.logger.info(
            "entity_description_generated",
            entity_name=entity_name,
            description_length=len(description),
        )

        return description

    async def extract_entities(
        self, text: str, context: str | None = None
    ) -> list[dict[str, Any]]:
        """
        Extract named entities from text for knowledge graph.

        Args:
            text: Text to extract entities from
            context: Optional additional context

        Returns:
            List of extracted entities with metadata

        Raises:
            LLMServiceError: If extraction fails
        """
        self.logger.info("extracting_entities", text_length=len(text))

        system_prompt = """You are an entity extraction assistant. Analyze the text and extract important named entities.

For each entity, provide:
- name: The entity name (exact as it appears)
- type: One of [person, project, concept, organization, document, event, location]
- description: Brief description of the entity (1-2 sentences)
- properties: Key-value pairs with additional info (e.g., {"role": "developer", "status": "active"})
- confidence: Float between 0 and 1

Extract only significant entities (people, organizations, projects, concepts, locations, events).
Avoid extracting common nouns or trivial mentions.

Return ONLY a valid JSON array of entity objects. Example:
[
  {
    "name": "María González",
    "type": "person",
    "description": "Team member working on the AION project",
    "properties": {"role": "developer"},
    "confidence": 0.95
  },
  {
    "name": "AION",
    "type": "project",
    "description": "AI personal assistant with long-term memory",
    "properties": {"status": "development"},
    "confidence": 1.0
  }
]

If no significant entities are found, return an empty array: []"""

        user_prompt = f"Text to analyze:\n{text}"
        if context:
            user_prompt = f"Context:\n{context}\n\n{user_prompt}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        response = await self.chat(
            messages, model=self.extraction_model, temperature=0.2, max_tokens=2000
        )

        # Parse JSON response
        try:
            import json

            entities = json.loads(response.strip())
            self.logger.info("entities_extracted", count=len(entities))
            return entities

        except json.JSONDecodeError as e:
            self.logger.error(
                "entity_extraction_json_error", error=str(e), response=response
            )
            raise LLMServiceError(
                "Failed to parse entity extraction response",
                details={"error": str(e), "response": response[:500]},
            ) from e

    async def extract_relationships(
        self, text: str, entities: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Extract relationships between entities from text.

        Args:
            text: Text containing the entities
            entities: List of extracted entities

        Returns:
            List of relationships

        Raises:
            LLMServiceError: If extraction fails
        """
        if len(entities) < 2:
            self.logger.info("skipping_relationship_extraction", reason="not_enough_entities")
            return []

        self.logger.info(
            "extracting_relationships",
            text_length=len(text),
            num_entities=len(entities),
        )

        entity_names = [e["name"] for e in entities]

        system_prompt = """You are a relationship extraction assistant. Analyze the text and identify meaningful relationships between the provided entities.

For each relationship, provide:
- source_name: Source entity name (must match exactly from entity list)
- target_name: Target entity name (must match exactly from entity list)
- type: One of [RELATED_TO, MENTIONED_IN, PART_OF, CREATED_BY, WORKS_ON, LOCATED_IN, ASSOCIATED_WITH, DEPENDS_ON]
- properties: Key-value pairs with additional info (e.g., {"context": "mentioned in meeting"})
- strength: Float between 0 and 1 indicating relationship strength

Extract only clear, meaningful relationships. Avoid speculative connections.

Return ONLY a valid JSON array of relationship objects. Example:
[
  {
    "source_name": "María González",
    "target_name": "AION",
    "type": "WORKS_ON",
    "properties": {"role": "developer"},
    "strength": 0.9
  },
  {
    "source_name": "AION",
    "target_name": "FastAPI",
    "type": "DEPENDS_ON",
    "properties": {"component": "backend framework"},
    "strength": 0.95
  }
]

If no relationships are found, return an empty array: []"""

        user_prompt = f"""Entities found:
{', '.join(entity_names)}

Text to analyze:
{text}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        response = await self.chat(
            messages, model=self.extraction_model, temperature=0.2, max_tokens=2000
        )

        # Parse JSON response
        try:
            import json

            relationships = json.loads(response.strip())
            self.logger.info("relationships_extracted", count=len(relationships))
            return relationships

        except json.JSONDecodeError as e:
            self.logger.error(
                "relationship_extraction_json_error", error=str(e), response=response
            )
            raise LLMServiceError(
                "Failed to parse relationship extraction response",
                details={"error": str(e), "response": response[:500]},
            ) from e

    async def chat_with_tools(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        max_iterations: int = 5,
    ) -> dict[str, Any]:
        """
        Chat with tool calling support (agentic loop).

        This method implements the full tool calling loop:
        1. Send request with tools
        2. If model requests tools, execute them
        3. Send results back
        4. Repeat until model responds with text (finish_reason: "stop")

        Args:
            messages: List of message dictionaries
            model: Model to use (defaults to configured model)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            max_iterations: Maximum iterations in the agentic loop (default: 5)

        Returns:
            Final response with tool call history

        Raises:
            LLMServiceError: If tool calling fails
            ValueError: If tool registry is not configured
        """
        if self.tool_registry is None:
            raise ValueError("Tool registry is not configured for this LLM service")

        model = model or self.default_model

        self.logger.info(
            "chat_with_tools_starting",
            model=model,
            num_messages=len(messages),
            max_iterations=max_iterations,
        )

        # Get tool definitions
        tools = self.tool_registry.get_tools_definitions()

        if not tools:
            # No tools available, fall back to regular chat
            self.logger.warning("no_tools_available_falling_back_to_regular_chat")
            return await self.client.generate_completion(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

        # Agentic loop
        conversation_messages = messages.copy()
        tool_calls_history = []
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            self.logger.info(
                "tool_calling_iteration",
                iteration=iteration,
                num_messages=len(conversation_messages),
            )

            # Send request with tools
            response = await self.client.generate_completion(
                model=model,
                messages=conversation_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                tools=tools,
                tool_choice="auto",
            )

            # Get response message
            response_message = response["choices"][0]["message"]
            finish_reason = response["choices"][0]["finish_reason"]

            # Check if model wants to call tools
            if finish_reason == "tool_calls" and response_message.get("tool_calls"):
                tool_calls_data = response_message["tool_calls"]

                self.logger.info(
                    "model_requested_tools", num_tools=len(tool_calls_data)
                )

                # Add assistant message with tool calls to conversation
                conversation_messages.append(response_message)

                # Parse tool calls
                tool_calls = []
                for tc in tool_calls_data:
                    import json

                    tool_calls.append(
                        ToolCall(
                            tool_call_id=tc["id"],
                            tool_name=tc["function"]["name"],
                            arguments=json.loads(tc["function"]["arguments"]),
                        )
                    )

                # Execute tools
                tool_results = await self.tool_registry.execute_multiple_tool_calls(
                    tool_calls
                )

                # Add to history
                tool_calls_history.extend(
                    [
                        {
                            "tool_name": tr.tool_name,
                            "arguments": tc.arguments,
                            "result": tr.result,
                            "success": tr.success,
                            "error": tr.error,
                        }
                        for tc, tr in zip(tool_calls, tool_results)
                    ]
                )

                # Add tool results to conversation
                for tool_result in tool_results:
                    conversation_messages.append(tool_result.to_message_format())

                # Continue loop to get next response
                continue

            else:
                # Model responded with text, exit loop
                self.logger.info(
                    "tool_calling_completed",
                    iterations=iteration,
                    num_tool_calls=len(tool_calls_history),
                    finish_reason=finish_reason,
                )

                # Add tool call history to response
                response["tool_calls_history"] = tool_calls_history
                response["iterations"] = iteration

                return response

        # Max iterations reached
        self.logger.warning(
            "tool_calling_max_iterations_reached",
            max_iterations=max_iterations,
            num_tool_calls=len(tool_calls_history),
        )

        # Return last response even if max iterations reached
        return {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "Maximum tool calling iterations reached. Please try simplifying your request.",
                    },
                    "finish_reason": "max_iterations",
                }
            ],
            "tool_calls_history": tool_calls_history,
            "iterations": iteration,
        }
