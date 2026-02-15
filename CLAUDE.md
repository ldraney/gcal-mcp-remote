# gcal-mcp-remote

Remote MCP connector wrapping `gcal-mcp-ldraney` with Google OAuth 2.0 over Streamable HTTP.

## Architecture

Three-party OAuth proxy: Claude.ai <-> this server <-> Google OAuth.

- **src/gcal_mcp_remote/server.py** — Main entrypoint. Imports `mcp` from `gcal_mcp`, configures auth, adds custom routes, runs Streamable HTTP.
- **src/gcal_mcp_remote/auth/provider.py** — `GoogleOAuthProvider` implementing `OAuthAuthorizationServerProvider`. Proxies Google OAuth.
- **src/gcal_mcp_remote/auth/storage.py** — `TokenStore` for encrypted file-based persistence of tokens, auth codes, and client registrations.
- **src/gcal_mcp_remote/auth/discovery_auth.py** — `MethodAwareAuthMiddleware` allowing unauthenticated MCP tool discovery (initialize, tools/list).
- **src/gcal_mcp_remote/client_patch.py** — Monkey-patches `get_client()` in all `gcal_mcp` tool modules to use a per-request `ContextVar`-based `GCalClient`.

## Key Patterns

- The `mcp` FastMCP instance is imported from `gcal_mcp` and reconfigured at runtime (auth settings, host/port, stateless mode).
- `load_access_token()` in the provider calls `set_client_for_request()` which builds `google.oauth2.credentials.Credentials` with the user's refresh token and creates a `GCalClient`.
- All 3 tool modules (`events`, `calendars`, `freebusy`) import `get_client` from `gcal_mcp.server` — the patch replaces it in each module's namespace.
- `BASE_URL` hostname is added to `transport_security.allowed_hosts` — without this, MCP rejects requests with 421 Misdirected Request.
- Google OAuth requires `access_type=offline` and `prompt=consent` to get a refresh_token on first authorization.
- `MethodAwareAuthMiddleware` peeks at JSON-RPC method names to allow `initialize` and `tools/list` without Bearer tokens.

## Running

```bash
cp .env.example .env   # fill in values
make install
make run               # start server on :8001

# Expose via any HTTPS tunnel (Tailscale Funnel, ngrok, Cloudflare Tunnel, etc.)
```

## Testing

```bash
curl http://127.0.0.1:8001/health
curl http://127.0.0.1:8001/.well-known/oauth-authorization-server
curl -X POST http://127.0.0.1:8001/mcp  # should 401
```
