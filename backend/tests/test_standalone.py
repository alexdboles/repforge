"""Portable configuration and provider tests; no paid requests."""
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
import pytest
from fastapi import HTTPException, Response
from lib.auth import cookie_policy, clear_session
from lib.llm import DirectChat, LlmUnavailable, _chat, _send


def test_cookie_policy(monkeypatch):
    monkeypatch.delenv('COOKIE_SECURE', raising=False)
    monkeypatch.delenv('COOKIE_SAMESITE', raising=False)
    assert cookie_policy() == {'secure': True, 'samesite': 'none'}
    monkeypatch.setenv('COOKIE_SECURE', 'false')
    with pytest.raises(HTTPException):
        cookie_policy()
    monkeypatch.setenv('COOKIE_SAMESITE', 'lax')
    response = Response()
    clear_session(response)
    assert 'SameSite=lax' in response.headers['set-cookie']
    assert 'Secure' not in response.headers['set-cookie']
    assert 'HttpOnly' in response.headers['set-cookie']


async def test_direct_provider_uses_instructions_and_budget(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'mock-provider-not-a-real-key')
    monkeypatch.setenv('OPENAI_MODEL', 'fixture-model')
    chat = _chat('fixture', 'system rules')
    assert isinstance(chat, DirectChat)
    client = AsyncMock()
    client.responses.create.return_value = SimpleNamespace(status='completed', output_text='hello')
    with patch('lib.llm.AsyncOpenAI') as sdk, patch('lib.llm.provider_budget', AsyncMock()) as budget:
        sdk.return_value.__aenter__ = AsyncMock(return_value=client)
        sdk.return_value.__aexit__ = AsyncMock(return_value=None)
        assert await _send(chat, 'reply') == 'hello'
        budget.assert_awaited_once_with('llm')
        client.responses.create.assert_awaited_once_with(model='fixture-model', instructions='system rules', input='reply', store=False)
        assert sdk.call_args.kwargs['max_retries'] == 0
        client.responses.create.return_value = SimpleNamespace(status='incomplete', output_text='partial')
        with pytest.raises(LlmUnavailable):
            await _send(chat, 'reply')
