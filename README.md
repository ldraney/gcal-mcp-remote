[![PyPI](https://img.shields.io/pypi/v/gcal-mcp-remote-ldraney)](https://pypi.org/project/gcal-mcp-remote-ldraney/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

# gcal-mcp-remote

Remote MCP server wrapping [gcal-mcp](https://github.com/ldraney/gcal-mcp) with Google OAuth 2.0 and Streamable HTTP transport — designed for Claude.ai connectors.

## How it works

```
Claude.ai ──HTTP+Bearer──> gcal-mcp-remote ──Google API──> Google Calendar
                                │
                          imports gcal-mcp's FastMCP (all 14 tools)
                          patches get_client() with per-request ContextVar
                          adds Google OAuth + /health + /oauth/callback
```

Three-party OAuth: Claude ↔ this server ↔ Google. Each user authorizes their own Google Calendar via OAuth. The server stores per-user Google refresh tokens (encrypted at rest).

## Prerequisites

1. A **Web application** OAuth client in [Google Cloud Console](https://console.cloud.google.com/apis/credentials):
   - Create Credentials → OAuth client ID → Type: **Web application**
   - Add authorized redirect URI: `{BASE_URL}/oauth/callback`
   - Note the Client ID and Client Secret
2. Google Calendar API enabled in the same project

## Setup

```bash
git clone https://github.com/ldraney/gcal-mcp-remote.git
cd gcal-mcp-remote
cp .env.example .env
# Edit .env with your Google OAuth credentials, BASE_URL, and SESSION_SECRET
make install
make run
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GCAL_OAUTH_CLIENT_ID` | Google OAuth Web application client ID |
| `GCAL_OAUTH_CLIENT_SECRET` | Google OAuth Web application client secret |
| `SESSION_SECRET` | Random secret for encrypting token store |
| `BASE_URL` | Public HTTPS URL where this server is reachable |
| `HOST` | Bind address (default: `127.0.0.1`) |
| `PORT` | Listen port (default: `8001`) |

## Verification

```bash
curl http://127.0.0.1:8001/health                                    # {"status": "ok"}
curl http://127.0.0.1:8001/.well-known/oauth-authorization-server    # OAuth metadata
curl -X POST http://127.0.0.1:8001/mcp                               # 401 (auth required)
```

## Deploying

### Standalone

Use any HTTPS tunnel (Tailscale Funnel, ngrok, Cloudflare Tunnel) to expose the server publicly, then add the URL as a Claude.ai connector.

A systemd service file is provided in `systemd/gcal-mcp-remote.service`.

### Kubernetes (production)

Production deployment is managed by [mcp-gateway-k8s](https://github.com/ldraney/mcp-gateway-k8s), which runs this server as a pod with Tailscale Funnel ingress. That repo contains the Dockerfile, K8s manifests, and secrets management.

Full integration testing (Claude.ai connector → OAuth → Google Calendar) is tracked in [mcp-gateway-k8s#12](https://github.com/ldraney/mcp-gateway-k8s/issues/12) and [#6](https://github.com/ldraney/gcal-mcp-remote/issues/6).

## Privacy

See [PRIVACY.md](PRIVACY.md) for our privacy policy.

## License

MIT
