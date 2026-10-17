"""AT-SPI identity, ambiguity and stale-state checks without a live desktop."""
import importlib.util
from pathlib import Path
import types
import unittest
from unittest import mock

spec = importlib.util.spec_from_file_location('tigo_atspi_fixture', Path(__file__).resolve().parents[1]/'scripts/x11_accessibility.py')
a11y = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a11y)


class Node:
    def __init__(self, name, role='push button', children=(), pid=41, states=('enabled', 'sensitive', 'showing'), actions=('click',)):
        self.name, self.role, self.children, self.pid = name, role, list(children), pid
        self.states, self.actions, self.invocations = set(states), actions, []
    def get_name(self): return self.name
    def get_role_name(self): return self.role
    def get_child_count(self): return len(self.children)
    def get_child_at_index(self, i): return self.children[i]
    def get_process_id(self): return self.pid
    def get_state_set(self): return types.SimpleNamespace(contains=self.states.__contains__)
    def get_action_iface(self): return self
    def get_n_actions(self): return len(self.actions)
    def get_action_name(self, i): return self.actions[i]
    def do_action(self, i):
        self.invocations.append(i)
        return True


class TestSemanticDesktop(unittest.TestCase):
    def fixture(self, buttons):
        window = Node('Fixture', 'frame', buttons, actions=())
        desktop = Node('desktop', children=[Node('app', children=[window])])
        atspi = types.SimpleNamespace(get_desktop=lambda i: desktop,
                    StateType=types.SimpleNamespace(ENABLED='enabled', SENSITIVE='sensitive', SHOWING='showing'))
        request = {'action':'find', 'pid':41, 'title':'Fixture', 'window_id':'0x123', 'name':'Save'}
        return window, atspi, request

    def test_scoped_tree_reports_semantic_selector_without_pixels(self):
        button = Node('Save')
        _, api, request = self.fixture([Node('Secret', 'password text', actions=()), button])
        result = a11y.execute(request, api)
        self.assertEqual(result['elements'], [{'path':'1', 'name':'Save', 'role':'push button', 'enabled':True, 'showing':True, 'actions':['click']}])
        self.assertFalse(result['truncated'])
        self.assertEqual(button.invocations, [])

    def test_pid_and_title_must_both_match(self):
        _, api, request = self.fixture([Node('Save')])
        for change in ({'pid':42}, {'title':'Other'}):
            with self.assertRaises(RuntimeError): a11y.execute({**request, **change}, api)

    def test_duplicate_names_need_fresh_path(self):
        first, second = Node('Save'), Node('Save')
        _, api, request = self.fixture([first, second])
        request['action'] = 'invoke'
        with self.assertRaises(RuntimeError): a11y.execute(request, api)
        self.assertEqual(first.invocations + second.invocations, [])
        result = a11y.execute({**request, 'path':'1'}, api)
        self.assertTrue(result['verificationRequired'])
        self.assertEqual(first.invocations, [])
        self.assertEqual(second.invocations, [0])

    def test_disabled_hidden_or_focus_refused_never_invoke(self):
        for states in (('enabled','sensitive'), ('showing',), ('enabled','sensitive','showing')):
            button = Node('Save', states=states)
            _, api, request = self.fixture([button])
            def refuse(): raise RuntimeError('Focus changed')
            with self.assertRaises(RuntimeError): a11y.execute({**request, 'action':'invoke'}, api, focus_check=refuse)
            self.assertFalse(button.invocations)

    def test_name_or_state_changed_after_observation_stops_action(self):
        for changed in ('name', 'state'):
            button = Node('Save')
            _, api, request = self.fixture([button])
            def change():
                if changed == 'name': button.name = 'Delete'
                else: button.states.clear()
            with self.assertRaises(RuntimeError): a11y.execute({**request,'action':'invoke'}, api, focus_check=change)
            self.assertFalse(button.invocations)

    def test_truncated_search_cannot_establish_uniqueness(self):
        button = Node('Save')
        _, api, request = self.fixture([button, Node('Save')])
        with self.assertRaises(RuntimeError): a11y.execute({**request,'action':'invoke','limit':1,'path':'0'}, api)
        self.assertFalse(button.invocations)

    def test_non_click_action_is_not_substituted(self):
        button = Node('Save', actions=('delete',))
        _, api, request = self.fixture([button])
        with self.assertRaises(RuntimeError): a11y.execute({**request,'action':'invoke'}, api)
        self.assertFalse(button.invocations)
