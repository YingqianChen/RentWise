"""LLM Provider abstraction layer

Supports multiple LLM providers with unified interface:
- Ollama (local/remote server)
- Groq (cloud API)
"""

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ...core.config import settings


class LLMProvider(ABC):
    """LLM provider abstract base class"""

    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Chat completion"""
        pass

    @abstractmethod
    async def chat_completion_json(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Chat completion with JSON output"""
        pass


class OllamaProvider(LLMProvider):
    """Ollama provider"""

    def __init__(self, host: str, api_key: str):
        import ollama
        self.client = ollama.AsyncClient(
            host=host,
            headers={'Authorization': f'Bearer {api_key}'} if api_key else None
        )

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
    ) -> str:
        response = await self.client.chat(
            model=model,
            messages=messages,
            options={
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        )
        return response.get('message', {}).get('content', "")

    async def chat_completion_json(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        response = await self.client.chat(
            model=model,
            messages=messages,
            format='json',
            options={
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        )
        content = response.get('message', {}).get('content', '{}')
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return self._extract_json_block(content)

    def _extract_json_block(self, text: str) -> Dict[str, Any]:
        """Extract JSON block from text"""
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("Model response does not contain a valid JSON object.")
        return json.loads(text[start: end + 1])


class GroqProvider(LLMProvider):
    """Groq provider"""

    def __init__(self, api_key: str):
        from groq import AsyncGroq
        self.client = AsyncGroq(api_key=api_key)

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.1,
        max_tokens: Optional[int] = None,
    ) -> str:
        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens:
            kwargs["max_tokens"] = max_tokens

        response = await self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content

    async def chat_completion_json(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "response_format": {"type": "json_object"},
        }
        if max_tokens:
            kwargs["max_tokens"] = max_tokens

        response = await self.client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return self._extract_json_block(content)

    def _extract_json_block(self, text: str) -> Dict[str, Any]:
        """Extract JSON block from text"""
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("Model response does not contain a valid JSON object.")
        return json.loads(text[start: end + 1])


# Provider instance cache
_provider_instance: Optional[LLMProvider] = None


def get_provider() -> LLMProvider:
    """Get LLM provider instance (singleton)"""
    global _provider_instance

    if _provider_instance is not None:
        return _provider_instance

    provider_type = settings.LLM_PROVIDER.lower()

    if provider_type == "groq":
        if not settings.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is required for Groq provider")
        _provider_instance = GroqProvider(api_key=settings.GROQ_API_KEY)

    elif provider_type == "ollama":
        _provider_instance = OllamaProvider(
            host=settings.OLLAMA_HOST,
            api_key=settings.OLLAMA_API_KEY
        )

    else:
        raise ValueError(f"Unknown LLM provider: {provider_type}")

    return _provider_instance


def get_model_name() -> str:
    """Get default model name for current provider"""
    if settings.LLM_PROVIDER.lower() == "groq":
        return settings.GROQ_MODEL
    return settings.OLLAMA_MODEL
