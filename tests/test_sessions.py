import json
import tempfile
import unittest
from pathlib import Path
from agent.sessions import Session

class SessionTest(unittest.TestCase):
    def test_reload_no_duplicate_prompt_and_no_key(self):
        with tempfile.TemporaryDirectory() as d:
            s = Session(Path(d), "demo", "secret-example")
            m = s.load("one")
            m += [{"role":"user","content":"имя: Тимур, secret-example"},
                  {"role":"assistant","content":"Запомнил"}]
            s.save(m)
            self.assertNotIn("secret-example",s.path.read_text())
            self.assertEqual(s.load("two"), [{"role":"system","content":"two"},
                {"role":"user","content":"имя: Тимур, [скрыто]"}, m[-1]])
    def test_invalid_id(self):
        for name in ("../x", "x/y", "CON", "a:b"):
            with self.assertRaises(ValueError): Session(Path("."), name, "")
