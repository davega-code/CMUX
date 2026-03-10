from pathlib import Path

CLAUDE_PROJECTS_DIR = Path.home() / ".claude" / "projects"


def cwd_to_project_slug(cwd: str) -> str:
    """Convert a working directory to a Claude project slug.

    Example: C:\\Repos\\Tools\\cmux -> C--Repos-Tools-cmux
    """
    return cwd.replace(":", "-").replace("\\", "-").replace("/", "-")


def get_project_dir(cwd: str) -> Path:
    """Get the Claude projects directory for a given working directory."""
    return CLAUDE_PROJECTS_DIR / cwd_to_project_slug(cwd)


def get_jsonl_path(cwd: str, session_id: str) -> Path:
    """Get the JSONL session log path for a given session."""
    return get_project_dir(cwd) / f"{session_id}.jsonl"

