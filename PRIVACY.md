# Privacy Policy

**gcal-mcp-remote** — Last updated: 2026-02-15

## What This Service Does

This is a remote MCP (Model Context Protocol) server that wraps gcal-mcp with Google OAuth 2.0 authentication over Streamable HTTP transport. It acts as a proxy between AI assistants (e.g., Claude) and the Google Calendar API.

## Data We Handle

### OAuth Tokens
- We store Google OAuth 2.0 access tokens and refresh tokens locally on the server where this software is deployed.
- Tokens are encrypted at rest using Fernet symmetric encryption.
- Tokens are used solely to authenticate Google Calendar API requests on your behalf.
- Tokens are never shared with third parties.

### Google Calendar Data
- We access your Google Calendar data only when you explicitly request it through MCP tool calls.
- We do not store, log, or analyze calendar data beyond what is needed to fulfill the current request.

### No Analytics or Tracking
- This software does not include any analytics, telemetry, or tracking.
- No data is sent to any third party beyond Google's own API.

## Data Storage

- All data is stored locally on the server where this software is deployed.
- The operator of the server is responsible for securing the deployment environment.
- No data is stored in cloud services by this software itself.

## Your Rights

- You can revoke access at any time through your Google Account settings (Security → Third-party apps with account access).
- Revoking access immediately invalidates all stored tokens.

## Self-Hosted Nature

This is open-source, self-hosted software. The privacy practices depend on how the operator deploys and manages the server. This policy covers the software's behavior — the operator is responsible for their own infrastructure security.

## Contact

For questions about this software's privacy practices, please open an issue at https://github.com/ldraney/gcal-mcp-remote/issues.
