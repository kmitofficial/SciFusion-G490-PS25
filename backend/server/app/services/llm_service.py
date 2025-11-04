"""Helpers for interacting with LLM providers used by SciFusion."""
from __future__ import annotations

import json
import os
from typing import Any, Iterable, List, Literal, Tuple

from app.models.ai import ChatMessage, LLMChatResponse, Thought


Provider = Literal["anthropic", "groq", "openai", "deepseek", "gemini", "localhost"]


class LLMConfigurationError(RuntimeError):
    """Raised when an LLM provider cannot be initialised."""


def build_llm_client(model_name: str) -> Tuple[Any, str, Provider]:
    """Instantiate an LLM client for the requested provider.

    Returns a tuple of (client, resolved_model_name, provider_key).
    """

    if "claude" in model_name:
        import anthropic

        client = anthropic.Anthropic()
        return client, model_name, "anthropic"

    if model_name in {"openai/gpt-oss-120b", "openai/gpt-oss-20b"} or "groq" in model_name.lower() or model_name.startswith(
        "openai/"
    ):
        import groq

        client = groq.Groq(api_key=os.environ.get("GROQ_API_KEY"))
        return client, model_name, "groq"

    if "gpt" in model_name and not model_name.startswith("openai/"):
        import openai

        client = openai.OpenAI()
        return client, model_name, "openai"

    if "deepseek" in model_name:
        import openai

        api_key = os.environ.get("DEEPSEEK_API_KEY")
        if not api_key:
            raise LLMConfigurationError("DEEPSEEK_API_KEY must be set to use DeepSeek models.")
        client = openai.OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        return client, model_name, "deepseek"

    if model_name == "Intern-S1":
        import openai

        api_key = os.environ.get("INS1_API_KEY")
        if not api_key:
            raise LLMConfigurationError("INS1_API_KEY must be set to use Intern-S1.")
        client = openai.OpenAI(api_key=api_key, base_url="https://chat.intern-ai.org.cn/api/v1/")
        return client, model_name, "openai"

    if model_name.startswith("localhost"):
        import openai

        client = openai.OpenAI(base_url="http://localhost:11434/v1", api_key="na")
        return client, model_name, "localhost"

    if model_name.startswith("gemini"):
        import google.generativeai as genai

        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise LLMConfigurationError("GOOGLE_API_KEY must be set to use Gemini models.")
        genai.configure(api_key=api_key)
        client = genai.GenerativeModel(model_name)
        return client, model_name, "gemini"

    raise ValueError(f"Unsupported model '{model_name}'. Please extend llm_service to handle it.")


def _convert_messages_for_gemini(messages: Iterable[ChatMessage]) -> List[dict[str, Any]]:
    converted: List[dict[str, Any]] = []
    for message in messages:
        role = "user"
        if message.role == "assistant":
            role = "model"
        elif message.role == "system":
            # Gemini does not have a dedicated system role; include as user instruction.
            role = "user"
        converted.append({"role": role, "parts": [{"text": message.content}]})
    return converted


def generate_structured_chat(
    *,
    messages: Iterable[ChatMessage],
    model_name: str,
    system_prompt: str | None = None,
) -> LLMChatResponse:
    """Call the configured LLM and coerce the response into thoughts + answer."""

    client, resolved_model, provider = build_llm_client(model_name)

    guidance = (
        "You are SciFusion's research copilot. Think aloud step by step. "
        "Return a JSON object with keys: thoughts (array of objects with title and detail) and answer (string)."
    )
    if system_prompt:
        combined_system = f"{system_prompt.strip()}\n\n{guidance}"
    else:
        combined_system = guidance

    if provider != "gemini":
        raise ValueError(
            "Structured chat is currently implemented for Gemini models. "
            "Please choose a Gemini model such as 'gemini-2.5-flash-lite'."
        )

    import google.generativeai as genai
    from google.generativeai import types as genai_types

    converted_messages = list(_convert_messages_for_gemini(messages))

    model = genai.GenerativeModel(resolved_model, system_instruction=combined_system)
    generation_config = genai_types.GenerationConfig(response_mime_type="application/json")

    response = model.generate_content(converted_messages, generation_config=generation_config)
    raw_text = response.text or "{}"

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        parsed = {"answer": raw_text, "thoughts": []}

    thoughts_payload = parsed.get("thoughts") or []
    thoughts: List[Thought] = []
    if isinstance(thoughts_payload, list):
        for item in thoughts_payload:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or item.get("heading") or "Thought")
            detail = str(item.get("detail") or item.get("content") or item.get("summary") or "")
            thoughts.append(Thought(title=title.strip(), detail=detail.strip()))

    answer = parsed.get("answer") or parsed.get("content") or raw_text
    if isinstance(answer, dict):
        answer = json.dumps(answer, indent=2)
    elif not isinstance(answer, str):
        answer = str(answer)

    return LLMChatResponse(content=answer.strip(), thoughts=thoughts, raw=parsed)


__all__ = ["LLMConfigurationError", "build_llm_client", "generate_structured_chat"]