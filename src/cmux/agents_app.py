from datetime import datetime, timezone

from textual.app import App, ComposeResult
from textual.widgets import DataTable, Footer, Header, Static
from textual import work

from .events import (
    AgentCompleteEvent,
    AgentProgressEvent,
    AgentStartEvent,
    AgentState,
    SessionInfo,
)
from .parser import JsonlParser
from .session import get_jsonl_path


class AgentsApp(App):
    CSS_PATH = "css/agents.tcss"
    TITLE = "cmux - Agent Monitor"

    def __init__(self, cwd: str, session_id: str, **kwargs):
        super().__init__(**kwargs)
        self.cwd = cwd
        self.session_id = session_id
        self.jsonl_path = get_jsonl_path(cwd, session_id)
        self.agents: dict[str, AgentState] = {}

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static(
            "Agents: [bold]0[/] total",
            id="agent-summary",
        )
        yield Static(
            "Waiting for session to start...",
            id="waiting-message",
        )
        yield DataTable(id="agent-table")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#agent-table", DataTable)
        table.add_columns("ID", "Status", "Description", "Tool", "Tools", "Duration", "Tokens")
        table.cursor_type = "row"
        table.display = False
        self.set_interval(1.0, self._refresh_durations)
        self.tail_session()

    @work(exclusive=True, thread=False)
    async def tail_session(self) -> None:
        parser = JsonlParser(self.jsonl_path)

        async for event in parser.tail_events():
            if isinstance(event, SessionInfo):
                self.query_one("#waiting-message").display = False
                self.query_one("#agent-table", DataTable).display = True

            elif isinstance(event, AgentStartEvent):
                self.agents[event.agent_id] = AgentState(
                    agent_id=event.agent_id,
                    prompt=event.prompt[:80],
                    status="running",
                    started_at=event.timestamp,
                )
                self._rebuild_table()

            elif isinstance(event, AgentProgressEvent):
                agent = self.agents.get(event.agent_id)
                if agent:
                    agent.current_tool = event.tool_name
                    if event.tool_name:
                        agent.tool_count += 1
                    self._rebuild_table()

            elif isinstance(event, AgentCompleteEvent):
                agent = self.agents.get(event.agent_id)
                if agent:
                    agent.status = event.status
                    agent.completed_at = event.timestamp
                    agent.total_tokens = event.total_tokens
                    agent.total_duration_ms = event.total_duration_ms
                    agent.current_tool = None
                    self._rebuild_table()

    def _refresh_durations(self) -> None:
        if any(a.status == "running" for a in self.agents.values()):
            self._rebuild_table()

    def _rebuild_table(self) -> None:
        table = self.query_one("#agent-table", DataTable)
        table.clear()
        now = datetime.now(timezone.utc)

        # Update summary
        running = sum(1 for a in self.agents.values() if a.status == "running")
        done = sum(1 for a in self.agents.values() if a.status == "completed")
        total = len(self.agents)
        self.query_one("#agent-summary", Static).update(
            f"Agents: [bold]{total}[/] total  "
            f"[yellow]{running}[/] running  "
            f"[green]{done}[/] completed"
        )

        for agent in self.agents.values():
            # Duration
            if agent.total_duration_ms is not None:
                dur = f"{agent.total_duration_ms / 1000:.1f}s"
            elif agent.status == "running":
                elapsed = (now - agent.started_at).total_seconds()
                dur = f"{elapsed:.0f}s..."
            else:
                dur = "-"

            # Status
            if agent.status == "running":
                status = "RUNNING"
            elif agent.status == "completed":
                status = "DONE"
            else:
                status = agent.status.upper()

            tokens = str(agent.total_tokens) if agent.total_tokens else "-"
            current = agent.current_tool or "-"

            table.add_row(
                agent.agent_id[:12],
                status,
                agent.prompt[:40],
                current,
                str(agent.tool_count),
                dur,
                tokens,
            )
