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
