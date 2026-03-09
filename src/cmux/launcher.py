import glob
import os
import shutil
import subprocess
import sys
import time
import uuid


def _find_wt() -> str:
    """Find the Windows Terminal executable."""
    wt = shutil.which("wt") or shutil.which("wt.exe")
    if wt:
        return wt

    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if local_app_data:
        alias = os.path.join(local_app_data, "Microsoft", "WindowsApps", "wt.exe")
        if os.path.exists(alias):
            return alias

    program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    matches = glob.glob(os.path.join(
        program_files, "WindowsApps", "Microsoft.WindowsTerminal_*", "wt.exe",
    ))
    if matches:
        return sorted(matches)[-1]

    raise FileNotFoundError(
        "Windows Terminal (wt.exe) not found. "
        "Install it from the Microsoft Store or https://aka.ms/terminal"
    )


def _build_system_prompt(cwd: str, session_id: str) -> str:
    todo_path = f"{cwd}/{session_id}-todo.json".replace("\\", "/")
    return (
        "You are running inside cmux, a session monitor. "
        "IMPORTANT: Maintain a task list as a JSON file at "
        f"{todo_path} -- "
        "Create this file at the START of your session with your planned "
        "approach broken into tasks. Update it as you work. "
        "The JSON must have a top-level tasks array. "
        "Each task object has three fields: "
        "id (integer), title (string), and status (string). "
        "Valid status values are pending, in_progress, or done. "
        "Mark tasks in_progress when you start them, done when complete. "
        "Add new tasks as they emerge. Keep the file valid JSON at all times."
    )


def _find_claude() -> str:
    """Find the Claude Code CLI executable."""
    claude = shutil.which("claude") or shutil.which("claude.exe")
    if claude:
        return claude
    local_bin = os.path.join(os.path.expanduser("~"), ".local", "bin", "claude.exe")
    if os.path.exists(local_bin):
        return local_bin
    raise FileNotFoundError(
        "Claude Code CLI not found. "
        "Install it from https://docs.anthropic.com/en/docs/claude-code"
    )


def launch(cwd: str):
    """Launch Windows Terminal with 3 split panes for cmux.

    Uses wt -w <name> to target a named window. Each pane is added
    via a separate subprocess call, which avoids all argument-parsing
    issues with semicolon-separated commands.
    """
    session_id = str(uuid.uuid4())
    python = sys.executable
    system_prompt = _build_system_prompt(cwd, session_id)
    claude = _find_claude()
    wt = _find_wt()
    window = "cmux"

    # Pane 1: Claude Code CLI (creates the window)
    subprocess.Popen([
        wt, "-w", window,
        "new-tab",
        "--title", "Claude",
        "-d", cwd,
        "cmd", "/k",
        f'"{claude}" --session-id {session_id}'
        f' --append-system-prompt "{system_prompt}"',
    ])

    # Small delay to let the window initialize before adding split panes
    time.sleep(1)

    # Pane 2: TODO tracker (vertical split — right side, 50%)
    subprocess.Popen([
        wt, "-w", window,
        "split-pane",
        "-V", "-s", "0.5",
        "--title", "TODOs",
        "-d", cwd,
        "cmd", "/k",
        f'"{python}" -m cmux todos --cwd "{cwd}" --session-id {session_id}',
    ])

    # Small delay before the next split
    time.sleep(0.5)

    # Pane 3: Agent monitor (horizontal split of right pane — bottom-right, 50%)
    subprocess.Popen([
        wt, "-w", window,
        "split-pane",
        "-H", "-s", "0.5",
        "--title", "Agents",
        "-d", cwd,
        "cmd", "/k",
        f'"{python}" -m cmux agents --cwd "{cwd}" --session-id {session_id}',
    ])
