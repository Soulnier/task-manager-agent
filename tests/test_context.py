import unittest
from agent import context as ctx

class Estimate(unittest.TestCase):
    def test_tool_schema_and_arguments_count(self):
        msgs = [{"role":"user","content":"файл"}]
        self.assertGreater(ctx.estimate(msgs,[{"name":"read_file"}]),ctx.estimate(msgs,[]))
        self.assertGreater(ctx.estimate(msgs+[{"role":"assistant","tool_calls":[{"arguments":"z"*100}]}],[]),ctx.estimate(msgs,[]))
