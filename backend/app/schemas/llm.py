from enum import Enum as PyEnum
from typing import Dict, List, Optional, Union, Any

from pydantic import BaseModel, Field, validator


class LLMProvider(str, PyEnum):
    """
    Supported LLM providers.
    """
    OPENAI = "openai"
    GOOGLE = "google"
    ANTHROPIC = "anthropic"
    LLAMA = "llama"
    CUSTOM = "custom"


class LLMModel(BaseModel):
    """
    Schema for LLM model information.
    """
    provider: LLMProvider
    name: str
    version: Optional[str] = None
    description: Optional[str] = None
    context_window: int
    max_output_tokens: int
    supports_streaming: bool = False
    supports_function_calling: bool = False
    is_private: bool = False
    cost_per_1k_input: Optional[float] = None
    cost_per_1k_output: Optional[float] = None


class LLMSettings(BaseModel):
    """
    Schema for LLM generation settings.
    """
    model: str
    provider: LLMProvider
    temperature: float = 0.2
    top_p: Optional[float] = None
    max_tokens: int = 1000
    stop_sequences: Optional[List[str]] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    timeout: int = 60
    use_streaming: bool = False


class LLMGenerateRequest(BaseModel):
    """
    Schema for LLM text generation requests.
    """
    prompt: str
    system_message: Optional[str] = None
    settings: LLMSettings
    include_reasoning: bool = False
    include_sources: bool = True


class LLMChatMessage(BaseModel):
    """
    Schema for chat message in an LLM conversation.
    """
    role: str  # "system", "user", "assistant", "function"
    content: str
    name: Optional[str] = None  # For function messages
    function_call: Optional[Dict[str, Any]] = None


class LLMChatRequest(BaseModel):
    """
    Schema for LLM chat generation requests.
    """
    messages: List[LLMChatMessage]
    settings: LLMSettings
    functions: Optional[List[Dict[str, Any]]] = None
    include_reasoning: bool = False
    include_sources: bool = True


class LLMToolCall(BaseModel):
    """
    Schema for LLM function/tool call.
    """
    name: str
    arguments: Dict[str, Any]
    id: Optional[str] = None


class LLMSource(BaseModel):
    """
    Schema for sources used in LLM generation.
    """
    content_id: int
    content_type: str
    text: str
    score: float
    metadata: Optional[Dict[str, Any]] = None


class LLMGenerateResponse(BaseModel):
    """
    Schema for LLM text generation responses.
    """
    text: str
    model: str
    provider: LLMProvider
    token_count: dict
    elapsed_time: float
    reasoning: Optional[str] = None
    sources: Optional[List[LLMSource]] = None
    tool_calls: Optional[List[LLMToolCall]] = None
    finish_reason: Optional[str] = None


class LLMChatResponse(BaseModel):
    """
    Schema for LLM chat generation responses.
    """
    message: LLMChatMessage
    model: str
    provider: LLMProvider
    token_count: dict
    elapsed_time: float
    reasoning: Optional[str] = None
    sources: Optional[List[LLMSource]] = None
    finish_reason: Optional[str] = None


class LLMStreamingChunk(BaseModel):
    """
    Schema for streaming chunks from LLM generation.
    """
    text: str
    is_finished: bool = False
    token_count: Optional[Dict[str, int]] = None
    tool_calls: Optional[List[LLMToolCall]] = None
    finish_reason: Optional[str] = None


class LLMModelListResponse(BaseModel):
    """
    Schema for listing available LLM models.
    """
    models: List[LLMModel]
    default_model: str 