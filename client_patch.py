"""Per-request GCalClient injection via ContextVar.

Monkey-patches get_client() in calendar_mcp.server and all 3 tool modules
so each authenticated request gets its own GCalClient with the user's
Google OAuth credentials.
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar

from gcal_sdk import GCalClient
from google.oauth2.credentials import Credentials

_request_client: ContextVar[GCalClient | None] = ContextVar(
    "_request_client", default=None
)


def patched_get_client() -> GCalClient:
    """Return the per-request GCalClient set by the OAuth flow."""
    client = _request_client.get()
    if client is None:
        raise RuntimeError(
            "No GCalClient set for this request — is OAuth configured?"
        )
    return client


def set_client_for_request(
    refresh_token: str,
    client_id: str,
    client_secret: str,
) -> None:
    """Create a GCalClient with the given Google refresh token and set it on the contextvar."""
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
    )
    client = GCalClient(credentials=creds)
    _request_client.set(client)


@contextmanager
def client_context(refresh_token: str, client_id: str, client_secret: str):
    """Context manager that sets up a per-request GCalClient."""
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
    )
    token = _request_client.set(GCalClient(credentials=creds))
    try:
        yield
    finally:
        _request_client.reset(token)


def apply_patch() -> None:
    """Replace get_client in calendar_mcp.server and all tool modules."""
    import calendar_mcp.server
    import calendar_mcp.tools.events
    import calendar_mcp.tools.calendars
    import calendar_mcp.tools.freebusy

    calendar_mcp.server.get_client = patched_get_client

    for mod in [
        calendar_mcp.tools.events,
        calendar_mcp.tools.calendars,
        calendar_mcp.tools.freebusy,
    ]:
        mod.get_client = patched_get_client
