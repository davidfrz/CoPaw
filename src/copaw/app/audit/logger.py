# -*- coding: utf-8 -*-
"""JSONL-based audit logger with file rotation."""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import AuditEntry

logger = logging.getLogger(__name__)

# Default rotation threshold: 10 MB.
_DEFAULT_MAX_BYTES = 10 * 1024 * 1024


class AuditLogger:
    """Append-only JSONL audit logger with rotation and query support.

    Usage::

        audit = AuditLogger(Path("~/.copaw/audit.jsonl"))
        audit.log(action="tool_call", target="execute_shell_command",
                  summary="Ran: ls -la", actor="agent")
    """

    def __init__(
        self,
        path: Path,
        max_bytes: int = _DEFAULT_MAX_BYTES,
    ) -> None:
        self._path = path
        self._max_bytes = max_bytes
        # Ensure parent dir exists.
        self._path.parent.mkdir(parents=True, exist_ok=True)

    # -- write ----------------------------------------------------------------

    def log(
        self,
        action: str,
        target: str = "",
        summary: str = "",
        actor: str = "system",
        result: str = "success",
        detail: Optional[Dict[str, Any]] = None,
    ) -> AuditEntry:
        """Create and persist an audit entry. Returns the entry."""
        entry = AuditEntry(
            action=action,
            target=target,
            summary=summary,
            actor=actor,
            result=result,
            detail=detail,
        )
        self._append(entry)
        return entry

    def _append(self, entry: AuditEntry) -> None:
        """Append a single entry as one JSON line."""
        self._maybe_rotate()
        try:
            with open(self._path, "a", encoding="utf-8") as f:
                f.write(entry.model_dump_json() + "\n")
        except Exception:
            logger.exception("Failed to write audit entry")

    def _maybe_rotate(self) -> None:
        """Rotate the log file if it exceeds *max_bytes*."""
        try:
            if not self._path.exists():
                return
            if self._path.stat().st_size < self._max_bytes:
                return
        except OSError:
            return

        rotated = self._path.with_suffix(".jsonl.1")
        try:
            # Simple rotation: keep only one backup.
            if rotated.exists():
                rotated.unlink()
            os.rename(self._path, rotated)
            logger.info("Rotated audit log -> %s", rotated)
        except OSError:
            logger.exception("Failed to rotate audit log")

    # -- read -----------------------------------------------------------------

    def query(
        self,
        *,
        action: Optional[str] = None,
        actor: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[AuditEntry]:
        """Read entries from the log file with optional filtering.

        Returns entries in reverse-chronological order (newest first).
        """
        entries = self._read_all()

        if action:
            entries = [e for e in entries if e.action == action]
        if actor:
            entries = [e for e in entries if e.actor == actor]

        # Newest first.
        entries.sort(key=lambda e: e.timestamp, reverse=True)

        return entries[offset : offset + limit]

    def count(
        self,
        *,
        action: Optional[str] = None,
        actor: Optional[str] = None,
    ) -> int:
        """Return total number of entries matching the filters."""
        entries = self._read_all()
        if action:
            entries = [e for e in entries if e.action == action]
        if actor:
            entries = [e for e in entries if e.actor == actor]
        return len(entries)

    def _read_all(self) -> List[AuditEntry]:
        """Parse every line from the log file."""
        if not self._path.exists():
            return []
        entries: List[AuditEntry] = []
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entries.append(
                            AuditEntry.model_validate(json.loads(line)),
                        )
                    except Exception:
                        # Skip malformed lines.
                        continue
        except OSError:
            logger.exception("Failed to read audit log")
        return entries
