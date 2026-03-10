# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is CMUX

A tmux-like session monitor for Claude Code on Windows. Launches Windows Terminal with three
split panes: the Claude Code CLI (left), a TODO tracker TUI (top-right), and a subagent monitor
TUI (bottom-right). No IPC or daemons — both TUI panes read from the same JSONL session log
that Claude Code writes natively.

## Development Commands

```bash
# Install dependencies
uv sync

# Run from source
uv run cmux

# Run individual TUI apps (for development/debugging)
uv run cmux todos --cwd <path> --session-id <uuid>
uv run cmux agents --cwd <path> --session-id <uuid>

# Install as editable
uv pip install -e .
```

There are no tests, linter, or formatter configured yet.

## Architecture

**Entry point**: `cmux.cli:main` — a Click group with two subcommands (`todos`, `agents`).
Invoking `cmux` without a subcommand calls `launcher.launch()`.

**Data flow** — single JSONL source, no IPC:

Both TUI panes tail `~/.claude/projects/<slug>/<session-id>.jsonl` via `JsonlParser`.

1. **TODO channel**: `JsonlParser` scans `assistant` lines for `TaskCreate`/`TaskUpdate` tool
   calls and `user` lines for their results. `TodosApp` renders the accumulated task list with
   status icons (pending `○`, in-progress `▶`, completed `✓`). The `active_form` field is shown
   as the label for in-progress tasks.

2. **Agent channel**: `JsonlParser` scans `progress` lines for `agent_progress` events, emitting
   `AgentStartEvent`, `AgentProgressEvent`, and `AgentCompleteEvent`. `AgentsApp` renders them
   in a `DataTable` with live elapsed durations.

**Key modules** (`src/cmux/`):

| Module | Role |
|--------|------|
| `launcher.py` | Finds `wt.exe` and `claude`, spawns 3 WT panes with sequential `subprocess.Popen` calls |
| `parser.py` | `JsonlParser` — async generator that tails the JSONL log, yields typed event dataclasses |
| `events.py` | Dataclasses for session info, agent lifecycle events, `TodoItem`/`TodoUpdateEvent`, and `AgentState` |
| `session.py` | Path helpers: converts CWD to Claude's project slug, resolves JSONL path |
| `todos_app.py` | Textual app consuming `JsonlParser` todo events, renders task list with status icons |
| `agents_app.py` | Textual app consuming `JsonlParser` events, renders agent table with live durations |
| `css/` | Textual CSS stylesheets for both TUI apps |

**Windows Terminal pane layout**: The launcher creates panes via separate `subprocess.Popen` calls
to `wt.exe -w cmux` with `time.sleep()` delays between them (not semicolon-chained commands) to
avoid argument-parsing issues.

## Dependencies

- **textual** — TUI framework for the two monitor apps
- **click** — CLI argument parsing
- **watchfiles** — async file change notifications (used inside `JsonlParser`)
- **hatchling** — build backend

## Conventions

- Python 3.11+ (uses `X | Y` union syntax)
- Package lives in `src/cmux/` with hatchling build
- Session IDs are UUIDs generated per launch
- Claude's project slug format: `C:\Repos\Foo` → `C--Repos-Foo` (colons to `-`, slashes to `-`)
