# cmux

A tmux-like session monitor for [Claude Code](https://docs.anthropic.com/en/docs/claude-code). Uses Windows Terminal split panes to give you real-time visibility into what Claude is doing, its task plan, and subagent activity.

```
+----------------------------+----------------------------+
|                            |   TODO Tracker             |
|   Claude Code CLI          |   Task list maintained by  |
|   (interactive session)    |   Claude in real-time      |
|                            +----------------------------+
|                            |   Agent Monitor            |
|                            |   Subagent status, tools,  |
|                            |   duration, token usage    |
+----------------------------+----------------------------+
```

## Requirements

- Windows 11 with [Windows Terminal](https://aka.ms/terminal)
- Python 3.11+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI installed and authenticated

## Install

### As a global tool (recommended)

```bash
uv tool install git+https://github.com/davega-code/CMUX.git
```

This makes `cmux` available as a command anywhere on your system.

To update later:

```bash
uv tool upgrade cmux
```

To uninstall:

```bash
uv tool uninstall cmux
```

### From a local clone

```bash
git clone https://github.com/davega-code/CMUX.git
cd CMUX
uv sync
```

Then run with `uv run cmux` from the cloned directory, or install into your environment:

```bash
uv pip install -e .
```

## Usage

### Launch a monitored session

Navigate to your project directory and run:

```bash
# If installed as a tool
cmux

# If running from the cloned repo
uv run cmux
```

This opens Windows Terminal with three panes:

| Pane | Content |
|------|---------|
| **Left (50%)** | Claude Code CLI — interactive session, ready for your prompts |
| **Top-right** | TODO Tracker — structured task list that Claude maintains as it works |
| **Bottom-right** | Agent Monitor — live table of subagents with status, tools, duration, tokens |

### Specify a different project directory

```bash
cmux --cwd /path/to/your/project
```

### Run individual panes standalone

You can run the tracker TUIs independently (useful for debugging or custom layouts):

```bash
# TODO tracker
cmux todos --cwd /path/to/project --session-id <uuid>

# Agent monitor
cmux agents --cwd /path/to/project --session-id <uuid>
```

## How it works

1. **`cmux`** generates a session UUID and launches `wt.exe` with three split panes
2. **Left pane** runs `claude --session-id <uuid> --append-system-prompt "..."` — the system prompt instructs Claude to maintain a `<uuid>-todo.json` task list file
3. **Top-right pane** watches `<uuid>-todo.json` for changes and renders the task list with status icons (pending, in progress, done)
4. **Bottom-right pane** tails Claude's JSONL session log at `~/.claude/projects/<slug>/<uuid>.jsonl` and extracts subagent lifecycle events (start, progress, complete)

No IPC or background daemons — each pane independently reads its data source.

## TODO file format

Claude maintains a JSON file in the project directory:

```json
{
  "tasks": [
    {"id": 1, "title": "Explore existing codebase", "status": "done"},
    {"id": 2, "title": "Implement parser module", "status": "in_progress"},
    {"id": 3, "title": "Write tests", "status": "pending"}
  ]
}
```

Status values: `pending`, `in_progress`, `done`.

## License

MIT
