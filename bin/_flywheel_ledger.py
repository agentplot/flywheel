"""The run ledger — the facts a loop run records as it happens.

One JSONL file per loop process under
`<state-home>/<org>/observations/<scope>/`, where scope is `bolt-<slug>`,
`intent-<slug>`, or `dispatch`. The loop writes four kinds of entry —
`precondition`, `expect`, `actual`, `note` — and two markdown documents are
rendered from them beside the JSONL: the plan (`<run>.plan.md`, preconditions
and expectations only, what the run intends, for the operator to read) and the
report (`<run>.report.md`, expected and actual joined by step, mismatches
first).

Observation never gates: the plan document is written for the operator to
read, and the run proceeds. Every write is best-effort: observation must
never kill a pass. A failed write is logged, counted, and noted in the
report.
"""

import json
import os
import time
from pathlib import Path


def state_home():
    """The same root the server's logs use: XDG_STATE_HOME when set,
    ~/.local/state otherwise, with FLYWHEEL_STATE_HOME as the override."""
    home = os.environ.get("FLYWHEEL_STATE_HOME")
    if home:
        return Path(home)
    base = os.environ.get("XDG_STATE_HOME")
    root = Path(base) if base else Path.home() / ".local" / "state"
    return root / "flywheel"


def observations_root(org, home=None):
    return (home or state_home()) / org / "observations"


class RunLedger:
    """One loop run's ledger."""

    def __init__(self, root, scope, run_id=None, clock=time.time, log=None):
        self.dir = Path(root) / scope
        self.scope = scope
        self._clock = clock
        self._log = log or (lambda message: None)
        stamp = time.strftime("%Y%m%dT%H%M%S", time.gmtime(clock()))
        self.run_id = run_id or f"{stamp}-{os.getpid()}"
        self.path = self.dir / f"{self.run_id}.jsonl"
        self.entries = []
        self.write_failures = 0

    # -- entries -----------------------------------------------------------

    def _append(self, entry):
        entry = {"ts": self._clock(), **entry}
        self.entries.append(entry)
        try:
            self.dir.mkdir(parents=True, exist_ok=True)
            with open(self.path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, separators=(",", ":")) + "\n")
        except OSError as err:
            self.write_failures += 1
            self._log(f"ledger write failed ({self.path}): {err}")

    def precondition(self, text):
        self._append({"kind": "precondition", "text": str(text)})

    def expect(self, step, trigger, expected):
        self._append({"kind": "expect", "step": step,
                      "trigger": trigger, "expected": expected})

    def actual(self, step, outcome, ok=True):
        self._append({"kind": "actual", "step": step,
                      "outcome": outcome, "ok": bool(ok)})

    def note(self, text):
        self._append({"kind": "note", "text": str(text)})

    # -- rendering ---------------------------------------------------------

    def write_plan(self, plan):
        """The drive plan, rendered for the operator to read. Never a gate:
        the run proceeds; the document is the record of what it intends."""
        if not plan:
            return None
        lines = [f"# {self.scope} — plan for run {self.run_id}", ""]
        pre = [e["text"] for e in self.entries if e["kind"] == "precondition"]
        if pre:
            lines += ["preconditions: " + " · ".join(pre), ""]
        lines += ["| step | trigger | expected |", "|---|---|---|"]
        lines += [f"| {e.get('step', '')} | {e.get('trigger', '')} "
                  f"| {e.get('expected', '')} |" for e in plan]
        return self._write_doc(f"{self.run_id}.plan.md", "\n".join(lines) + "\n")

    def write_report(self):
        """The expected-vs-actual table, mismatched rows first."""
        pre = [e["text"] for e in self.entries if e["kind"] == "precondition"]
        expects = [e for e in self.entries if e["kind"] == "expect"]
        actuals = [e for e in self.entries if e["kind"] == "actual"]
        notes = [e["text"] for e in self.entries if e["kind"] == "note"]
        unclaimed = list(actuals)
        rows = []
        for e in expects:
            hit = next((a for a in unclaimed if a["step"] == e["step"]), None)
            if hit is not None:
                unclaimed.remove(hit)
                mark = "✓" if hit["ok"] else "✗"
                rows.append((not hit["ok"], e["step"], e["trigger"],
                             e["expected"], f"{mark} {hit['outcome']}"))
            else:
                rows.append((True, e["step"], e["trigger"],
                             e["expected"], "✗ never happened"))
        rows += [(True, a["step"], "", "(unexpected)",
                  f"{'✓' if a['ok'] else '✗'} {a['outcome']}")
                 for a in unclaimed]
        rows.sort(key=lambda r: not r[0])       # mismatches first, stable
        mismatched = sum(1 for r in rows if r[0])

        lines = [f"# {self.scope} — run {self.run_id}", ""]
        if pre:
            lines += ["preconditions: " + " · ".join(pre), ""]
        if rows:
            lines.append(
                f"{mismatched} of {len(rows)} step(s) diverged from expectation."
                if mismatched else "The run matched expectations.")
            lines += ["", "| step | trigger | expected | actual |",
                      "|---|---|---|---|"]
            lines += [f"| {s} | {t} | {x} | {a} |" for _, s, t, x, a in rows]
        else:
            lines.append("No actions this run.")
        for text in notes:
            lines += ["", f"> {text}"]
        if self.write_failures:
            lines += ["", f"> {self.write_failures} ledger write(s) failed — "
                          "the JSONL under-records this run."]
        return self._write_doc(f"{self.run_id}.report.md", "\n".join(lines) + "\n")

    def _write_doc(self, name, text):
        try:
            self.dir.mkdir(parents=True, exist_ok=True)
            path = self.dir / name
            path.write_text(text, encoding="utf-8")
            return path
        except OSError as err:
            self.write_failures += 1
            self._log(f"ledger doc write failed ({name}): {err}")
            return None


class NullLedger:
    """The absent ledger: records nothing. The default seam for callers
    (and tests) that never asked for observation."""

    run_id = None
    entries = ()
    write_failures = 0

    def precondition(self, text):
        pass

    def expect(self, step, trigger, expected):
        pass

    def actual(self, step, outcome, ok=True):
        pass

    def note(self, text):
        pass

    def write_plan(self, plan):
        return None

    def write_report(self):
        return None
