import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncIterator

from .events import (
    AgentCompleteEvent,
    AgentProgressEvent,
    AgentStartEvent,
    SessionInfo,
)


def _parse_ts(ts_str: str) -> datetime:
    if not ts_str:
        return datetime.now(timezone.utc)
    return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))


def _summarize_tool_input(tool_name: str, inp: dict) -> str:
    if tool_name == "Bash":
        return inp.get("description", inp.get("command", "")[:100])
    elif tool_name == "Read":
        return inp.get("file_path", "")
    elif tool_name == "Glob":
        return inp.get("pattern", "")
    elif tool_name == "Grep":
        return f'/{inp.get("pattern", "")}/ in {inp.get("path", ".")}'
    elif tool_name in ("Write", "Edit"):
        return inp.get("file_path", "")
    elif tool_name == "Agent":
        return inp.get("description", "")[:100]
    elif tool_name == "ToolSearch":
        return inp.get("query", "")
    return str(inp)[:100]


class JsonlParser:
    """Tails a JSONL session log file and yields parsed agent-related events."""

    def __init__(self, jsonl_path: Path):
        self.jsonl_path = jsonl_path
        self._file_pos: int = 0
        self._session_info: SessionInfo | None = None
        self._known_agents: set[str] = set()

    async def tail_events(self) -> AsyncIterator:
        """Async generator that waits for the file, then yields events as new lines appear."""
        # Wait for file to exist
        while not self.jsonl_path.exists():
            await asyncio.sleep(0.5)

        # Initial catchup
        async for event in self._read_new_lines():
            yield event

        # Watch for changes
        import watchfiles

        async for _changes in watchfiles.awatch(
            self.jsonl_path.parent,
            watch_filter=lambda change, path: str(path) == str(self.jsonl_path),
        ):
            async for event in self._read_new_lines():
                yield event

    async def _read_new_lines(self):
        with open(self.jsonl_path, "r", encoding="utf-8") as f:
            f.seek(self._file_pos)
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                for event in self._parse_line(data):
                    yield event
            self._file_pos = f.tell()

    def _parse_line(self, data: dict) -> list:
        events = []
        line_type = data.get("type")
        timestamp = _parse_ts(data.get("timestamp", ""))

        if line_type == "user":
            # Extract session info from first user message
            if self._session_info is None and data.get("sessionId"):
                self._session_info = SessionInfo(
                    session_id=data.get("sessionId", ""),
                    cwd=data.get("cwd", ""),
                    version=data.get("version", ""),
                    slug=data.get("slug", ""),
                    git_branch=data.get("gitBranch", ""),
                )
                events.append(self._session_info)

            # Check for agent completion
            tool_result = data.get("toolUseResult", {})
            if isinstance(tool_result, dict) and tool_result.get("agentId"):
                agent_id = tool_result["agentId"]
                events.append(AgentCompleteEvent(
                    timestamp=timestamp,
                    agent_id=agent_id,
                    status=tool_result.get("status", "completed"),
                    prompt=tool_result.get("prompt", "")[:200],
                    total_duration_ms=tool_result.get("totalDurationMs", 0),
                    total_tokens=tool_result.get("totalTokens", 0),
                    total_tool_use_count=tool_result.get("totalToolUseCount", 0),
                ))

        elif line_type == "progress":
            progress_data = data.get("data", {})
            if progress_data.get("type") != "agent_progress":
                return events

            agent_id = progress_data.get("agentId", "")
            prompt = progress_data.get("prompt", "")

            # First appearance — emit start event
            if prompt and agent_id not in self._known_agents:
                self._known_agents.add(agent_id)
                events.append(AgentStartEvent(
                    timestamp=timestamp,
                    agent_id=agent_id,
                    prompt=prompt[:300],
                ))

            # Extract tool name from forwarded message
            fwd_msg = progress_data.get("message", {})
            if isinstance(fwd_msg, dict):
                inner_msg = fwd_msg.get("message", {})
                inner_content = inner_msg.get("content", [])
                if isinstance(inner_content, list):
                    for item in inner_content:
                        if isinstance(item, dict) and item.get("type") == "tool_use":
                            events.append(AgentProgressEvent(
                                timestamp=timestamp,
                                agent_id=agent_id,
                                tool_name=item.get("name"),
                                tool_input_summary=_summarize_tool_input(
                                    item.get("name", ""),
                                    item.get("input", {}),
                                ),
                            ))

        return events
