from typing import Optional
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from app.config import (
    HUGGINGFACEHUB_API_TOKEN,
    HUGGINGFACE_MODEL,
    HUGGINGFACE_PROVIDER,
    HUGGINGFACE_MAX_NEW_TOKENS,
    HUGGINGFACE_TEMPERATURE,
    HUGGINGFACE_TOP_P,
    HUGGINGFACE_TIMEOUT,
    is_valid_hf_token,
)


def create_llm_endpoint(
    repo_id: Optional[str] = None,
    token: Optional[str] = None,
    provider: Optional[str] = None,
    temperature: Optional[float] = None,
    max_new_tokens: Optional[int] = None,
    top_p: Optional[float] = None,
    timeout: Optional[int] = None,
) -> HuggingFaceEndpoint:
    """
    Construct a configured HuggingFaceEndpoint instance using validated settings.
    """
    model_id = repo_id or HUGGINGFACE_MODEL
    api_token = token or HUGGINGFACEHUB_API_TOKEN
    model_provider = provider if provider is not None else HUGGINGFACE_PROVIDER

    endpoint_kwargs = {
        "repo_id": model_id,
        "task": "text-generation",
        "max_new_tokens": max_new_tokens or HUGGINGFACE_MAX_NEW_TOKENS,
        "top_p": top_p or HUGGINGFACE_TOP_P,
        "temperature": temperature if temperature is not None else HUGGINGFACE_TEMPERATURE,
        "timeout": timeout or HUGGINGFACE_TIMEOUT,
    }

    if api_token:
        endpoint_kwargs["huggingfacehub_api_token"] = api_token

    if model_provider:
        endpoint_kwargs["provider"] = model_provider

    return HuggingFaceEndpoint(**endpoint_kwargs)


def create_chat_model(
    endpoint: Optional[HuggingFaceEndpoint] = None,
) -> ChatHuggingFace:
    """
    Construct a ChatHuggingFace wrapper instance with tool-calling capabilities.
    """
    active_llm = endpoint or create_llm_endpoint()
    return ChatHuggingFace(
        llm=active_llm,
        model_id=active_llm.repo_id or HUGGINGFACE_MODEL,
    )


# Standard singleton instances for backward compatibility across modules
llm = create_llm_endpoint()
model = create_chat_model(llm)


