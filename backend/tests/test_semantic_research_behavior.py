import pytest

from app.cancellable_research import _research_fallback
from app.semantic_research import _phase_prompt


def test_phase_research_failure_is_not_converted_to_fallback():
    with pytest.raises(RuntimeError, match="Semantic research failed for phase 'business-requirements'"):
        _research_fallback(
            "phase",
            {"phase": "business-requirements"},
            "RuntimeError",
            "research model returned no final answer",
        )


def test_phase_research_prompt_is_navigation_only():
    prompt = _phase_prompt("business-requirements").lower()

    assert "highest-value signals" in prompt
    assert "do not reconstruct the business requirements" in prompt
