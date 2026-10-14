"""Workflow definitions cannot turn observations into unrestricted execution."""
import json
import unittest
from jarvis_gui.workflows import validate_workflows, match_workflow, WorkflowRunner


class TestWorkflows(unittest.TestCase):
    def definition(self):
        check={'call':{'server':'jarvis-x11','tool':'windows','arguments':{}},'contains':'Editor'}
        return [{'name':'Focus editor','aliases':['focus editor'],'steps':[{
            'call':{'server':'jarvis-x11','tool':'focus_window','arguments':{'window_id':'1'}}, 'after':check}]}]

    def test_exact_alias_only(self):
        definitions=validate_workflows(json.dumps(self.definition()))
        self.assertIsNotNone(match_workflow(definitions,'FOCUS EDITOR'))
        self.assertIsNone(match_workflow(definitions,'please focus editor and delete files'))

    def test_shell_and_non_desktop_servers_are_rejected(self):
        for call in ({'server':'windows-mcp','tool':'PowerShell','arguments':{}},
                     {'server':'shell','tool':'exec','arguments':{}},
                     {'server':'hypruse','tool':'anything','arguments':{}}):
            value=self.definition()
            value[0]['steps'][0]['call']=call
            with self.assertRaises(ValueError):validate_workflows(json.dumps(value))

    def test_checks_cannot_inject_input_and_every_step_needs_verification(self):
        value=self.definition()
        value[0]['steps'][0]['after']['call']['tool']='key'
        with self.assertRaises(ValueError):validate_workflows(json.dumps(value))
        value=self.definition()
        value[0]['steps'][0].pop('after')
        with self.assertRaises(ValueError):validate_workflows(json.dumps(value))

    def test_alias_collisions_and_unbounded_sequences_are_rejected(self):
        value=self.definition()
        with self.assertRaises(ValueError):validate_workflows(json.dumps(value*2))
        value[0]['steps']*=6
        with self.assertRaises(ValueError):validate_workflows(json.dumps(value))

    def test_structured_checks_match_actual_values_without_boolean_coercion(self):
        check={"call":{"server":"jarvis-x11","tool":"active_window","arguments":{}},"path":["id"],"equals":"0x1234"}
        value=self.definition()
        value[0]['steps'][0]['after']=check
        validate_workflows(json.dumps(value))
        result={"content":[{"type":"text","text":json.dumps({"id":"0x1234"})}]}
        self.assertTrue(WorkflowRunner._matches(result,check))
        self.assertFalse(WorkflowRunner._matches({"structuredContent":{"id":"0x4567"}},check))
        check={"path":["value"],"equals":True}
        self.assertFalse(WorkflowRunner._matches({"structuredContent":{"value":1}},check))

    def test_nonfinite_json_and_invalid_paths_are_rejected(self):
        value=self.definition()
        value[0]['steps'][0]['after']={"call":{"server":"jarvis-x11","tool":"active_window"},"path":[True],"equals":1}
        with self.assertRaises(ValueError):validate_workflows(json.dumps(value))
        with self.assertRaises(ValueError):validate_workflows('[NaN]')
