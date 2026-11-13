from pathlib import Path
import tempfile
import unittest
from agent.docs_search import search

class Docs(unittest.TestCase):
    def test_hits_limit_and_boundary(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/"workspace"
            docs=root/"docs"
            docs.mkdir(parents=True)
            (docs/"tasks.md").write_text("Приоритет по умолчанию — mid.\n\nДругое.",encoding="utf-8")
            (root/"private.txt").write_text("приоритет секрет",encoding="utf-8")
            try:
                (docs/"escape.txt").symlink_to(root/"private.txt")
            except OSError:
                pass
            result=search(root,"ПРИОРИТЕТ",1)
            self.assertIn("docs/tasks.md",result)
            self.assertIn("mid",result)
            self.assertNotIn("секрет",result)
            self.assertNotIn("Другое",result)
            with self.assertRaises(ValueError): search(root,"x",6)
