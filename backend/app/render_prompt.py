"""
Prompt contract for the presentation-stage LLM.

The analysis stage produces the content.
The rendering stage receives a phase-specific template and the completed
phase content, then produces the document in that template's format.
"""

from textwrap import dedent


RENDER_SYSTEM_PROMPT = dedent(
    """
    You are a document writer.

    You need to produce the requested software reverse-engineering
    documentation using the provided document template.

    Use the template as the format and structure for the document.

    Use the provided phase content as the source of the document's content.

    Do not invent facts, information, findings, requirements, or conclusions.

    If the phase content does not contain information for a section of the
    template, skip that section rather than inventing content.

    Preserve the meaning and factual content of the phase content.

    Return only the completed document.
    """
).strip()


def build_render_prompt(phase: str, analysis: str, template: str) -> tuple[str, str]:
    """Build the renderer prompts for a single completed phase."""
    phase_name = phase.replace("-", " ").strip().title()

    if not template or not template.strip():
        raise ValueError(f"No render template was provided for phase '{phase}'.")

    user_prompt = dedent(
        f"""
        You need to produce a {phase_name} documentation in the format
        specified by the template below.

        Start with the template and create the document according to its
        structure, headings, ordering, and formatting.

        You can take the content of the document from the provided
        {phase}.md content below.

        Do not invent content.

        If information required by a template section is not available in
        the {phase}.md content, skip that section.

        Do not add information from your own knowledge.

        --- BEGIN TEMPLATE ---
        {template}
        --- END TEMPLATE ---

        --- BEGIN {phase.upper()}.MD CONTENT ---
        {analysis}
        --- END {phase.upper()}.MD CONTENT ---

        Produce only the completed {phase_name} document.
        """
    ).strip()

    return RENDER_SYSTEM_PROMPT, user_prompt
