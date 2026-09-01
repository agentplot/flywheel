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

    def test_the_credentials_block_parses(self):
        # Problem 10 (willdan fleet): the org's app id squatted in
        # dispatch.env and every non-dispatch actor re-read it by hand.
        m = parse(MINIMAL + """\
credentials:
  FLYWHEEL_GH_APP_ID: 4562912
  FLYWHEEL_GH_APP_KEY: op:Vault/willdan-app.pem
""")
        self.assertEqual(m["credentials"]["FLYWHEEL_GH_APP_ID"], "4562912")
        self.assertEqual(m["credentials"]["FLYWHEEL_GH_APP_KEY"],
                         "op:Vault/willdan-app.pem")

    def test_an_absent_credentials_block_is_an_empty_map(self):
        self.assertEqual(parse(MINIMAL)["credentials"], {})

    def test_an_unknown_credentials_key_is_refused_by_name(self):
        message = refusal(MINIMAL + "credentials:\n  GH_TOKEN: nope\n")
        self.assertIn("GH_TOKEN", message)
        self.assertIn("FLYWHEEL_GH_APP_ID", message)


DISPATCH = """\
dispatch:
  host: workstation
  model: opus[1m]
  channels: plugin:discord@claude-plugins-official
  env:
    DISCORD_STATE_DIR: .flywheel/discord
    EXTRA: value
  prompt: "You are dispatch. Wait for input."
"""


class DispatchBlockTest(unittest.TestCase):

    def test_the_full_block_parses(self):
        d = parse(MINIMAL + DISPATCH)["dispatch"]
        self.assertEqual(d["host"], "workstation")
        self.assertEqual(d["model"], "opus[1m]")
        self.assertEqual(d["channels"], "plugin:discord@claude-plugins-official")
        self.assertEqual(d["env"], {"DISCORD_STATE_DIR": ".flywheel/discord",
                                    "EXTRA": "value"})
        self.assertEqual(d["prompt"], "You are dispatch. Wait for input.")

    def test_absent_block_parses_to_an_empty_dict(self):
        self.assertEqual(parse(MINIMAL)["dispatch"], {})

    def test_host_is_optional(self):
        d = parse(MINIMAL + "dispatch:\n  prompt: \"hi\"\n")["dispatch"]
        self.assertNotIn("host", d)

    def test_a_two_space_key_closes_the_env_map(self):
        d = parse(MINIMAL + """\
dispatch:
  env:
    A: 1
  prompt: "hi"
""")["dispatch"]
        self.assertEqual(d["env"], {"A": "1"})
        self.assertEqual(d["prompt"], "hi")

    def test_a_top_level_key_closes_the_block(self):
        m = parse(MINIMAL + "dispatch:\n  prompt: \"hi\"\nproject: Fly\n")
        self.assertEqual(m["top"]["project"], "Fly")
        self.assertNotIn("project", m["dispatch"])

    def test_an_unknown_dispatch_key_is_refused_by_name(self):
        message = refusal(MINIMAL + "dispatch:\n  prompt: \"hi\"\n  cwd: x\n")
        self.assertIn("dispatch: unknown key `cwd:`", message)

    def test_a_block_without_prompt_is_refused(self):
        message = refusal(MINIMAL + "dispatch:\n  model: opus\n")
        self.assertIn("dispatch: missing prompt", message)

    def test_a_dispatch_host_outside_hosts_is_refused(self):
        message = refusal(MINIMAL + "dispatch:\n  host: cloud\n  prompt: \"hi\"\n")
        self.assertIn("dispatch: host 'cloud' is not in hosts:", message)

    def test_the_shipped_template_parses_clean(self):
        template = (Path(__file__).resolve().parents[1]
                    / "skills" / "fleet" / "template-fleet.yaml")
        m = parse(template.read_text())
        self.assertEqual(m["dispatch"]["channels"],
                         "plugin:discord@claude-plugins-official")


class ManifestValidationTest(unittest.TestCase):

    def test_conductors_cwd_is_refused_with_the_rename(self):
        message = refusal(MINIMAL + "conductors_cwd: tracker/main\n")
        self.assertIn("`conductors_cwd:` retired", message)
        self.assertIn("loops_cwd", message)

    def test_conductor_model_is_refused(self):
        message = refusal(MINIMAL + "conductor_model: opus\n")
        self.assertIn("`conductor_model:` retired", message)

    def test_actors_is_refused_naming_the_dispatch_block(self):
        message = refusal(MINIMAL + """\
actors:
  - name: dispatch
    profile: flywheel-dispatch
    host: workstation
    state: running
    cwd: tracker/main
""")
        self.assertIn("`actors:` retired", message)
        self.assertIn("`dispatch:` block", message)
        self.assertIn("flywheel dispatch", message)

    def test_teams_host_must_exist(self):
        message = refusal(MINIMAL + "teams:\n  op@laptop: laptop\n")
        self.assertIn("'laptop' is not in hosts:", message)


if __name__ == "__main__":
    unittest.main()
