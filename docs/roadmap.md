# Deferred work

## Multiple assistant providers

Recorded on 2026-10-17 at the user's request; explicitly deferred. Do not start
this work as part of voice, GUI or installation changes without a new request.

The intended future direction is to let Tigo use Codex, Claude Code,
Antigravity and direct model APIs with user-supplied credentials where needed.

Proposed implementation order:

1. Extract a common provider interface while preserving the working Codex path.
2. Add Claude Code using its supported programmatic interface.
3. Add Antigravity using supported CLI/SDK interfaces.
4. Add direct API providers with their own tool execution loop and credential
   storage, rather than assuming every API supplies a ready-made desktop agent.

Each adapter needs streamed text/tool events, session identity/resume,
interruption, MCP capabilities/permissions and error handling. Provider choice
must not silently mix conversation state or credentials, widen desktop input
grants or bypass native ownership guards. Update GUI, installers, docs and tests
alongside the provider layer. Subscription sign-in and API-key billing are
separate integration modes and must be verified against official documentation
when this work resumes.

The current runtime remains Codex app-server only. This document records the
plan, not an implemented capability or a measured token/cost estimate.
