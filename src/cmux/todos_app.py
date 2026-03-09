import asyncio
import json
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Footer, Header, Static
from textual import work

from .session import get_todo_path

STATUS_ICONS = {
    "done": "[green]✓[/]",
    "in_progress": "[yellow]▶[/]",
    "pending": "[dim]○[/]",
}


class TodosApp(App):
    CSS_PATH = "css/todos.tcss"
    TITLE = "cmux - TODO Tracker"

    def __init__(self, cwd: str, session_id: str, **kwargs):
        super().__init__(**kwargs)
        self.cwd = cwd
        self.session_id = session_id
        self.todo_path = get_todo_path(cwd, session_id)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static(
            f"Session: [bold]{self.session_id[:8]}...[/]",
            id="session-header",
        )
        yield Static(
            "Waiting for Claude to initialize tasks...",
            id="waiting-message",
        )
        yield VerticalScroll(id="task-list")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#task-list").display = False
        self.watch_todo_file()

    @work(exclusive=True, thread=False)
    async def watch_todo_file(self) -> None:
        # Wait for file to exist
        while not self.todo_path.exists():
            await asyncio.sleep(0.5)

        self.query_one("#waiting-message").display = False
        self.query_one("#task-list").display = True
        self._render_tasks()

        # Watch for changes
        import watchfiles

        async for _changes in watchfiles.awatch(
            self.todo_path.parent,
            watch_filter=lambda change, path: str(path) == str(self.todo_path),
        ):
            self._render_tasks()

    def _render_tasks(self) -> None:
        try:
            data = json.loads(self.todo_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return

        tasks = data.get("tasks", [])
        container = self.query_one("#task-list")
        container.remove_children()

        for task in tasks:
            status = task.get("status", "pending")
            title = task.get("title", "Untitled")
            icon = STATUS_ICONS.get(status, "?")

            if status == "done":
                markup = f"{icon} [strike]{title}[/strike]"
                css_class = "task-done"
            elif status == "in_progress":
                markup = f"{icon} [bold]{title}[/bold]"
                css_class = "task-in-progress"
            else:
                markup = f"{icon} {title}"
                css_class = "task-pending"

            widget = Static(markup, classes=f"task-row {css_class}")
            container.mount(widget)
