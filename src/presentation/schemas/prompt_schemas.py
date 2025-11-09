"""
Pydantic schemas for system prompt API.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class SystemPromptResponse(BaseModel):
    """System prompt response schema."""

    prompt_type: str = Field(..., description="Type of the prompt")
    content: str = Field(..., description="Prompt content")
    description: str = Field(..., description="Prompt description")
    is_active: bool = Field(..., description="Whether the prompt is active")
    created_at: datetime | None = Field(None, description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")

    class Config:
        from_attributes = True


class SystemPromptUpdateRequest(BaseModel):
    """Request schema for updating a system prompt."""

    content: str = Field(..., description="New prompt content", min_length=10)
    description: str | None = Field(None, description="Optional description update")


class SystemPromptCreateRequest(BaseModel):
    """Request schema for creating a system prompt."""

    prompt_type: str = Field(..., description="Type of the prompt")
    content: str = Field(..., description="Prompt content", min_length=10)
    description: str = Field(..., description="Prompt description")
    is_active: bool = Field(True, description="Whether the prompt is active")


class PromptsListResponse(BaseModel):
    """Response schema for listing all prompts."""

    prompts: list[SystemPromptResponse]
    total: int = Field(..., description="Total number of prompts")
