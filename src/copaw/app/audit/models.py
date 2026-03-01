# -*- coding: utf-8 -*-
"""Data models for the audit logging system."""

import enum
import time
import uuid
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class AuditAction(str, enum.Enum):
    """Categories of auditable operations."""

    TOOL_CALL = "tool_call"
    APPROVAL_DECISION = "approval_decision"
    CONFIG_CHANGE = "config_change"
    SKILL_CHANGE = "skill_change"
    MCP_CHANGE = "mcp_change"
    CRON_CHANGE = "cron_change"


class AuditEntry(BaseModel):
    """A single audit log entry."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    timestamp: float = Field(default_factory=time.time)
    actor: str = Field(
        default="system",
        description="Who performed the action (agent/user/system/cron)",
    )
    action: str = Field(
        ...,
        description="Action category from AuditAction enum",
    )
    target: str = Field(
        default="",
        description="Primary object of the action (tool name, etc.)",
    )
    summary: str = Field(
        default="",
        description="Human-readable one-line summary",
    )
    result: str = Field(
        default="success",
        description="Outcome: success / denied / error / timeout",
    )
    detail: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Extra context (command args, before/after values, etc.)",
    )
