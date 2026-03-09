import subprocess
import sys
import uuid


def _build_system_prompt(cwd: str, session_id: str) -> str:
    todo_path = f"{cwd}\\{session_id}-todo.json".replace("\\", "/")
    return (
        "You are running inside cmux, a session monitor. "
        "IMPORTANT: Maintain a task list file at "
        f"`{todo_path}`. "
        "Create this file at the START of your session with your planned "
        "approach broken into tasks. Update it as you work. Format: "
        '{"tasks": [{"id": 1, "title": "...", "status": "pending|in_progress|done"}]} '
        "Mark tasks in_progress when you start them, done when complete. "
        "Add new tasks as they emerge. Keep the file valid JSON at all times."
    )


def launch(cwd: str):
    """Launch Windows Terminal with 3 split panes for cmux."""
    session_id = str(uuid.uuid4())
    python = sys.executable
    system_prompt = _build_system_prompt(cwd, session_id)

    cmd = [
        "wt.exe",
        "--title", "cmux",
        # Pane 1 (left): Claude Code CLI
        "new-tab",
        "--title", "Claude",
        "-d", cwd,
        "claude",
        "--session-id", session_id,
        "--append-system-prompt", system_prompt,
        ";",
        # Pane 2 (top-right): TODO tracker
        "split-pane", "-V", "-s", "0.5",
        "--title", "TODOs",
        "-d", cwd,
        python, "-m", "cmux", "todos",
        "--cwd", cwd,
        "--session-id", session_id,
        ";",
        # Pane 3 (bottom-right): Agent monitor
        "split-pane", "-H", "-s", "0.5",
        "--title", "Agents",
        "-d", cwd,
        python, "-m", "cmux", "agents",
        "--cwd", cwd,
        "--session-id", session_id,
        ";",
        # Return focus to Claude pane
        "move-focus", "--direction", "left",
    ]

    subprocess.Popen(cmd)
