"""Per-request GCalClient injection via ContextVar.

Monkey-patches get_client() in gcal_mcp.server and all 3 tool modules
so each authenticated request gets its own GCalClient with the user's
Google OAuth credentials.

The Google Calendar API discovery document is loaded once from the
static copy bundled with the googleapiclient library. Per-request
clients use build_from_document() instead of build(), avoiding the
discovery cache machinery (and its "file_cache is only supported with
oauth2client<4.0.0" warning) entirely.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from contextvars import ContextVar

from gcal_sdk import GCalClient
from gcal_sdk.calendars import CalendarsResource
from gcal_sdk.events import EventsResource
from gcal_sdk.freebusy import FreeBusyResource
from google.oauth2.credentials import Credentials
from googleapiclient import discovery_cache
from googleapiclient.discovery import build_from_document

logger = logging.getLogger(__name__)

_request_client: ContextVar[GCalClient | None] = ContextVar(
    "_request_client", default=None
)

# Load the static Calendar v3 discovery document once at import time.
# This is the same JSON that build() would read from the bundled files,
# but we skip the cache/autodetect path that emits the file_cache warning.
_CALENDAR_DISCOVERY_DOC = discovery_cache.get_static_doc("calendar", "v3")
if _CALENDAR_DISCOVERY_DOC is None:
    # Fallback: if the static doc isn't bundled, build_from_document will
    # fail, so we log a warning and fall back to build() at runtime.
    logger.warning(
        "Static discovery document for calendar v3 not found; "
        "will fall back to build() per-request"
    )


def _make_client(credentials: Credentials) -> GCalClient:
    """Create a GCalClient using the cached discovery document.

    Uses build_from_document() with the pre-loaded static discovery JSON
    instead of build(), which avoids the per-call discovery cache lookup
    and the associated file_cache warning.
    """
    if _CALENDAR_DISCOVERY_DOC is not None:
        service = build_from_document(_CALENDAR_DISCOVERY_DOC, credentials=credentials)
    else:
        # Fallback path — should not happen with standard google-api-python-client
        from googleapiclient.discovery import build

        service = build("calendar", "v3", credentials=credentials)

    # SYNC NOTE: object.__new__(GCalClient) bypasses __init__ to avoid a
    # redundant build() call.  The attribute assignments below must be kept
    # in sync with GCalClient.__init__ in gcal-sdk.  If gcal-sdk adds new
    # instance attributes in __init__, they must be replicated here.
    # Long-term, consider adding a GCalClient.from_service() factory method
    # to gcal-sdk so the library owns its own construction logic.
    client = object.__new__(GCalClient)
    client._credentials = credentials
    client._service = service
    client.events = EventsResource(service)
    client.calendars = CalendarsResource(service)
    client.freebusy = FreeBusyResource(service)
    return client


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
    """Create a GCalClient with the given Google refresh token and set it on the contextvar.

    Uses the cached discovery document to avoid per-request build() calls.
    """
    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
    )
    client = _make_client(creds)
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
    token = _request_client.set(_make_client(creds))
    try:
        yield
    finally:
        _request_client.reset(token)


def apply_patch() -> None:
    """Replace get_client in gcal_mcp.server and all tool modules."""
    import gcal_mcp.server
    import gcal_mcp.tools.events
    import gcal_mcp.tools.calendars
    import gcal_mcp.tools.freebusy

    gcal_mcp.server.get_client = patched_get_client

    for mod in [
        gcal_mcp.tools.events,
        gcal_mcp.tools.calendars,
        gcal_mcp.tools.freebusy,
    ]:
        mod.get_client = patched_get_client
