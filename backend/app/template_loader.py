"""Load phase-specific document templates for presentation rendering."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILLS_SOURCE = PROJECT_ROOT / ".agents" / "skills"
TEMPLATE_FILENAME = "OUTPUT_TEMPLATE.md"


def load_phase_template(phase: str) -> str:
    """Load the presentation template belonging to a phase's skill.

    Templates live beside each phase's SKILL.md so the analysis methodology
    and presentation structure remain phase-specific and independently
    maintainable.
    """
    phase_name = (phase or "").strip()
    if not phase_name:
        raise ValueError("phase cannot be empty")

    template_path = SKILLS_SOURCE / phase_name / TEMPLATE_FILENAME
    if not template_path.is_file():
        raise FileNotFoundError(
            f"No {TEMPLATE_FILENAME} found for phase '{phase_name}' at "
            f"'{template_path}'."
        )

    template = template_path.read_text(encoding="utf-8", errors="replace")
    if not template.strip():
        raise ValueError(
            f"{TEMPLATE_FILENAME} is empty for phase '{phase_name}' at "
            f"'{template_path}'."
        )

    return template
