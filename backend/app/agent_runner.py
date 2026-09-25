    if tools_manifest:
        lines.append("tools:")
        for group, names in tools_manifest.items():
            lines.append(f"  {group}: {', '.join(names)}")
    else:
        lines.append("tools: none")
    lines.extend([
        "Runtime skill resources are relative to the supplied skill resource root; use read_resource with the supplied relative path.",
        "Use list_resources when you need to discover the complete runtime resource inventory.",
        "Use repository read_file/search/list tools only for the target repository.",
        "Use output-content tools only for workflow artifacts from the current analysis run.",
        "Do not construct host filesystem paths or use repository tools to access runtime resources.",
    ])
    return "\n".join(lines)

def _build_tools(phase: str, repository: Path, output_run_dir: Path):
    root = repository.resolve()
    output_root = output_run_dir.resolve()
    skill_dir = (SKILLS_SOURCE / phase).resolve()

    def safe_path(relative_path: str) -> Path:
        candidate = (root / relative_path).resolve()
        if root != candidate and root not in candidate.parents:
            raise ValueError("Path escapes repository root.")
        return candidate

    @function_tool
    def list_resources() -> str:
        """List files available in the runtime-owned resource directory for the current phase."""
        if not skill_dir.is_dir():
            return "No runtime resources are available."
        files = sorted(
            path.relative_to(skill_dir).as_posix()
            for path in skill_dir.rglob("*")
            if path.is_file()
        )
        return "\n".join(files) if files else "No runtime resources are available."

    @function_tool
    def read_resource(path: str, max_chars: int = 30000) -> str:
        """Read a file from the runtime-owned resource directory for the current phase."""
        candidate = (skill_dir / path).resolve()
        if skill_dir != candidate and skill_dir not in candidate.parents:
            return "Invalid resource path: access outside the current phase resource directory is not allowed."
        if not candidate.is_file():
            return "Runtime resource does not exist or is not a regular file."
        try:
            return candidate.read_text(encoding="utf-8", errors="replace")[:max_chars]
        except OSError as exc:
            return f"Could not read runtime resource: {exc}"

    @function_tool
    def list_previous_phase_outputs() -> str:
        """
        List files produced by previous SDLC phases for the current analysis run.
        Paths are relative to the current run's output-content directory.
        """
        if not output_root.exists():
            return "No previous phase outputs are available."

        if not output_root.is_dir():
            return "The current run output path is not a directory."

        files = sorted(
            path.relative_to(output_root).as_posix()
            for path in output_root.rglob("*")
            if path.is_file() and path.name != "run-state.json"
        )

        if not files:
            return "No previous phase outputs are available."

        return "\n".join(files)

    @function_tool
    def read_previous_phase_output(filename: str) -> str:
        """
        Read a specific previous-phase output file from the current analysis run.
        The filename must be one returned by list_previous_phase_outputs().
        """
        file_path = (output_root / filename).resolve()

        # Prevent path traversal outside the current run output directory.
        if output_root != file_path and output_root not in file_path.parents:
            return "Invalid filename: access outside the current run output directory is not allowed."

        if not file_path.exists():
            return f"Previous phase output not found: {filename}"

        if not file_path.is_file():
            return f"Not a file: {filename}"

        try:
            return file_path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            return f"Unable to read {filename}: {exc}"
    @function_tool
    def list_files(path: str = ".", max_entries: int = 300) -> str:
        """List repository files and directories recursively, without modifying anything."""
        target = safe_path(path)
        if not target.exists():
            return "Path does not exist."
        entries = []
        for item in target.rglob("*"):
            if ".git" in item.parts:
                continue
            entries.append(str(item.relative_to(root)))
            if len(entries) >= max_entries:
                entries.append("[truncated]")
                break
        return "\n".join(entries)

    @function_tool
    def read_file(path: str, max_chars: int = 30000) -> str:
        """Read a UTF-8 text file for conditional follow-up evidence not already present in deterministic intelligence."""
        target = safe_path(path)
        if not target.is_file():
            return "File does not exist or is not a regular file."
        try:
            return target.read_text(encoding="utf-8", errors="replace")[:max_chars]
        except OSError as exc:
            return f"Could not read file: {exc}"

    @function_tool
    def search_repository(query: str, max_results: int = 100) -> str:
        """Search repository text for conditional follow-up evidence not already present in deterministic intelligence."""
        matches = []
        for item in root.rglob("*"):
            if ".git" in item.parts or not item.is_file():
                continue
            try:
                with item.open("r", encoding="utf-8", errors="replace") as handle:
                    for line_number, line in enumerate(handle, start=1):
                        if query.lower() in line.lower():