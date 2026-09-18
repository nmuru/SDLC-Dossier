import pytest

from app.analyzer import _phase_failure
from app.cancellable_research import _research_failure
from app.semantic_research import _phase_prompt


def test_repository_research_failure_is_not_converted_to_fallback():
    with pytest.raises(RuntimeError, match="Repository semantic research failed"):
        raise _research_failure(
            "repository",
            {},
            "RuntimeError",
            "research model returned no final answer",
        )


def test_phase_research_failure_is_not_converted_to_fallback():
    with pytest.raises(RuntimeError, match="Semantic research failed for phase 'business-requirements'"):
        raise _research_failure(
            "phase",
            {"phase": "business-requirements"},
            "RuntimeError",
            "research model returned no final answer",
        )


def test_phase_research_prompt_retains_rich_summary_objective():
    prompt = _phase_prompt("business-requirements").lower()

    assert "summarize the business behavior" in prompt
    assert "actors" in prompt
    assert "workflows" in prompt
    assert "do not propose files to inspect" in prompt


def test_phase_failure_explains_max_turns_and_recovery():
    failure = _phase_failure("business-requirements", "Business Requirements", RuntimeError("max_turns exceeded"))

    assert failure["error"] == (
        "Max turns exceeded for phase 'Business Requirements'. "
        "Retry the phase or try a different model."
    )


def test_semantic_research_disables_tool_calls(monkeypatch, tmp_path):
    import asyncio
    from types import SimpleNamespace
    import app.semantic_research as semantic_research

    captured = {}

    class FakeCompletions:
        async def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(
                choices=[SimpleNamespace(
                    finish_reason="stop",
                    message=SimpleNamespace(content="final research brief", tool_calls=None),
                )]
            )

    class FakeClient:
        def __init__(self, *args, **kwargs):
            self.chat = SimpleNamespace(completions=FakeCompletions())

        async def close(self):
            pass

    monkeypatch.setattr(semantic_research, "AsyncOpenAI", FakeClient)
    result = asyncio.run(
        semantic_research._one_shot_chat(
            provider="openrouter",
            model="test-model",
            api_key="test-key",
            system_prompt="system",
            user_prompt="user",
            repository=tmp_path,
        )
    )

    assert result == "final research brief"
    assert captured["tool_choice"] == "none"
    assert "tools" not in captured
