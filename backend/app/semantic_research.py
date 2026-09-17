"""LLM-assisted semantic summaries for SDLC reverse engineering.

Deterministic repository intelligence remains the auditable source of repository facts.
Semantic research is an upstream navigation aid, not a substitute for the phase agent.
"""
from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Optional

from openai import AsyncOpenAI

from .repository_intelligence import RepositoryIntelligence

logger = logging.getLogger(__name__)

RESEARCH_VERSION = "4"
MAX_RESEARCH_INPUT_CHARS = 120_000
MAX_PHASE_INPUT_CHARS = 100_000
MAX_REASONING_FALLBACK_CHARS = 60_000
MAX_TOOL_ROUNDS = 2
MAX_TOOL_RESULT_CHARS = 20_000
MAX_COMPLETION_TOKENS = 6_000


def _provider_base_url(provider: str) -> str:
    name = provider.strip().lower()
    if name == "openrouter":
        return "https://openrouter.ai/api/v1"
    if name == "openai":
        return "https://api.openai.com/v1"
    raise ValueError(f"Unsupported provider '{provider}'. Supported providers are: openrouter, openai")


def _clip(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "\n\n[deterministic intelligence truncated for the research pass]"


def _repository_research_input(intelligence: RepositoryIntelligence) -> str:
    sections = [
        "REPOSITORY INTELLIGENCE SCHEMA: " + intelligence.schema_version,
        f"FILES CONSIDERED: {intelligence.file_count}",
        "LANGUAGES: " + str(intelligence.languages),
        "TECHNOLOGIES: " + ", ".join(intelligence.technologies),
        "PACKAGE SCRIPTS: " + str(intelligence.package_scripts),
        "DEPENDENCIES: " + str(intelligence.dependencies),
        "DEV DEPENDENCIES: " + str(intelligence.dev_dependencies),
        "ENVIRONMENT VARIABLES: " + ", ".join(intelligence.env_variables),
        "ENTRY POINTS:\n" + "\n".join(f"- {x}" for x in intelligence.entry_points[:100]),
        "API ROUTES:\n" + "\n".join(f"- {x}" for x in intelligence.api_routes[:180]),
        "PAGES:\n" + "\n".join(f"- {x}" for x in intelligence.page_files[:180]),
        "DOCUMENTATION EXCERPTS:\n" + "\n\n".join(f"### {path}\n{excerpt}" for path, excerpt in list(intelligence.documentation_excerpts.items())[:12]),
        "INTEGRATION FILES:\n" + "\n".join(f"- {x}" for x in intelligence.integration_files[:120]),
        "CONFIG/CI FILES:\n" + "\n".join(f"- {x}" for x in (intelligence.config_files + intelligence.ci_files)[:160]),
        "SOURCE FILES AND SYMBOLS:\n" + "\n".join(
            f"- {item.path} [{item.language or 'unknown'}] imports={item.imports[:12]} exports={item.exports[:12]} symbols={item.symbols}"
            for item in intelligence.source_files[:500]
        ),
        "LOCAL DEPENDENCY EDGES:\n" + "\n".join(
            f"- {edge.source} -> {edge.target}" + (f" ({edge.imported_as})" if edge.imported_as else "")
            for edge in intelligence.dependency_edges[:300]
        ),
        "PARSE SUMMARY: " + str(intelligence.parse_summary),
    ]
    return _clip("\n\n".join(sections), MAX_RESEARCH_INPUT_CHARS)


REPOSITORY_RESEARCH_PROMPT = """You are the repository-level semantic research pass for an SDLC reverse-engineering system.

The program has already scanned the repository and supplied deterministic repository intelligence. Your job is NOT to perform the SDLC analysis. Do NOT produce requirements, architecture, design, a complete domain model, or a holistic documentation brief.

Your only job is to compress the supplied deterministic evidence into a short navigation aid that downstream phase agents can use to reduce unnecessary repository exploration.

Identify only high-value repository-wide signals: likely product/domain, major actors or boundaries, major capability areas, important entities/state relationships, integrations, and material ambiguities. Use representative paths only when they directly support a finding. Do not enumerate the repository, create a research plan, or explain your reasoning.

Target 400-700 words and never exceed 900 words. Prefer a small number of high-signal findings over coverage. Distinguish observed evidence from reasonable inference. Begin directly with the findings.

The output is advisory and must not be treated as authoritative evidence; downstream agents verify material claims against source code."""


PHASE_RESEARCH_PROMPTS = {
    "business-purpose": "Identify only the highest-value signals about product purpose, users, value, major capability areas, and system boundaries. Do not perform the Business Purpose analysis.",
    "scope": "Identify only high-value signals about system boundaries, included application areas, external dependencies, and apparent gaps. Do not perform the Scope analysis.",
    "business-requirements": "Identify only the strongest signals that can help a downstream agent locate actors, goals, business behaviors, workflow/state changes, validation or permission rules, and notable exceptions. Do not reconstruct the business requirements.",
    "features": "Identify only the strongest user-visible capability and workflow signals. Do not produce the feature inventory or complete workflow analysis.",
    "software-requirements": "Identify only high-value signals about externally observable inputs, outputs, operations, validation, state changes, errors, and integrations. Do not write the software requirements.",
    "technology-architecture": "Identify only the strongest structural, runtime, integration, state, configuration, and dependency signals. Do not perform the architecture analysis.",
    "design-pattern": "Identify only recurring structural or dependency patterns strongly suggested by the supplied evidence. Do not perform the design-pattern analysis.",
    "high-level-design": "Identify only high-value subsystem, responsibility, interaction, data-flow, and external-boundary signals. Do not produce the high-level design.",
    "low-level-design": "Identify only high-value module, contract, control-flow, data-transformation, validation, and state signals. Do not produce the low-level design.",
    "implementation-detail": "Identify only high-value implementation mechanisms, algorithms, dependencies, configuration, and error-handling signals. Do not perform the implementation-detail analysis.",
    "testing-harness": "Identify only high-value test organization, fixtures, mocks, integration-boundary, and verification signals. Do not perform the testing-harness analysis.",
    "future-directions": "Identify only evidence-backed gaps, TODO/debt signals, incomplete areas, missing-test signals, and material risks. Do not produce future recommendations or a complete gap analysis.",
}


def _phase_prompt(phase: str) -> str:
    return PHASE_RESEARCH_PROMPTS.get(
        phase,
        "Identify only the highest-value signals relevant to this SDLC phase. Do not perform the phase analysis itself.",
    )


def _extract_message_content(response: Any) -> str | None:
    choices = getattr(response, "choices", None) or []
    if not choices:
        return None
    message = getattr(choices[0], "message", None)
    if message is None:
        return None
    content = getattr(message, "content", None)
    if isinstance(content, str) and content.strip():
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
            else:
                text = getattr(item, "text", None)
                if isinstance(text, str):
                    parts.append(text)
        joined = "".join(parts).strip()
        if joined:
            return joined
    output_text = getattr(message, "output_text", None)
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()
    return None


def _extract_reasoning_fallback(response: Any) -> str | None:
    choices = getattr(response, "choices", None) or []
    if not choices:
        return None
    message = getattr(choices[0], "message", None)
    if message is None:
        return None
    for name in ("reasoning", "reasoning_content", "analysis"):
        value = getattr(message, name, None)
        if isinstance(value, str) and value.strip():
            return _clip(value.strip(), MAX_REASONING_FALLBACK_CHARS)
    return None


def _response_diagnostics(response: Any) -> dict[str, Any]:
    choices = getattr(response, "choices", None) or []
    if not choices:
        return {"choices": 0}
    message = getattr(choices[0], "message", None)
    return {
        "choices": len(choices),
        "finish_reason": getattr(choices[0], "finish_reason", None),
        "message_content_type": type(getattr(message, "content", None)).__name__ if message else None,
        "has_tool_calls": bool(message and getattr(message, "tool_calls", None)),
        "has_reasoning": bool(message and any(getattr(message, name, None) for name in ("reasoning", "reasoning_content", "analysis"))),
    }


def _repository_tools(repository: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    root = repository.resolve()

    def safe_path(relative_path: str) -> Path:
        path = (root / relative_path).resolve()
        if path != root and root not in path.parents:
            raise ValueError("Path must remain inside the repository")
        return path

    def read_file(path: str, max_chars: int = 30000) -> str:
        target = safe_path(path)
        if not target.is_file():
            return "File does not exist or is not a regular file."
        try:
            return target.read_text(encoding="utf-8", errors="replace")[:max_chars]
        except OSError as exc:
            return f"Could not read file: {exc}"

    def search_repository(query: str, max_results: int = 50) -> str:
        if not query.strip():
            return "Query must not be empty."
        matches: list[str] = []
        for item in root.rglob("*"):
            if ".git" in item.parts or not item.is_file():
                continue
            try:
                with item.open("r", encoding="utf-8", errors="replace") as handle:
                    for line_number, line in enumerate(handle, start=1):
                        if query.lower() in line.lower():
                            matches.append(f"{item.relative_to(root)}:{line_number}: {line.rstrip()}")
                            if len(matches) >= max_results:
                                return "\n".join(matches + ["[truncated]"])
            except OSError:
                continue
        return "\n".join(matches) if matches else "No matches found."

    schemas = [
        {"type": "function", "function": {"name": "read_file", "description": "Read one specific repository file for a single important ambiguity.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "max_chars": {"type": "integer", "minimum": 1, "maximum": 30000}}, "required": ["path"]}}},
        {"type": "function", "function": {"name": "search_repository", "description": "Search one precise repository term for a single important ambiguity; never use for broad discovery.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "max_results": {"type": "integer", "minimum": 1, "maximum": 50}}, "required": ["query"]}}},
    ]
    return schemas, {"read_file": read_file, "search_repository": search_repository}


async def _one_shot_chat(*, provider: str, model: str, api_key: str, system_prompt: str, user_prompt: str, repository: Path) -> str:
    client = AsyncOpenAI(base_url=_provider_base_url(provider), api_key=api_key.strip())
    tools, handlers = _repository_tools(repository)
    messages: list[dict[str, Any]] = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
    tool_rounds = 0
    try:
        while True:
            tool_choice = "auto" if tool_rounds < MAX_TOOL_ROUNDS else "none"
            try:
                response = await client.chat.completions.create(model=model.strip(), messages=messages, temperature=0.1, tools=tools, tool_choice=tool_choice, max_tokens=MAX_COMPLETION_TOKENS)
            except Exception as exc:
                logger.exception("SEMANTIC_RESEARCH provider request failed model=%s provider=%s tool_round=%d tool_choice=%s input_chars=%d error_type=%s error=%s", model, provider, tool_rounds, tool_choice, sum(len(str(message.get("content") or "")) for message in messages), type(exc).__name__, exc)
                raise

            diagnostics = _response_diagnostics(response)
            logger.info("SEMANTIC_RESEARCH response model=%s provider=%s tool_round=%d diagnostics=%s", model, provider, tool_rounds, diagnostics)
            choices = getattr(response, "choices", None) or []
            message = getattr(choices[0], "message", None) if choices else None
            tool_calls = getattr(message, "tool_calls", None) or [] if message else []
            if tool_calls and tool_rounds < MAX_TOOL_ROUNDS:
                messages.append({"role": "assistant", "content": getattr(message, "content", None), "tool_calls": [{"id": call.id, "type": "function", "function": {"name": call.function.name, "arguments": call.function.arguments}} for call in tool_calls]})
                for call in tool_calls[:2]:
                    try:
                        arguments = json.loads(call.function.arguments or "{}")
                        result = handlers[call.function.name](**arguments)
                    except Exception as exc:
                        result = f"Tool call failed: {exc}"
                    messages.append({"role": "tool", "tool_call_id": call.id, "content": _clip(str(result), MAX_TOOL_RESULT_CHARS)})
                tool_rounds += 1
                continue

            content = _extract_message_content(response)
            if content:
                return content
            reasoning = _extract_reasoning_fallback(response)
            if reasoning:
                logger.warning("SEMANTIC_RESEARCH model returned reasoning without answer; failing closed")
                raise RuntimeError(f"Research LLM returned reasoning but no final answer. finish_reason={diagnostics.get('finish_reason')}; reasoning_chars={len(reasoning)}")
            raise RuntimeError("Research LLM returned an empty response. " + f"finish_reason={diagnostics.get('finish_reason')}; response_diagnostics={json.dumps(diagnostics, default=str)}")
    finally:
        await client.close()


def run_repository_research(*, intelligence: RepositoryIntelligence, repository: Path, provider: str, model: str, api_key: str) -> str:
    if not api_key or not api_key.strip():
        raise ValueError("An API key is required for repository research")
    return asyncio.run(_one_shot_chat(repository=repository, provider=provider, model=model, api_key=api_key, system_prompt=REPOSITORY_RESEARCH_PROMPT, user_prompt=_repository_research_input(intelligence),))


def run_phase_research(*, phase: str, phase_intelligence: str, repository_research: str, repository: Path, provider: str, model: str, api_key: str) -> str:
    if not api_key or not api_key.strip():
        raise ValueError(f"An API key is required for phase research '{phase}'")
    user_prompt = _clip(
        "REPOSITORY SUMMARY:\n" + repository_research
        + "\n\nDETERMINISTIC PHASE INTELLIGENCE:\n" + phase_intelligence
        + "\n\nPHASE FOCUS:\n" + _phase_prompt(phase)
        + "\n\nProduce a navigation brief, not a phase deliverable. Return at most 10 high-value findings. For each finding, give a short statement and representative evidence path(s) when useful. Include at most 3 material uncertainties. Do not attempt to cover the whole phase, reconstruct all workflows, enumerate files, create a research plan, or explain your reasoning. Prefer omission over speculative or low-value detail. Target 250-450 words and never exceed 600 words. Begin directly with the findings.",
        MAX_PHASE_INPUT_CHARS,
    )
    system_prompt = """You are a narrowly scoped semantic research assistant inside an SDLC reverse-engineering pipeline.

The downstream phase agent is responsible for the actual SDLC analysis and final documentation. You are NOT that agent. Do not perform the phase, do not write the phase deliverable, and do not attempt a holistic understanding of the product.

The program has already supplied a repository-level semantic summary and deterministic phase intelligence. Your sole purpose is to identify a small number of high-value signals that can help the downstream phase agent reach the source evidence faster and avoid unnecessary broad tool calls.

Return only a compact navigation brief. Focus on the strongest evidence-backed signals, representative source locations, and a few material uncertainties. Do not enumerate the repository. Do not create a research or verification plan. Do not describe your reasoning. Do not repeat the supplied material merely to make the answer comprehensive.

If the supplied evidence is sufficient, do not use repository tools. If one specific ambiguity materially affects a finding, you may read one precise file or search one precise term. Never use tools for broad discovery.

A useful answer is intentionally incomplete: it should reduce downstream exploration, not replace it. Target 250-450 words and never exceed 600 words. Begin directly with the findings."""
    return asyncio.run(_one_shot_chat(repository=repository, provider=provider, model=model, api_key=api_key, system_prompt=system_prompt, user_prompt=user_prompt))


def write_research_artifact(path: Path, *, kind: str, phase: Optional[str], content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    header = [f"# {kind.title()} Research Brief", "", f"Research schema: {RESEARCH_VERSION}", f"Phase: {phase or 'repository-wide'}", "", "> This is an upstream reasoning artifact. It is not authoritative evidence or final SDLC documentation. Material claims must be verified against repository source.", ""]
    path.write_text("\n".join(header) + content + "\n", encoding="utf-8")
