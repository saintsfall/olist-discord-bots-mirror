"""
    Testes de import e smoke tests.
"""


def test_handle_events_import():
    """Garante que handle_events e set_events podem ser importados."""
    from bot_events.handle_events import set_events

    assert callable(set_events)


def test_handlers_import():
    """Garante que os handlers podem ser importados."""
    from bot_events.handlers import (
        handle_n8n_webhook_response,
        handle_with_n8n,
        handle_with_orchestrator,
    )

    assert callable(handle_with_orchestrator)
    assert callable(handle_with_n8n)
    assert callable(handle_n8n_webhook_response)
