"""Tests for LLM service routing, retries, and fallback."""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from app.llm import LLMProvider, LLMSettings
from app.llm.clients import FakeLLMClient, LLMClient
from app.llm.contracts import (
    LLMChatMessage,
    LLMChatRequest,
    LLMChatResponse,
    LLMErrorCategory,
    LLMMessageRole,
    LLMResponseFormat,
)
from app.llm.errors import LLMProviderError
from app.llm.service import LLMService


def request(*, provider: LLMProvider | None = None) -> LLMChatRequest:
    return LLMChatRequest(
        messages=(LLMChatMessage(role=LLMMessageRole.USER, content="hello"),),
        provider=provider,
        request_id="service-request",
    )


async def no_sleep(_: float) -> None:
    return None


@dataclass
class ScriptedClient:
    provider: LLMProvider
    model: str = "scripted-model"
    outcomes: list[LLMChatResponse | LLMProviderError] = field(default_factory=list)
    requests: list[LLMChatRequest] = field(default_factory=list)
    ready_checked: int = 0

    def validate_ready(self) -> None:
        self.ready_checked += 1

    async def complete(self, request_value: LLMChatRequest) -> LLMChatResponse:
        self.requests.append(request_value)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, LLMProviderError):
            raise outcome
        return outcome


@dataclass
class CapturingFactory:
    clients: dict[LLMProvider, LLMClient]
    requested_providers: list[LLMProvider] = field(default_factory=list)

    def __call__(
        self,
        settings: LLMSettings,
        *,
        provider: LLMProvider | None = None,
    ) -> LLMClient:
        selected_provider = provider or settings.provider
        self.requested_providers.append(selected_provider)
        return self.clients[selected_provider]


def response(provider: LLMProvider, content: str = "ok") -> LLMChatResponse:
    return LLMChatResponse(
        provider=provider,
        model=f"{provider.value}-model",
        content=content,
        request_id="service-request",
    )


def provider_error(
    category: LLMErrorCategory,
    provider: LLMProvider = LLMProvider.GROQ,
    message: str = "provider failed",
) -> LLMProviderError:
    return LLMProviderError(
        message,
        category=category,
        provider=provider,
        request_id="service-request",
    )


async def test_default_service_uses_fake_provider_safely() -> None:
    service = LLMService(settings=LLMSettings())

    result = await service.complete(request())

    assert result.provider is LLMProvider.FAKE
    assert result.request_id == "fake:service-request"


def test_validate_ready_checks_selected_client() -> None:
    client = ScriptedClient(provider=LLMProvider.FAKE)
    factory = CapturingFactory({LLMProvider.FAKE: client})
    service = LLMService(settings=LLMSettings(), client_factory=factory)

    service.validate_ready()

    assert client.ready_checked == 1
    assert factory.requested_providers == [LLMProvider.FAKE]


async def test_request_provider_overrides_settings_provider() -> None:
    fake_client = FakeLLMClient()
    factory = CapturingFactory({LLMProvider.FAKE: fake_client})
    service = LLMService(
        settings=LLMSettings(provider=LLMProvider.GROQ),
        client_factory=factory,
    )

    result = await service.complete(request(provider=LLMProvider.FAKE))

    assert result.provider is LLMProvider.FAKE
    assert factory.requested_providers == [LLMProvider.FAKE]


async def test_complete_json_forces_structured_json_request() -> None:
    client = ScriptedClient(
        provider=LLMProvider.FAKE,
        outcomes=[response(LLMProvider.FAKE, content='{"ok":true}')],
    )
    factory = CapturingFactory({LLMProvider.FAKE: client})
    service = LLMService(settings=LLMSettings(), client_factory=factory)

    await service.complete_json(request())

    assert client.requests[0].response_format is LLMResponseFormat.JSON_OBJECT
    assert client.requests[0].structured_json is True


@pytest.mark.parametrize(
    "category",
    [
        LLMErrorCategory.TIMEOUT,
        LLMErrorCategory.UNAVAILABLE,
        LLMErrorCategory.RATE_LIMIT,
    ],
)
async def test_service_retries_transient_errors(category: LLMErrorCategory) -> None:
    client = ScriptedClient(
        provider=LLMProvider.GROQ,
        outcomes=[
            provider_error(category),
            provider_error(category),
            response(LLMProvider.GROQ),
        ],
    )
    factory = CapturingFactory({LLMProvider.GROQ: client})
    service = LLMService(
        settings=LLMSettings(
            provider=LLMProvider.GROQ,
            max_retries=2,
        ),
        client_factory=factory,
        sleep=no_sleep,
    )

    result = await service.complete(request())

    assert result.provider is LLMProvider.GROQ
    assert len(client.requests) == 3


