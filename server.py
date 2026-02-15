"""Main entrypoint — configures the gcal-mcp FastMCP instance with OAuth
and serves it over Streamable HTTP.
"""

from __future__ import annotations

import logging
import os
import sys

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

GCAL_OAUTH_CLIENT_ID = os.environ["GCAL_OAUTH_CLIENT_ID"]
GCAL_OAUTH_CLIENT_SECRET = os.environ["GCAL_OAUTH_CLIENT_SECRET"]
SESSION_SECRET = os.environ["SESSION_SECRET"]
BASE_URL = os.environ.get("BASE_URL", "https://example.com")
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "8001"))

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 1. Apply the per-request client monkey-patch BEFORE importing mcp
#    (gcal_mcp registers tools at import time)
# ---------------------------------------------------------------------------

from client_patch import apply_patch  # noqa: E402

apply_patch()

# ---------------------------------------------------------------------------
# 2. Import the already-constructed FastMCP instance from gcal-mcp
# ---------------------------------------------------------------------------

from gcal_mcp.server import mcp  # noqa: E402

# ---------------------------------------------------------------------------
# 3. Set up auth provider and storage
# ---------------------------------------------------------------------------

from auth.provider import GoogleOAuthProvider  # noqa: E402
from auth.storage import TokenStore  # noqa: E402

store = TokenStore(secret=SESSION_SECRET)
provider = GoogleOAuthProvider(
    store=store,
    google_client_id=GCAL_OAUTH_CLIENT_ID,
    google_client_secret=GCAL_OAUTH_CLIENT_SECRET,
    base_url=BASE_URL,
)

# ---------------------------------------------------------------------------
# 4. Configure auth on the existing mcp instance
#    (bypassing constructor validation since instance is already built)
# ---------------------------------------------------------------------------

from mcp.server.auth.provider import ProviderTokenVerifier  # noqa: E402
from mcp.server.auth.settings import (  # noqa: E402
    AuthSettings,
    ClientRegistrationOptions,
    RevocationOptions,
)

mcp.settings.auth = AuthSettings(
    issuer_url=BASE_URL,
    resource_server_url=f"{BASE_URL}/mcp",
    client_registration_options=ClientRegistrationOptions(enabled=True),
    revocation_options=RevocationOptions(enabled=True),
)
mcp._auth_server_provider = provider
mcp._token_verifier = ProviderTokenVerifier(provider)

# ---------------------------------------------------------------------------
# 5. Configure HTTP transport settings
# ---------------------------------------------------------------------------

mcp.settings.host = HOST
mcp.settings.port = PORT
mcp.settings.stateless_http = True

# Allow the public hostname through transport security
from urllib.parse import urlparse  # noqa: E402

_host = urlparse(BASE_URL).hostname
if _host:
    mcp.settings.transport_security.allowed_hosts = [_host]

# ---------------------------------------------------------------------------
# 6. Custom routes (health check + Google OAuth callback)
# ---------------------------------------------------------------------------

from starlette.requests import Request  # noqa: E402
from starlette.responses import JSONResponse, RedirectResponse, Response  # noqa: E402


@mcp.custom_route("/health", methods=["GET"])
async def health(request: Request) -> Response:
    return JSONResponse({"status": "ok"})


@mcp.custom_route("/.well-known/oauth-protected-resource", methods=["GET"])
async def oauth_protected_resource(request: Request) -> Response:
    """RFC 9728 — Protected Resource Metadata for MCP clients."""
    return JSONResponse({
        "resource": f"{BASE_URL}/mcp",
        "authorization_servers": [f"{BASE_URL}/"],
    })


@mcp.custom_route("/oauth/callback", methods=["GET"])
async def google_oauth_callback(request: Request) -> Response:
    """Handle Google's OAuth redirect after user authorizes.

    Exchanges Google's auth code for tokens, generates our own
    auth code, and redirects back to Claude's redirect_uri.
    """
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    error = request.query_params.get("error")

    if error:
        logger.error("Google OAuth error: %s", error)
        return JSONResponse(
            {"error": "google_oauth_error", "detail": error}, status_code=400
        )

    if not code or not state:
        return JSONResponse(
            {"error": "missing_params", "detail": "code and state are required"},
            status_code=400,
        )

    try:
        redirect_url = await provider.exchange_google_code(code, state)
        return RedirectResponse(url=redirect_url, status_code=302)
    except ValueError as exc:
        logger.error("OAuth callback failed: %s", exc)
        return JSONResponse(
            {"error": "callback_failed", "detail": str(exc)}, status_code=400
        )
    except Exception as exc:
        logger.exception("Unexpected error in OAuth callback")
        return JSONResponse(
            {"error": "internal_error", "detail": "An internal error occurred"},
            status_code=500,
        )


# ---------------------------------------------------------------------------
# 7. Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logger.info("Starting gcal-mcp-remote on %s:%d", HOST, PORT)
    logger.info("Base URL: %s", BASE_URL)
    logger.info("MCP endpoint: %s/mcp", BASE_URL)
    mcp.run(transport="streamable-http")
