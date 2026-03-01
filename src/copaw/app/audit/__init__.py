# -*- coding: utf-8 -*-
"""Audit logging system for CoPaw.

Records all critical operations (tool calls, approval decisions,
config changes, skill/MCP/cron changes) to a JSONL file.
"""

from .models import AuditAction, AuditEntry
from .logger import AuditLogger

__all__ = [
    "AuditAction",
    "AuditEntry",
    "AuditLogger",
]
