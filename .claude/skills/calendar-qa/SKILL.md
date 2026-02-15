# /calendar-qa

Run the QA test plan for gcal-mcp-remote against a live server.

## Server Endpoints

- **Production (k8s via Tailscale Funnel):** `https://archbox.tail5b443a.ts.net:8443`
- **Local dev:** `http://127.0.0.1:8001`
- **Health check:** `GET /health` → `{"status":"ok"}`
- **OAuth metadata:** `GET /.well-known/oauth-authorization-server`
- **MCP endpoint:** `POST /mcp` (requires OAuth bearer token)

## Usage

```
/calendar-qa              # run full test suite against production
/calendar-qa local        # run against local dev server
/calendar-qa events       # run only events tests
/calendar-qa calendars    # run only calendars tests
/calendar-qa freebusy     # run only freebusy tests
```

## Test Plan

### 1. Connectivity
- `curl <server>/health` returns `{"status":"ok"}`
- `curl <server>/.well-known/oauth-authorization-server` returns valid JSON
- `POST /mcp` without auth returns 401

### 2. Events CRUD
Run these in order (each step depends on the previous):

1. **list_events** — call with time_min=now, verify response is JSON array
2. **create_event** — create "QA Test Event" tomorrow at 3pm America/Denver, 1 hour
3. **get_event** — retrieve the created event by ID, verify fields match
4. **patch_event** — change summary to "QA Test Event (Updated)"
5. **list_events with q** — search for "QA Test Event", verify it appears
6. **create_event with recurrence** — create "QA Recurring" weekly for 3 weeks
7. **list_event_instances** — verify 3 instances returned
8. **delete_event** — delete both test events
9. **list_events** — verify test events no longer appear

### 3. Calendar Management
1. **list_calendars** — verify primary calendar present
2. **get_calendar** — get primary calendar details
3. **create_calendar** — create "QA Test Calendar"
4. **create_event on test calendar** — add an event to it
5. **move_event** — move event from test calendar to primary
6. **delete_calendar** — remove "QA Test Calendar"

### 4. FreeBusy
1. **query_freebusy** — check this week for primary calendar
2. Verify response contains `calendars` with busy periods

### 5. Edge Cases
- Create all-day event (date without time)
- Create event with attendees list
- Invalid calendar_id → verify clean error message
- Invalid event_id → verify clean error message

## Reporting

After running tests, output a summary table:

```
| Test                    | Status | Notes |
|-------------------------|--------|-------|
| health check            | PASS   |       |
| list_events             | PASS   |       |
| create_event            | PASS   | ID: xxx |
| ...                     |        |       |
```

Clean up all test events and calendars after the run.
