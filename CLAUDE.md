# gcal-mcp-remote

Remote MCP connector wrapping `ldraney-gcal-mcp` with Google OAuth 2.0 over Streamable HTTP.

## Architecture

Three-party OAuth proxy: Claude.ai ↔ this server ↔ Google OAuth.

- **server.py** — Main entrypoint. Imports `mcp` from `gcal_mcp`, configures auth, adds custom routes, runs Streamable HTTP.
- **auth/provider.py** — `GoogleOAuthProvider` implementing `OAuthAuthorizationServerProvider`. Proxies Google OAuth.
- **auth/storage.py** — `TokenStore` for encrypted file-based persistence of tokens, auth codes, and client registrations.
- **client_patch.py** — Monkey-patches `get_client()` in all `gcal_mcp` tool modules to use a per-request `ContextVar`-based `GCalClient`.

## Key Patterns

- The `mcp` FastMCP instance is imported from `gcal_mcp` and reconfigured at runtime (auth settings, host/port, stateless mode).
- `load_access_token()` in the provider calls `set_client_for_request()` which builds `google.oauth2.credentials.Credentials` with the user's refresh token and creates a `GCalClient`.
- All 3 tool modules (`events`, `calendars`, `freebusy`) import `get_client` from `gcal_mcp.server` — the patch replaces it in each module's namespace.
- `BASE_URL` hostname is added to `transport_security.allowed_hosts` — without this, MCP rejects requests with 421 Misdirected Request.
- Google OAuth requires `access_type=offline` and `prompt=consent` to get a refresh_token on first authorization.

## Running

```bash
cp .env.example .env   # fill in values
make install
make run               # start server on :8001

# Expose via any HTTPS tunnel (Tailscale Funnel, ngrok, Cloudflare Tunnel, etc.)
```

## Deployment

- **k8s (production):** `openclaw` namespace on archbox, LoadBalancer port 8001
- **Tailscale Funnel:** `https://archbox.tail5b443a.ts.net:8443` → k8s LB :8001
- **Health check:** `curl https://archbox.tail5b443a.ts.net:8443/health`

## Testing

```bash
curl http://127.0.0.1:8001/health
curl http://127.0.0.1:8001/.well-known/oauth-authorization-server
curl -X POST http://127.0.0.1:8001/mcp  # should 401
```

## Tools (14)

- **Events (8):** list_events, get_event, create_event, update_event, patch_event, delete_event, move_event, list_event_instances
- **Calendars (5):** list_calendars, get_calendar, create_calendar, delete_calendar, clear_calendar
- **FreeBusy (1):** query_freebusy

Use `/calendar-qa` to run the full QA test suite. See `.claude/agents/calendar-manager.md` for the agent profile.
