"""An actual child process speaking app-server JSON-RPC for integration tests."""
import json
import os
from pathlib import Path
import sys
import time

scenario = sys.argv[1]
log = Path(sys.argv[2])
turn_count = 0
previous = ""


def send(value, fragmented=False):
    data = (json.dumps(value, ensure_ascii=False) + '\n').encode()
    if fragmented:
        star = data.find('★'.encode())
        offset = star + 1 if star >= 0 else len(data) // 2
        sys.stdout.buffer.write(data[:offset]); sys.stdout.buffer.flush()
        time.sleep(.02)
        sys.stdout.buffer.write(data[offset:]); sys.stdout.buffer.flush()
    else:
        sys.stdout.buffer.write(data); sys.stdout.buffer.flush()


def notice(method, params):
    send({'method': method, 'params': params})


for line in sys.stdin:
    request = json.loads(line)
    with log.open('a', encoding='utf-8') as file:
        file.write(json.dumps({'request': request, 'home': os.environ.get('CODEX_HOME', ''), 'pid': os.getpid()}) + '\n')
    if 'id' not in request:
        continue
    method, params = request.get('method'), request.get('params', {})
    if method is None:
        continue
    result = {}
    if method == 'initialize':
        if scenario == 'slow-init':
            time.sleep(60)
        result = {'userAgent': 'fake-app-server'}
    elif method == 'model/list':
        result = {'data': [{'id': 'test-model', 'model': 'test-model', 'isDefault': True, 'hidden': False,
                            'supportedReasoningEfforts': [{'reasoningEffort': 'low'}, {'reasoningEffort': 'high'}]}], 'nextCursor': None}
        if scenario == 'models-paged':
            if params.get('cursor') == 'second-page':
                result = {'data': [{'id': 'new-model', 'model': 'new-model', 'hidden': True,
                                    'supportedReasoningEfforts': [{'reasoningEffort': 'medium'}]},
                                   {'id': 'test-model', 'model': 'test-model'}], 'nextCursor': None}
            else:
                result['nextCursor'] = 'second-page'
    elif method in ('thread/start', 'thread/resume'):
        if scenario == 'resume-error' and method == 'thread/resume':
            send({'id': request['id'], 'error': {'code': -32600, 'message': 'Thread not available'}})
            continue
        result = {'thread': {'id': params.get('threadId', 'session-123'), 'turns': []}}
    elif method == 'mcpServerStatus/list':
        result = {'data': [{'name': 'tigo-x11', 'tools': {}}], 'nextCursor': None}
        if scenario.startswith('windows-control'):
            tools = {} if scenario == 'windows-control-missing' else {'ControlStatus': {'name': 'ControlStatus'}}
            result = {'data': [{'name': 'windows-mcp', 'tools': tools}], 'nextCursor': None}
    elif method == 'mcpServer/tool/call':
        tool = params['tool']
        if tool == 'ControlStatus':
            if scenario == 'windows-control-slow':
                continue
            status = {'state':'user','wait_seconds':7.5,'enabled':True,'policy':'relaxed','idle_timeout_seconds':10}
            result = {'content': [], 'structuredContent':status, 'isError':False}
            if scenario == 'windows-control-text':
                result = {'content':[{'type':'text','text':json.dumps(status)}]}
            elif scenario == 'windows-control-error':
                result = {'content':[], 'isError':True}
        elif scenario == 'refusal' and tool == 'focus_window':
            result = {'content': [{'type': 'text', 'text': 'Not authorized'}], 'isError': True}
        else:
            text = 'missing' if scenario == 'bad-check' else 'Editor ready'
            result = {'content': [{'type': 'text', 'text': text}], 'isError': False}
    elif method == 'turn/start':
        turn_count += 1
        thread = params['threadId']
        turn = 'turn-' + str(turn_count)
        send({'id': request['id'], 'result': {'turn': {'id': turn, 'status': 'inProgress', 'items': []}}})
        notice('turn/started', {'threadId': thread, 'turn': {'id': turn, 'status': 'inProgress', 'items': []}})
        if scenario == 'slow':
            previous = turn
            continue
        if scenario == 'error':
            notice('turn/completed', {'threadId': thread, 'turn': {'id': turn, 'status': 'failed', 'error': {'message': 'Login required'}, 'items': []}})
            continue
        if scenario == 'approval':
            send({'id':'approval','method':'item/commandExecution/requestApproval','params':{'threadId':thread,'turnId':turn}})
        if previous and scenario == 'late':
            notice('item/agentMessage/delta', {'threadId': thread, 'turnId': previous, 'itemId': 'old-item', 'delta': 'STALE'})
            notice('turn/completed', {'threadId': thread, 'turn': {'id': previous, 'status': 'completed', 'items': []}})
        if scenario in ('commentary', 'commentary-only'):
            notice('item/completed', {'threadId': thread, 'turnId': turn, 'item': {'id':'commentary','type':'agentMessage','phase':'commentary','text':'I will inspect the task.'}})
            if scenario == 'commentary-only':
                notice('turn/completed', {'threadId':thread,'turn':{'id':turn,'status':'completed','items':[]}})
                continue
        text = params['input'][0]['text']
        if scenario == 'fragmented':
            text = 'hello ★'
        item = 'answer-' + str(turn_count)
        send({'method': 'item/agentMessage/delta', 'params': {'threadId': thread, 'turnId': turn, 'itemId': item, 'delta': text[:2]}}, scenario == 'fragmented')
        notice('item/agentMessage/delta', {'threadId': thread, 'turnId': turn, 'itemId': item, 'delta': text[2:]})
        notice('item/completed', {'threadId': thread, 'turnId': turn, 'item': {'id': item, 'type': 'agentMessage', 'phase':'final_answer', 'text': text}})
        notice('turn/completed', {'threadId': thread, 'turn': {'id': turn, 'status': 'completed', 'items': []}})
        previous = turn
        continue
    elif method == 'turn/interrupt':
        send({'id': request['id'], 'result': {}})
        if scenario == 'ignore-stop':
            continue
        notice('turn/completed', {'threadId': params['threadId'], 'turn': {'id': params['turnId'], 'status': 'interrupted', 'items': []}})
        continue
    send({'id': request['id'], 'result': result})
