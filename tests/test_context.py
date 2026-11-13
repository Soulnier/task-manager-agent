import unittest
from agent import context as ctx

class Estimate(unittest.TestCase):
    def test_tool_schema_and_arguments_count(self):
        msgs = [{"role":"user","content":"файл"}]
        self.assertGreater(ctx.estimate(msgs,[{"name":"read_file"}]),ctx.estimate(msgs,[]))
        self.assertGreater(ctx.estimate(msgs+[{"role":"assistant","tool_calls":[{"arguments":"z"*100}]}],[]),ctx.estimate(msgs,[]))

system = {"role":"system","content":"правила"}
def user(t): return {"role":"user","content":t}
def answer(t): return {"role":"assistant","content":t}

class Budget(unittest.TestCase):
    def test_whole_turn_only(self):
        old = [user("x"*500), {"role":"assistant","tool_calls":[{"id":"a"},{"id":"b"}]},
               {"role":"tool","tool_call_id":"a","content":"a"},
               {"role":"tool","tool_call_id":"b","content":"b"}, answer("готово")]
        latest = [user("новый"),answer("ответ")]
        data = [system]+old+latest
        view = ctx.ensure_context_budget(data, [], ctx.estimate([system]+latest))
        self.assertEqual(view,[system]+latest)
        self.assertEqual(data,[system]+old+latest)
    def test_active_turn_too_big(self):
        with self.assertRaises(ValueError):
            ctx.ensure_context_budget([system,user("x"*2000)],[],50)
