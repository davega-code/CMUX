from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Static
from textual import work

from .events import SessionInfo, TodoUpdateEvent
from .parser import JsonlParser
from .session import get_jsonl_path

STATUS_ICONS = {
    "completed": "[green]✓[/green]",
    "in_progress": "[yellow]▶[/yellow]",
    "pending": "[dim]○[/dim]",
}


class TodosApp(App):
    CSS_PATH = "css/todos.tcss"
    TITLE = "cmux - TODO Tracker"

    def __init__(self, cwd: str, session_id: str, **kwargs):
        super().__init__(**kwargs)
        self.cwd = cwd
        self.session_id = session_id
        self.jsonl_path = get_jsonl_path(cwd, session_id)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static(
            f"Session: [bold]{self.session_id[:8]}...[/bold]  "
            f"Watching: [dim]{self.jsonl_path}[/dim]",
            id="session-header",
        )
        yield Static(
            "Waiting for Claude to initialize tasks...",
            id="task-list",
        )
        yield Footer()

    def on_mount(self) -> None:
        self.tail_session()

    @work(exclusive=True, thread=False)
    async def tail_session(self) -> None:
        parser = JsonlParser(self.jsonl_path)

        async for event in parser.tail_events():
            if isinstance(event, TodoUpdateEvent):
                self._render_tasks(event)

    def _render_tasks(self, event: TodoUpdateEvent) -> None:
        lines = []
        for task in event.tasks:
            icon = STATUS_ICONS.get(task.status, "?")
            if task.status == "in_progress":
                label = task.active_form or task.subject
                lines.append(f"{icon} [bold]{label}[/bold]")
            elif task.status == "completed":
                lines.append(f"{icon} [dim strike]{task.subject}[/dim strike]")
            else:
                lines.append(f"{icon} [dim]{task.subject}[/dim]")

        self.query_one("#task-list", Static).update("\n".join(lines))
