"""Provider-independent LLM service with retry and optional fallback."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from app.llm.clients import LLMClient
from app.llm.contracts import (
    LLMChatRequest,
    LLMChatResponse,
    LLMErrorCategory,
    LLMProvider,
    LLMResponseFormat,
)
from app.llm.errors import LLMProviderError
from app.llm.factory import LLMClientFactory, SettingsLLMClientFactory
from app.llm.retry import is_fallback_eligible_llm_error, is_retryable_llm_error
from app.llm.settings import LLMSettings

SleepCallable = Callable[[float], Awaitable[None]]


class LLMService:
    """Stable service API for future runtime nodes and agents."""

    def __init__(
        self,
        *,
        settings: LLMSettings,
        client_factory: LLMClientFactory | None = None,
        sleep: SleepCallable | None = None,
    ) -> None:
        self._settings = settings
        self._client_factory = client_factory or SettingsLLMClientFactory()
        self._sleep = sleep or asyncio.sleep

    @property
    def settings(self) -> LLMSettings:
        """Return the immutable LLM settings used by this service."""
        return self._settings

    def validate_ready(self) -> None:
        """Validate the selected primary provider configuration."""
        self._create_client(self._settings.provider).validate_ready()

    async def complete(self, request: LLMChatRequest) -> LLMChatResponse:
        """Complete a chat request with bounded retries and optional fallback."""
        provider = request.provider or self._settings.provider
        primary_client = self._create_client(provider)
        try:
            return await self._complete_with_retries(primary_client, request)
        except LLMProviderError as exc:
            if not self._should_use_fallback(exc, provider):
                raise
            return await self._complete_with_fallback(
                request=request,
                failed_provider=provider,
                failure=exc,
            )
        except Exception as exc:
            raise LLMProviderError(
                "llm service encountered an unexpected provider error",
                category=LLMErrorCategory.UNKNOWN,
                provider=provider,
                request_id=request.request_id,
            ) from exc

    async def complete_json(self, request: LLMChatRequest) -> LLMChatResponse:
        """Complete a request while requiring JSON-object response mode."""
        json_request = request.model_copy(
            update={
                "response_format": LLMResponseFormat.JSON_OBJECT,
                "structured_json": True,
            },
        )
        return await self.complete(json_request)

    def _create_client(self, provider: LLMProvider) -> LLMClient:
        return self._client_factory(self._settings, provider=provider)

    async def _complete_with_retries(
        self,
        client: LLMClient,
        request: LLMChatRequest,
    ) -> LLMChatResponse:
        attempts_remaining = self._settings.max_retries + 1
        last_error: LLMProviderError | None = None
        while attempts_remaining > 0:
            try:
                return await client.complete(request)
            except LLMProviderError as exc:
                last_error = exc
                attempts_remaining -= 1
                if attempts_remaining <= 0 or not is_retryable_llm_error(exc.category):
                    raise
                await self._sleep(0)
        if last_error is not None:
            raise last_error
        raise LLMProviderError(
            "llm service exhausted retry attempts",
            category=LLMErrorCategory.UNKNOWN,
            provider=client.provider,
            request_id=request.request_id,
        )

    def _should_use_fallback(
        self,
        failure: LLMProviderError,
        failed_provider: LLMProvider,
    ) -> bool:
        if not self._settings.fallback_enabled:
            return False
        if self._settings.fallback_provider is failed_provider:
            return False
        return is_fallback_eligible_llm_error(failure.category)

    async def _complete_with_fallback(
        self,
        *,
        request: LLMChatRequest,
        failed_provider: LLMProvider,
        failure: LLMProviderError,
    ) -> LLMChatResponse:
        fallback_provider = self._settings.fallback_provider
        fallback_client = self._create_client(fallback_provider)
        fallback_response = await fallback_client.complete(
            request.model_copy(update={"provider": fallback_provider}),
        )
        metadata: dict[str, Any] = {
            **fallback_response.metadata,
            "fallback_used": True,
            "fallback_from_provider": failed_provider.value,
            "fallback_error_category": failure.category.value,
        }
        return fallback_response.model_copy(update={"metadata": metadata})