async def test_service_stops_after_configured_retry_limit() -> None:
    client = ScriptedClient(
        provider=LLMProvider.GROQ,
        outcomes=[
            provider_error(LLMErrorCategory.TIMEOUT),
            provider_error(LLMErrorCategory.TIMEOUT),
        ],
    )
    service = LLMService(
        settings=LLMSettings(provider=LLMProvider.GROQ, max_retries=1),
        client_factory=CapturingFactory({LLMProvider.GROQ: client}),
        sleep=no_sleep,
    )

    with pytest.raises(LLMProviderError) as exc_info:
        await service.complete(request())

    assert exc_info.value.category is LLMErrorCategory.TIMEOUT
    assert len(client.requests) == 2


@pytest.mark.parametrize(
    "category",
    [
        LLMErrorCategory.CONFIGURATION,
        LLMErrorCategory.AUTHENTICATION,
        LLMErrorCategory.INVALID_RESPONSE,
        LLMErrorCategory.SAFETY,
    ],
)
async def test_service_does_not_retry_non_transient_errors(
    category: LLMErrorCategory,
) -> None:
    client = ScriptedClient(
        provider=LLMProvider.GROQ,
        outcomes=[provider_error(category)],
    )
    service = LLMService(
        settings=LLMSettings(provider=LLMProvider.GROQ, max_retries=3),
        client_factory=CapturingFactory({LLMProvider.GROQ: client}),
        sleep=no_sleep,
    )

    with pytest.raises(LLMProviderError) as exc_info:
        await service.complete(request())

    assert exc_info.value.category is category
    assert len(client.requests) == 1


async def test_fallback_is_disabled_by_default() -> None:
    primary = ScriptedClient(
        provider=LLMProvider.GROQ,
        outcomes=[provider_error(LLMErrorCategory.TIMEOUT)],
    )
    fallback = ScriptedClient(
        provider=LLMProvider.FAKE,
        outcomes=[response(LLMProvider.FAKE)],
    )
    service = LLMService(
        settings=LLMSettings(
            provider=LLMProvider.GROQ,
            max_retries=0,
            fallback_enabled=False,
        ),
        client_factory=CapturingFactory(
            {LLMProvider.GROQ: primary, LLMProvider.FAKE: fallback},
        ),
        sleep=no_sleep,
    )

    with pytest.raises(LLMProviderError):
        await service.complete(request())

    assert len(primary.requests) == 1
    assert len(fallback.requests) == 0


async def test_enabled_fallback_handles_transient_failure() -> None:
    primary = ScriptedClient(
        provider=LLMProvider.GROQ,
        outcomes=[provider_error(LLMErrorCategory.UNAVAILABLE)],
    )
    fallback = ScriptedClient(
        provider=LLMProvider.FAKE,
        outcomes=[response(LLMProvider.FAKE)],
    )
    service = LLMService(
        settings=LLMSettings(
            provider=LLMProvider.GROQ,
            max_retries=0,
            fallback_enabled=True,
            fallback_provider=LLMProvider.FAKE,
        ),
        client_factory=CapturingFactory(
            {LLMProvider.GROQ: primary, LLMProvider.FAKE: fallback},
        ),
        sleep=no_sleep,
    )

    result = await service.complete(request())

    assert result.provider is LLMProvider.FAKE
    assert result.metadata["fallback_used"] is True
    assert result.metadata["fallback_from_provider"] == "groq"
    assert result.metadata["fallback_error_category"] == "unavailable"
    assert fallback.requests[0].provider is LLMProvider.FAKE


async def test_fallback_does_not_hide_configuration_or_auth_errors() -> None:
    primary = ScriptedClient(
        provider=LLMProvider.GROQ,
        outcomes=[provider_error(LLMErrorCategory.AUTHENTICATION)],
    )
    fallback = ScriptedClient(
        provider=LLMProvider.FAKE,
        outcomes=[response(LLMProvider.FAKE)],
    )
    service = LLMService(
        settings=LLMSettings(
            provider=LLMProvider.GROQ,
            max_retries=0,
            fallback_enabled=True,
            fallback_provider=LLMProvider.FAKE,
        ),
        client_factory=CapturingFactory(
            {LLMProvider.GROQ: primary, LLMProvider.FAKE: fallback},
        ),
        sleep=no_sleep,
    )

    with pytest.raises(LLMProviderError) as exc_info:
        await service.complete(request())

    assert exc_info.value.category is LLMErrorCategory.AUTHENTICATION
    assert len(fallback.requests) == 0


async def test_missing_real_provider_key_fails_safely_without_secret_leak() -> None:
    service = LLMService(
        settings=LLMSettings(
            provider=LLMProvider.GROQ,
            groq_model="llama",
            fallback_enabled=True,
            fallback_provider=LLMProvider.FAKE,
        ),
    )

    with pytest.raises(LLMProviderError) as exc_info:
        await service.complete(request())

    assert exc_info.value.category is LLMErrorCategory.CONFIGURATION
    assert "secret" not in str(exc_info.value).lower()
