"""The fleet manifest parser and its validation.

The grammar is a hand-rolled YAML subset, and a hand-rolled parser's
failure mode is silence — a line that matches no branch simply vanishes.
These tests pin the shapes the fleet relies on, so a parser edit that
drops one fails here instead of in an org's fleet.
"""

import tempfile
import unittest
from pathlib import Path

from context import manifest_mod


def parse(text: str):
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "fleet.yaml"
        path.write_text(text)
        return manifest_mod.parse_manifest(path)


def refusal(text: str) -> str:
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "fleet.yaml"
        path.write_text(text)
        try:
            manifest_mod.parse_manifest(path)
        except SystemExit as e:
            return str(e)
    raise AssertionError("manifest parsed clean; a refusal was expected")


MINIMAL = """\
session: acme
tracker: acme/tracker
loops_cwd: tracker/main

hosts:
  workstation:
    hostname: mac-studio
    default: true
"""


class ManifestGrammarTest(unittest.TestCase):

    def test_top_level_scalars_hosts_and_path_parse(self):
        m = parse(MINIMAL)
        self.assertEqual(m["top"]["session"], "acme")
        self.assertEqual(m["top"]["tracker"], "acme/tracker")
        self.assertEqual(m["hosts"]["workstation"]["hostname"], "mac-studio")
        self.assertEqual(m["root"], m["path"].parent)
        self.assertEqual(m["path"].name, "fleet.yaml")

    def test_full_line_comments_and_blanks_are_ignored(self):
        m = parse("# a comment\n\n" + MINIMAL)
        self.assertEqual(m["top"]["session"], "acme")

    def test_teams_and_books_sections_parse(self):
        m = parse(MINIMAL + """\
teams:
  op@workstation: workstation

books:
  widget:
    book: books/widget
    repo: widget/main
""")
        self.assertEqual(m["teams"], {"op@workstation": "workstation"})
        self.assertEqual(m["books"]["widget"]["repo"], "widget/main")

    def test_a_top_level_key_ends_the_open_section(self):
        m = parse(MINIMAL + "teams:\n  a@workstation: workstation\nproject: Fly\n")
        self.assertEqual(m["top"]["project"], "Fly")
        self.assertNotIn("project", m["teams"])


class ManifestValidationTest(unittest.TestCase):

    def test_conductors_cwd_is_refused_with_the_rename(self):
        message = refusal(MINIMAL + "conductors_cwd: tracker/main\n")
        self.assertIn("`conductors_cwd:` retired", message)
        self.assertIn("loops_cwd", message)

    def test_conductor_model_is_refused(self):
        message = refusal(MINIMAL + "conductor_model: opus\n")
        self.assertIn("`conductor_model:` retired", message)

    def test_teams_host_must_exist(self):
        message = refusal(MINIMAL + "teams:\n  op@laptop: laptop\n")
        self.assertIn("'laptop' is not in hosts:", message)


if __name__ == "__main__":
    unittest.main()
