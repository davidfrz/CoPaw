# -*- coding: utf-8 -*-
"""FastAPI routes for querying audit logs."""

from typing import Optional

from fastapi import APIRouter, Query, Request

from .logger import AuditLogger
from .models import AuditAction

router = APIRouter(prefix="/audit", tags=["audit"])


def _get_logger(request: Request) -> AuditLogger:
    return request.app.state.audit_logger


@router.get("")
async def list_audit_entries(
    request: Request,
    action: Optional[str] = Query(
        None,
        description="Filter by action type (e.g. tool_call, config_change)",
    ),
    actor: Optional[str] = Query(
        None,
        description="Filter by actor (e.g. agent, user, system)",
    ),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Return paginated audit log entries (newest first)."""
    audit = _get_logger(request)
    entries = audit.query(
        action=action,
        actor=actor,
        limit=limit,
        offset=offset,
    )
    total = audit.count(action=action, actor=actor)
    return {
        "entries": [e.model_dump() for e in entries],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/actions")
async def list_actions():
    """Return the list of known audit action types."""
    return {"actions": [a.value for a in AuditAction]}
