from zipfile import ZipFile

from app.exporter import create_download_package


def test_download_package_contains_only_index_and_phase_html(tmp_path):
    phase_dir = tmp_path / "business-purpose"
    phase_dir.mkdir()
    (phase_dir / "raw.md").write_text("# Business Purpose\n\nA summary.", encoding="utf-8")
    (tmp_path / "repository-research.md").write_text("internal research", encoding="utf-8")
    (phase_dir / "phase-research.md").write_text("internal phase research", encoding="utf-8")
    (tmp_path / "agent-output.md").write_text("internal agent output", encoding="utf-8")

    zip_path = create_download_package(tmp_path)

    with ZipFile(zip_path) as archive:
        assert archive.namelist() == ["index.html", "business-purpose.html"]

    assert not (tmp_path / "business-purpose.md").exists()
