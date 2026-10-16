"""Explain a read-only Windows-MCP ownership snapshot; never acquire control."""
import json
import math


def control_summary(result):
    if not isinstance(result, dict):
        raise ValueError('Windows-MCP returned an invalid control status.')
    if result.get('isError'):
        raise ValueError('Windows-MCP refused the status check. Inspect its connection and permissions.')
    status = result.get('structuredContent')
    if not isinstance(status, dict):
        blocks = [x.get('text', '') for x in (result.get('content') or [])
                  if isinstance(x, dict) and x.get('type') == 'text']
        if len(blocks) != 1 or not isinstance(blocks[0], str) or len(blocks[0]) > 16384:
            raise ValueError('Windows-MCP did not return one bounded JSON control status.')
        try:
            status = json.loads(blocks[0])
        except ValueError as exc:
            raise ValueError('Windows-MCP returned an unreadable control status.') from exc
    if not isinstance(status, dict):
        raise ValueError('Windows-MCP returned an invalid control status.')

    def seconds(key):
        value = status.get(key)
        if type(value) not in (int, float) or not 0 <= value <= 86400 or not math.isfinite(value):
            return None
        return f'{value:.1f}'

    state = status.get('state')
    descriptions = {
        'ready': 'No user-input hold is reported. The next authorized action must still pass backend checks.',
        'ai': 'The service reports AI ownership. You can still take over using the service controls.',
        'user': 'You currently own the desktop. Leave the mouse and keyboard idle, then check again before continuing.',
        'takeover_pending': 'A user takeover is in progress. Pause desktop actions until the service releases the hold.',
        'unavailable': 'Desktop ownership is unavailable. Check the interactive Windows session and Windows-MCP health.',
        'disabled': 'The service reports ownership protection disabled. This check did not change that setting.',
    }
    if not isinstance(state, str) or state not in descriptions:
        raise ValueError('Windows-MCP returned an unknown ownership state; desktop availability is not confirmed.')
    parts = [descriptions[state]]
    wait = seconds('wait_seconds')
    if state == 'user' and wait is not None:
        parts.append(f'Remaining idle wait at this check: {wait} s. New physical input restarts the timer.')
    policy = status.get('policy')
    if policy in ('relaxed', 'balanced', 'strict'):
        parts.append('Gate policy: ' + policy + '.')
    timeout = seconds('idle_timeout_seconds')
    if timeout is not None:
        parts.append(f'Configured idle interval: {timeout} s.')
    parts.append('Snapshot only; Full Access does not override desktop ownership.')
    return '\n'.join(parts)
