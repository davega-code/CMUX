from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SessionInfo:
    session_id: str
    cwd: str
    version: str
    slug: str
    git_branch: str


@dataclass
class AgentStartEvent:
    timestamp: datetime
    agent_id: str
    prompt: str


@dataclass
class AgentProgressEvent:
    timestamp: datetime
    agent_id: str
    tool_name: str | None = None
    tool_input_summary: str | None = None


@dataclass
class AgentCompleteEvent:
    timestamp: datetime
    agent_id: str
    status: str
    prompt: str
    total_duration_ms: int
    total_tokens: int
    total_tool_use_count: int


@dataclass
class AgentState:
    agent_id: str
    prompt: str
    status: str  # "running", "completed", "error"
    started_at: datetime
    completed_at: datetime | None = None
    current_tool: str | None = None
    tool_count: int = 0
    total_tokens: int | None = None
    total_duration_ms: int | None = None
