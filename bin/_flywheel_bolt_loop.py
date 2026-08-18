"""#72 — the construction loop, as an ordinary program.

    query+guards -> spec (per strategy) -> apply -> verify -> merge
    -> land -> bookkeeping -> re-query ... STOP

`bin/flywheel-bolt-loop` is the command; this is the loop it runs. It
stands on the wave-1 substrate — `_flywheel_inbox` for the tracker and its
filters, `_flywheel_sessions` for launching and supervising work — and
adds the stages, the guards and the arithmetic between them.

**The program reads state and enforces contracts; sessions judge.** That
one line decides every design question in this file, and two consequences
are worth stating before the code:

*Stage outcomes are read from the world, never parsed out of a session's
prose.* The record's contract for a construction session is objective —
"settle plus the deliverable contract (change validates, commit on
branch, comment on item)" — so this asks `openspec validate --strict`,
`git rev-list` and the item's own comments. A merge-back succeeded when
the branch is an ancestor of the bolt branch, which `git merge-base`
answers; a session saying "green" is not evidence and is not read as any.

*Judgment is asked for in a session and answered in one parsed line, and
the loop performs the write.* Four places need it: the construction work
itself; the
plan-mode approval; and which merge criterion failed at landing. In each
the session supplies a verdict and this program supplies the writes, so
that what changed on the tracker is always something the loop can name.

Stateless by construction: every cycle re-reads the tracker and the
records, and the guards are idempotent, so a server that restarts this
process freely loses nothing. The one piece of state that cannot be
recomputed — when a session was launched, which the 4-hour stall budget
is measured from — is written to the tracker as a marker on the item and
recovered from there, because the tracker is the only bus.

*Per-item progress is a label, and the tree is what says so.* Each of the
four boundaries above writes one `stage:*` label on the batch's items —
planned, built, verified, merged — and `guard_stages` re-derives the two
git can answer for at the head of every cycle, so the labels self-heal
across the restart above rather than being remembered. The stage sequence
itself is the bound type's `loop:` block, which is what makes
`bolt-direct` — spec, build, merge, land, no verify — a named config
rather than a branch in this file.
"""

import hashlib
import json
import os
import re
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _flywheel_inbox as inbox        # noqa: E402
import _flywheel_ledger as obs         # noqa: E402
import _flywheel_sessions as sessions  # noqa: E402


# ---------------------------------------------------------------------------
# What the loop is made of
# ---------------------------------------------------------------------------

PROFILE = "flywheel-construction-session"

#: Every session launch names its model (herdr.md). Construction types run
#: `opus[1m]`; the mechanical stages and the one-line judgments do not.
STAGE_MODELS = {
    "spec": "opus[1m]",
    "build": "opus[1m]",
    "verify": "opus[1m]",
    "merge": "sonnet",
    "land": "opus[1m]",
    "scaffold": "sonnet",
    "plan": "sonnet",      # a plan against a claim
}

#: The type's strategy is the sequence of spec commands the loop runs on one
#: session. The hooks a type declares are the boundaries between them; they
#: are where extensions attach when extensions arrive.
STRATEGIES = {
    "ff": ("/opsx:ff",),
    "new+ff": ("/opsx:new", "/opsx:ff"),
    "new+continue": ("/opsx:new", "/opsx:continue"),
}

#: `new+continue` generates one artifact per command, so the loop repeats
#: the last invocation until the change validates. Bounded because an
#: unbounded round is how a loop stops terminating.
MAX_CONTINUE_ROUNDS = 8

#: The design record's two-rounds-then-pause shape, in the two places it
#: applies: a returned plan and a repeated verify finding.
MAX_PLAN_RETURNS = 2
MAX_FIX_ROUNDS = 2

#: The session-to-loop file channels, relative to the batch worktree. A
#: report is a file whose lifecycle the LOOP owns — deleted before the
#: session that writes it launches, read after it settles — never a scrape
#: of the pane (#200). The single word below is verify's "nothing found".
VERIFY_REPORT = ".flywheel/verify.md"
REVIEW_RULING = ".flywheel/review.json"
NO_FINDINGS = "NONE"

#: One retry of a failed landing per run: the first failure births the fix
#: item, the second is the andon cord's business, not another item's.
MAX_LANDING_ATTEMPTS = 2

#: A session's launch time, on the item, so a restarted loop measures the
#: stall budget from the launch rather than from its own start. Same shape
#: as the andon marker in `_flywheel_inbox`, and read the same way: code,
#: not judgment — half a marker is not a launch record.
SESSION_OPEN = "<!-- flywheel:session"
#: A clean verify verdict, made durable on the item so a restarted loop
#: re-buys no judgment for a branch that has not moved since.
VERIFIED_MARK = "<!-- flywheel:verified"
_VERIFIED = re.compile(
    r"<!--\s*flywheel:verified\s+sha=\"(?P<sha>[0-9a-f]+)\"\s*-->")
_SESSION = re.compile(
    r"<!--\s*flywheel:session\s+name=\"(?P<name>[^\"]+)\"\s+"
    r"started=\"(?P<started>\d+)\"\s*-->"
)

#: The one line a judgment session's answer is read from. Anything else is
#: unreadable on purpose: a verdict the loop cannot parse is a verdict it
#: does not act on.
_PLAN = re.compile(r"^(?P<verdict>APPROVED|RETURNED)\b[ \t]*:?[ \t]*(?P<why>.*)$",
                   re.MULTILINE)


class LoopError(Exception):
    """The run cannot proceed on the parameters it was given."""


# ---------------------------------------------------------------------------
# The type as a named loop config
# ---------------------------------------------------------------------------

#: The stages a type runs when its `loop:` block declares none. The three
#: types that shipped before `bolt-direct` declare no `stages:` key, so the
#: default is exactly what they have always run.
DEFAULT_STAGES = ("spec", "build", "verify", "merge", "land")


@dataclass(frozen=True)
class LoopConfig:
    """A bolt type's `loop:` block: what the program does differently."""

    name: str
    strategy: str = "ff"
    hooks: tuple = ()
    extensions: tuple = ()
    plan_mode: str = None
    stages: tuple = DEFAULT_STAGES

    @property
    def plan_mode_available(self):
        """Plan-mode is bolt-quick-only, and the type says so itself."""
        return self.plan_mode == "available"

    def runs(self, stage):
        """Does this type's cycle run that stage?

        `bolt-direct` is a fourth NAMED CONFIG rather than a branch in the
        cycle's code: it omits verify by declaring a stage set without it,
        so the next type that varies the sequence declares its own set and
        adds no second flag here.

        Every stage the cycle runs is gated on this — spec, build, verify
        and merge in `cycle`, and land in `landing_wanted`. Gating only the
        one stage a shipped type happens to omit would make that sentence
        true of `bolt-direct` and false of the type after it, which is the
        shape a reader would trust and be wrong about.
        """
        return stage in self.stages

    @property
    def invocations(self):
        try:
            return STRATEGIES[self.strategy]
        except KeyError:
            raise LoopError(
                f"{self.name}: unknown strategy {self.strategy!r} — "
                f"one of {', '.join(sorted(STRATEGIES))}")

    def validate(self):
        """Raise on a stage set the cycle cannot run. Returns self.

        `strategy` has raised on an unknown value since the type config
        existed; `stages` did not, so a typo — `stages: [spec, buld,
        merge, land]` — silently produced a type that skips the build
        stage and writes no `stage:built`, which is the same downgrade a
        declaration is refused for. An unknown stage name is a mistake,
        never a request, so it is named rather than dropped.
        """
        unknown = [s for s in self.stages if s not in DEFAULT_STAGES]
        if unknown:
            raise LoopError(
                f"{self.name}: unknown stage(s) {', '.join(map(repr, unknown))} "
                f"in its declared set — one of {', '.join(DEFAULT_STAGES)}. "
                f"A stage the cycle does not run is a stage silently skipped.")
        if not self.stages:
            raise LoopError(f"{self.name}: declares an empty stage set")
        return self


def parse_loop_block(text):
    """The `loop:` block out of a `schema.yaml`, by hand.

    Hand-parsed for a reason each schema records in its own comment:
    openspec 1.8.0 parses the file and then DROPS this block — its
    workflow-schema validator is a zod object in strip mode, so an unknown
    top-level key is neither an error nor preserved. "Whatever ends up
    reading this block MUST read schema.yaml itself", and this is that
    reader. It handles the shape the schemas actually use — scalars, flow
    lists, and dash lists — and nothing else, because anything richer would
    be a YAML parser this repo has no dependency budget for.
    """
    lines, inside = [], False
    for line in (text or "").splitlines():
        if not inside:
            if re.match(r"^loop:\s*(#.*)?$", line):
                inside = True
            continue
        if not line.strip() or line.lstrip().startswith("#"):
            continue                           # never ends the block
        if not line[:1].isspace():
            break                              # dedent ends the block
        lines.append(line)
    return _parse_mapping(lines, nested=True)


def _scalar(raw):
    return raw.strip().strip("'\"").strip()


def _parse_mapping(lines, nested=False):
    """The three YAML shapes the flywheel corners use, and nothing else.

    Scalars, flow lists and dash lists — one parser, so `parse_loop_block`
    and `read_binding` cannot disagree about what a key looks like. A key
    the parser cannot SEE is a key nothing can refuse, so teaching this
    about a new shape teaches every reader at once. Anything richer would
    be a YAML parser this repo has no dependency budget for.

    `nested` matches keys after stripping (a schema's indented `loop:`
    block); a top-level file keeps keys at column 0, so a nested map's
    indented keys open no entry. A key with no value on its line opens a
    block list, and is recorded even if no `- ` item follows — an empty
    declaration is still a declaration and still refusable.
    """
    block, pending = {}, None
    for line in lines:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        stripped = line.strip()
        if stripped.startswith("- "):
            if pending is not None:
                block.setdefault(pending, []).append(_scalar(stripped[2:]))
            continue
        match = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$",
                         stripped if nested else line)
        if not match:
            continue
        key, raw = match.group(1), match.group(2).strip()
        if raw.startswith("["):
            block[key] = [_scalar(v) for v in raw.strip("[]").split(",") if v.strip()]
            pending = None
        elif raw:
            block[key] = _scalar(raw)
            pending = None
        else:
            block[key] = []
            pending = key
    return block


def read_schema_config(path):
    """A `LoopConfig` from a schema.yaml on disk."""
    text = Path(path).read_text()
    block = parse_loop_block(text)
    name = ""
    for line in text.splitlines():
        match = re.match(r"^name:\s*(.+)$", line)
        if match:
            name = _scalar(match.group(1))
            break
    return LoopConfig(
        name=name or Path(path).parent.name,
        strategy=block.get("strategy", "ff"),
        hooks=tuple(block.get("hooks", ())),
        extensions=tuple(block.get("extensions", ())),
        plan_mode=block.get("plan_mode") or None,
        stages=tuple(block.get("stages") or DEFAULT_STAGES),
    )


def schema_roots(repo_dir):
    """Where a type's schema lives, nearest copy first.

    A repo's own copy shadows the installed one — that is the schemas'
    stated user-edit channel — and the installed user schemas are where
    `bin/install-schemas` publishes the plugin's.
    """
    repo = Path(repo_dir)
    import os
    data = os.environ.get("XDG_DATA_HOME") or (Path.home() / ".local" / "share")
    return [
        repo / "openspec" / "schemas",
        repo / "schemas",
        Path(data) / "openspec" / "schemas",
    ]


def find_schema(type_name, repo_dir):
    for root in schema_roots(repo_dir):
        candidate = Path(root) / type_name / "schema.yaml"
        if candidate.exists():
            return candidate
    return None


def load_type(type_name, repo_dir):
    path = find_schema(type_name, repo_dir)
    if path is None:
        raise LoopError(
            f"no schema.yaml for type {type_name!r} under "
            + ", ".join(str(r) for r in schema_roots(repo_dir)))
    return read_schema_config(path)


def read_binding(change_dir):
    """`openspec/changes/<slug>/.openspec.yaml` — the type this change bound.

    Binding a schema IS choosing the type, so the binding on disk is what
    the loop believes, ahead of anything it was told on the command line.

    Reads scalars, flow lists and dash lists — the same three shapes
    `parse_loop_block` handles, and for the same reason. A key this parser
    cannot SEE is a key nothing can refuse: `refuse_stage_declaration`
    rejects a `stages:` declaration only if it is in this dict, so a
    block-style list would have been ignored rather than refused, which is
    exactly the outcome that function's docstring argues against.
    """
    path = Path(change_dir) / ".openspec.yaml"
    if not path.exists():
        return {}
    return _parse_mapping(path.read_text().splitlines())


def plan_mode_declared(binding=None, milestone_description=None, flag=None):
    """Whether this BOLT declares the plan-mode path.

    Declared per bolt — "the milestone description, or the handoff plan" —
    and never by a type, so the carriers are read in the order they bind:
    the operator's flag wins outright in both directions, then an explicit
    `plan_mode:` in the change's binding, then the phrase the release writes
    into the milestone description.

    **`skip_specs` is not one of them**, though it reads like one. Measured
    on this repo, 2026-08-13: every bolt and intent change carries
    `skip_specs: true`, including `bolt-default` ones — it says the record
    itself has no spec deltas, not that its items go unspecced. Reading it
    as the declaration turned a bolt-default bolt into a plan-mode run on
    the first live invocation.
    """
    if flag is not None:
        return bool(flag)
    binding = binding or {}
    if "plan_mode" in binding:
        return str(binding["plan_mode"]).lower() in ("true", "yes", "available")
    return bool(re.search(r"plan[- ]mode path", milestone_description or "", re.I))


#: The keys a bolt might try to vary its stage set with. Read only so they
#: can be REFUSED — the stage set is the bound type's, never the bolt's.
STAGE_DECLARATION_KEYS = ("stages", "verify", "skip_verify")


def refuse_stage_declaration(binding, config):
    """A per-bolt stage declaration is refused, not honoured quietly.

    Symmetric with `resolve_plan_mode`, and for the same reason: **the bolt
    type is the scrutiny the release approved, and no program downgrades
    it.** Skipping verify is `bolt-direct`'s property alone, exactly as the
    plan-mode path is `bolt-quick`'s, so a `stages:` or `verify:` key in a
    change's binding raises here rather than being ignored.

    Ignoring it would satisfy the letter of "not reachable" and lose the
    point: a bolt that wrote `verify: false` into its binding and watched
    verify run anyway learns that the declaration is noise, and the next
    reader wires it up. A refusal says which rule it broke.

    Raises `LoopError`; returns the config unchanged when the binding is
    clean, so callers can use it inline.
    """
    for key in STAGE_DECLARATION_KEYS:
        if key in (binding or {}):
            raise LoopError(
                f"the binding declares {key!r}, but the stage set is the bound "
                f"type's and not the bolt's — {config.name!r} runs "
                f"{', '.join(config.stages)}. A type that omits verify is a "
                f"named config (bolt-direct); the bolt type is the scrutiny "
                f"the release approved, and no program downgrades it.")
    return config


def refuse_type_disagreement(binding, type_name):
    """A command-line `--type` that contradicts the binding is refused.

    The same rule `refuse_stage_declaration` states, closing the other route
    to it: **the bolt type is the scrutiny the release approved, and no
    program downgrades it.** The declaration door is shut, but the entry
    point resolves the type as the flag first and the binding second, so a
    flag alone could resolve a bolt bound to `bolt-default` as `bolt-direct`
    and drop verify with nothing recorded anywhere — the bolt merging and
    landing with no `stage:verified` while its binding still says otherwise.

    This is also what `read_binding`'s own docstring already claims: the
    binding on disk is what the loop believes, ahead of anything it was told
    on the command line.

    The disagreement is refused rather than the precedence reversed.
    Reversing it would make `--type` silently useless, which is a worse kind
    of quiet than the one being fixed. The legitimate need behind the flag —
    a bolt whose binding is wrong — is met by correcting the binding, which
    is a recorded act on disk, unlike a flag that leaves no trace.

    Where the binding records no schema the flag is honoured: there is no
    approval for it to contradict, and refusing would leave an unbound bolt
    unable to run at all. Returns the name to use, so callers can use it
    inline.
    """
    bound = (binding or {}).get("schema")
    if type_name and bound and type_name != bound:
        raise LoopError(
            f"the binding records type {bound!r} but {type_name!r} was named on "
            f"the command line — the binding on disk is what the loop believes, "
            f"ahead of anything it was told on the command line. The bolt type "
            f"is the scrutiny the release approved, and no program downgrades "
            f"it; correct the binding, which is a recorded act, rather than "
            f"passing a flag that leaves no trace on the tracker.")
    return type_name or bound or "bolt-quick"


def resolve_plan_mode(declared, config):
    """Permitted only where the bound type says `plan_mode: available`.

    The bolt type is the scrutiny the release approved, and no program
    downgrades it. So a declaration against bolt-default
    or bolt-adversarial is refused here rather than honoured quietly.
    """
    if not declared:
        return False
    if not config.plan_mode_available:
        raise LoopError(
            f"the plan-mode path is declared but type {config.name!r} does not "
            f"offer it (plan_mode: {config.plan_mode!r}) — plan-mode is "
            f"bolt-quick-only, and the type is the scrutiny the release approved")
    return True


# ---------------------------------------------------------------------------
# The tracker: the wave-1 reads, plus the writes a landing needs
# ---------------------------------------------------------------------------

class BoltTracker(inbox.Tracker):
    """`_flywheel_inbox.Tracker` plus the four writes this loop makes.

    Milestone moves, closes and item creation go through the REST API
    rather than `gh issue ...` for one mechanical reason: the shared `gh`
    helper parses stdout as JSON, and `gh issue create` prints a URL.
    """

    def _api(self, path, method=None, body=None):
        args = ["api"]
        if method:
            args += ["--method", method]
        args.append(f"/repos/{self.org}/{self.repo}{path}")
        if body is not None:
            args += ["--input", "-"]
        return self._gh(self.token, *args, input_json=body)

    def milestones(self, state="all"):
        pages = self._gh(
            self.token, "api",
            f"/repos/{self.org}/{self.repo}/milestones?state={state}&per_page=100",
            "--paginate", "--slurp")
        return [m for page in pages for m in page]

    def milestone(self, title):
        for row in self.milestones():
            if row.get("title") == title:
                return row
        return None

    def set_milestone(self, number, title):
        row = self.milestone(title)
        if row is None:
            raise LoopError(f"no milestone titled {title!r} to move #{number} to")
        self._api(f"/issues/{number}", "PATCH", {"milestone": row["number"]})

    def clear_milestone(self, number):
        self._api(f"/issues/{number}", "PATCH", {"milestone": None})

    def close(self, number, comment=None, reason=inbox.CLOSED_DONE):
        """Close with a reason, always: one `closed:*` label and the evidence.

        `reason` defaults to `closed:done` so every existing caller keeps
        its behaviour; the merge boundary passes `closed:merged`.
        """
        self.reclose(number, comment, was=None, now=reason)

    def reclose(self, number, comment=None, was=None, now=inbox.CLOSED_DONE):
        """Swap one `closed:*` reason for another on an already-closed item.

        The landing's upgrade. It must not depend on the item being open —
        it was closed at merge-back — and it must never leave the item
        carrying both reasons or neither. That is an "at every moment"
        invariant, so the swap is ONE call: add-then-remove would satisfy
        "never neither" and open a window in which the item carries both,
        and a concurrent reader of the Landed view (`is:closed
        label:closed:done`) would see it as landed early.

        The `state: closed` PATCH is repeated because an item that reached
        the landing without ever merging back (a bolt landed by another
        path, an item closed by hand) still has to end closed with the SHA
        on it.
        """
        if comment:
            self.comment(number, comment)
        self.swap_label(number, add=now, remove=was)
        self._api(f"/issues/{number}", "PATCH", {"state": "closed"})

    def create_item(self, title, body, labels=(), milestone=None):
        payload = {"title": title, "body": body, "labels": list(labels)}
        if milestone:
            row = self.milestone(milestone)
            if row is not None:
                payload["milestone"] = row["number"]
        created = self._api("/issues", "POST", payload)
        return created.get("number")


class ReadOnlyTracker:
    """Reads pass through; every write raises.

    `--dry-run`'s "writes nothing" is a property of the object rather than
    a promise in a docstring — the bolt's own acceptance asks for a no-work
    exit *observed* to write nothing, and an observation you could only make
    by trusting the code is not one.
    """

    WRITES = ("add_label", "remove_label", "swap_label", "comment",
              "set_milestone", "clear_milestone", "close", "reclose",
              "create_item", "create_milestone", "attach_sub_issue",
              "clear_board_status")

    def __init__(self, tracker):
        self._tracker = tracker
        self.refused = []

    def __getattr__(self, name):
        if name in self.WRITES:
            def refuse(*args, **kwargs):
                self.refused.append((name, args))
                raise LoopError(f"dry run: refused to {name}{args}")
            return refuse
        return getattr(self._tracker, name)


class FixtureTracker:
    """A `workflows/fixtures/*-tracker.json` file, used as the tracker.

    The file IS the tracker: reads come from it and writes go back to it,
    so a cycle can be exercised end to end — the dry-cycle property above
    all — without a token, a network or a live milestone.
    """

    def __init__(self, path, write_back=True):
        self.path = Path(path)
        self.raw = json.loads(self.path.read_text())
        self.write_back = write_back
        self.writes = []

    # -- reads -------------------------------------------------------------

    def _item(self, number):
        for raw in self.raw.get("items", ()):
            if raw["number"] == number:
                return raw
        return None

    def snapshot(self, milestone=None, with_edges=True):
        snap = inbox.TrackerSnapshot.from_fixture(self.path)
        if milestone:
            snap = inbox.TrackerSnapshot(
                items=[i for i in snap.items if i.milestone == milestone],
                batches=snap.batches, closed_milestones=snap.closed_milestones,
                milestone=milestone, plan_cards=snap.plan_cards)
        return snap

    def comments(self, number):
        raw = self._item(number) or {}
        return [c if isinstance(c, dict) else {"body": c}
                for c in raw.get("comments", ())]

    def has_label(self, number, label):
        raw = self._item(number) or {}
        return label in raw.get("labels", ())

    def labels(self, number):
        raw = self._item(number) or {}
        return set(raw.get("labels", ()))

    def closed_with(self, number, label):
        raw = self._item(number) or {}
        return raw.get("state") == "closed" and label in raw.get("labels", ())

    def closed(self, number):
        raw = self._item(number) or {}
        return raw.get("state") == "closed"

    def milestone(self, title):
        return {"title": title, "number": 1}

    # -- writes ------------------------------------------------------------

    def _record(self, kind, number, detail=""):
        self.writes.append((kind, number, detail))
        if self.write_back:
            self.path.write_text(json.dumps(self.raw, indent=2) + "\n")

    def add_label(self, number, label):
        raw = self._item(number)
        if raw is not None and label not in raw.setdefault("labels", []):
            raw["labels"].append(label)
        self._record("add_label", number, label)

    def remove_label(self, number, label):
        raw = self._item(number)
        if raw is not None and label in raw.get("labels", ()):
            raw["labels"].remove(label)
        self._record("remove_label", number, label)

    def swap_label(self, number, add, remove=None):
        raw = self._item(number)
        if raw is not None:
            if add not in raw.setdefault("labels", []):
                raw["labels"].append(add)
            if remove and remove != add and remove in raw["labels"]:
                raw["labels"].remove(remove)
        self._record("swap_label", number,
                     f"+{add}" + (f" -{remove}" if remove and remove != add else ""))

    def comment(self, number, body):
        raw = self._item(number)
        if raw is not None:
            raw.setdefault("comments", []).append({"body": body})
        self._record("comment", number, body[:60])

    def set_milestone(self, number, title):
        raw = self._item(number)
        if raw is not None:
            raw["milestone"] = title
        self._record("set_milestone", number, title)

    def clear_milestone(self, number):
        raw = self._item(number)
        if raw is not None:
            raw["milestone"] = None
        self._record("clear_milestone", number, "")

    def close(self, number, comment=None, reason=inbox.CLOSED_DONE):
        raw = self._item(number)
        if comment and raw is not None:
            raw.setdefault("comments", []).append({"body": comment})
        if raw is not None:
            raw["state"] = "closed"
            if reason not in raw.setdefault("labels", []):
                raw["labels"].append(reason)
        self._record("close", number, comment or "")

    def reclose(self, number, comment=None, was=None, now=inbox.CLOSED_DONE):
        raw = self._item(number)
        if comment and raw is not None:
            raw.setdefault("comments", []).append({"body": comment})
        if raw is not None:
            raw["state"] = "closed"
            if now not in raw.setdefault("labels", []):
                raw["labels"].append(now)
            if was and was != now and was in raw["labels"]:
                raw["labels"].remove(was)
        self._record("reclose", number, comment or "")

    def create_milestone(self, title):
        self.raw.setdefault("milestones", [])
        if title not in self.raw["milestones"]:
            self.raw["milestones"].append(title)
        self._record("create_milestone", 0, title)
        return 1

    def attach_sub_issue(self, parent, child):
        raw = self._item(parent)
        if raw is not None:
            subs = raw.setdefault("sub_issues", [])
            if child not in subs:
                subs.append(child)
        child_raw = self._item(child)
        if child_raw is not None:
            child_raw["parent_batch"] = parent
        self._record("attach_sub_issue", parent, str(child))

    def clear_board_status(self, number):
        raw = self._item(number)
        if raw is not None:
            raw["status"] = None
        self._record("clear_board_status", number, "")

    def create_item(self, title, body, labels=(), milestone=None):
        number = max([i["number"] for i in self.raw.get("items", ())] or [100]) + 1
        self.raw.setdefault("items", []).append({
            "number": number, "title": title, "body": body,
            "labels": list(labels), "blocked_by": [], "parent_batch": None,
            "milestone": milestone,
        })
        self._record("create_item", number, title)
        return number


# ---------------------------------------------------------------------------
# Batching — computed from the fields, not reasoned
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class WorkBatch:
    """The items one session takes, and the branch it takes them on."""

    slug: str
    items: tuple

    @property
    def numbers(self):
        return tuple(i.number for i in self.items)

    @property
    def change(self):
        """The one spec-driven change this batch's items name, if they agree."""
        changes = {i.change for i in self.items if i.change}
        return changes.pop() if len(changes) == 1 else None


def parented(snapshot):
    """Every item number some batch in the snapshot claims as a sub-issue.

    `Item.parent_batch` is the field the fixtures carry, and the live
    `Tracker.snapshot` never fills it (GitHub's issue payload has no such
    key), so parentage is taken from the batches' own `sub_issues` as well.
    Reading only the field would make every live item look like an orphan,
    and guard 2 would route the whole bolt.
    """
    return {n for b in snapshot.batches for n in b.sub_issues}


def analyse(items, snapshot=None, slug=""):
    """Group ready items into the batches one session could take.

    Type is the hard boundary and relatedness decides within a type
    (tracker.md invariant 3); on a bolt every work item is `type:assertion`,
    so what remains is relatedness, and the tracker already carries it as
    the unit an item was released in. Items sharing a parent ride together —
    unless they name distinct changes: an expanded plan task IS its own
    spec-driven change, and each change gets its own batch, its own
    session, and its own `build/<change>` branch (construction-loop.md:
    one writer per branch). An unparented item rides alone. Computed from
    the fields — this step reads and writes nothing, and reasons about
    nothing.
    """
    claimed = parented(snapshot) if snapshot is not None else set()
    groups, order = {}, []
    for item in items:
        key = item.parent_batch
        if key is None and item.number in claimed and snapshot is not None:
            for batch in snapshot.batches:
                if item.number in batch.sub_issues:
                    key = batch.number
                    break
        key = key if key is not None else f"solo:{item.number}"
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(item)
    batches = []
    for key in order:
        members = sorted(groups[key], key=lambda i: i.number)
        named, rest = {}, []
        for item in members:
            if item.change:
                named.setdefault(item.change, []).append(item)
            else:
                rest.append(item)
        for change_name, group in named.items():
            batches.append(WorkBatch(slug=change_name, items=tuple(group)))
        if rest:
            name = (f"{slug}-{rest[0].number}" if slug
                    else f"item-{rest[0].number}")
            batches.append(WorkBatch(slug=name, items=tuple(rest)))
    return batches


def after_split(snapshot, items):
    """Honor the plan's task-level chain: an item whose `After:` names a
    task not yet merged waits — "a task that builds on an earlier one waits
    for that item's merge" (construction-loop.md), the defer predicate one
    level below the unit cards' blocked-by. A token is a task ordinal — the
    Nth sub-issue of the item's own unit, by ascending number — or a `#123`
    issue number. An unresolvable token never holds the item: the plan's
    failure modes are asymmetric, and the loud one — a spec session that
    cannot derive, a red gate — is chosen over a silent deadlock.
    """
    runnable, held = [], []
    by_number = {i.number: i for i in snapshot.items}
    for item in items:
        siblings = ()
        for batch in snapshot.batches:
            if item.number in batch.sub_issues:
                siblings = tuple(sorted(batch.sub_issues))
                break
        blocker = None
        for token in item.after:
            token = str(token).lstrip("#")
            if token.isdigit():
                n = int(token)
                target_num = siblings[n - 1] if 1 <= n <= len(siblings) else n
                target = by_number.get(target_num)
            else:
                # A change name — the plan's own vocabulary for its tasks.
                target = next(
                    (by_number[n] for n in siblings if n in by_number
                     and token in (by_number[n].change, by_number[n].title)),
                    None)
            if target is None or target.number == item.number:
                continue
            # Merged is merged whichever closure model wrote it: an item
            # closed `closed:merged`/`closed:done`, or one the merge step
            # left open at `stage:merged` awaiting the landing.
            merged = inbox.STAGE_MERGED in target.labels or (
                (not target.is_open) and bool(
                    {inbox.CLOSED_MERGED, inbox.CLOSED_DONE} & target.labels))
            if not merged:
                blocker = target.number
                break
        if blocker is None:
            runnable.append(item)
        else:
            held.append((item, f"waits for #{blocker} to merge"))
    return tuple(runnable), tuple(held)


def session_name(prefix, slug):
    """`<type>-<topic>`, capped where herdr caps it. The name IS the
    classification, so the type prefix is never the part that gets cut."""
    return f"{prefix}-{slug}"[:sessions.MAX_NAME]


# ---------------------------------------------------------------------------
# Stage outcomes
# ---------------------------------------------------------------------------

@dataclass
class StageOutcome:
    stage: str
    status: str            # done | blocked | stalled | failed | paused | skipped
    detail: str = ""
    handle: object = None
    report: str = ""

    @property
    def ok(self):
        """May the cycle carry on past this stage?

        `skipped` is ok because a stage that does not apply must not stop
        the ones after it — the plan-mode path skips spec and verify, and
        still builds and merges.
        """
        return self.status in ("done", "skipped")

    @property
    def ran(self):
        """Did this boundary actually occur?

        The stage labels are written off THIS, never off `ok`. The two
        differ on exactly one status — `skipped` — and that difference is
        the whole point: a skipped stage is one that did not happen, and
        "a stage that did not happen writes no label" is the property the
        audit query depends on. Reading `ok` here would have the plan-mode
        path label items `stage:verified` with no verify session ever
        launched, which is the same wrong answer the spec forbids on
        `bolt-direct`, reached by a different route.
        """
        return self.status == "done"


@dataclass
class CycleResult:
    number: int
    actions: tuple = ()
    ready: tuple = ()
    outcomes: tuple = ()
    stopped: str = ""
    halted: str = ""


@dataclass
class RunReport:
    milestone: str
    cycles: list = field(default_factory=list)
    landing: str = "not attempted"
    queue: list = field(default_factory=list)
    halted: str = ""

    @property
    def ok(self):
        return not self.halted


def _run_subprocess(argv, cwd=None, env=None, timeout=None):
    return subprocess.run(argv, cwd=cwd, env=env, timeout=timeout,
                          capture_output=True, text=True)


# ---------------------------------------------------------------------------
# The loop
# ---------------------------------------------------------------------------

@dataclass
class BoltParams:
    slug: str
    org: str = "agentplot"
    repo: str = "flywheel"
    repo_dir: str = "."
    bolt_worktree: str = None
    bolt_branch: str = None
    main_branch: str = "main"
    type_name: str = "bolt-quick"
    plan_mode: bool = False
    config: LoopConfig = None
    runner_config: dict = None
    #: The bolt milestone's description — the planner's summary, which the
    #: book names as the charter's source. Read once by
    #: `bin/flywheel-bolt-loop` for the plan-mode flag and carried here so
    #: `guard_scaffold` can put it in the order that writes `bolt.md`,
    #: rather than costing a tracker round trip on every pass. Empty under
    #: `--fixture`, whose `milestone()` returns a stub with no description
    #: — the "milestone carries no description" path the spec covers.
    description: str = ""
    #: The design book's checkout, from the fleet binding — where the
    #: items' chapter citations resolve. Sessions cannot read a chapter
    #: they cannot find.
    book_dir: str = None

    def __post_init__(self):
        if not self.slug:
            raise LoopError("a bolt loop needs its slug — the milestone is bolt/<slug>")
        self.bolt_branch = self.bolt_branch or f"{inbox.BOLT_PREFIX}{self.slug}"
        self.bolt_worktree = self.bolt_worktree or self.repo_dir
        self.config = self.config or LoopConfig(name=self.type_name)

    @property
    def milestone(self):
        return f"{inbox.BOLT_PREFIX}{self.slug}"

    @property
    def change_dir(self):
        return Path(self.bolt_worktree) / "openspec" / "changes" / self.slug


class BoltLoop:
    """One bolt's construction, one process.

    Every seam the tests need is injected: the tracker, a runner factory,
    the subprocess used for git/openspec/`bin/flywheel-batch`, the clock and
    the log. Nothing here reaches the network or a pane on its own.
    """

    def __init__(self, params, tracker, runner_factory=None, run=_run_subprocess,
                 clock=time.time, log=None, dry_run=False, ledger=None):
        self.params = params
        self.tracker = tracker
        self.dry_run = dry_run
        self.ledger = ledger or obs.NullLedger()
        self._run = run
        self._clock = clock
        self._log = log or (lambda message: None)
        self._runner_factory = runner_factory or self._default_runner
        self._runners = {}
        self._plan_returns = {}
        self._fix_rounds = {}
        self._landing_attempts = 0
        self._merged = 0
        self._resume_landing = False

    # -- plumbing ----------------------------------------------------------

    def _default_runner(self, stage):
        return sessions.runner_for(
            sessions.choose_runner(stage, self.params.runner_config))

    def runner(self, stage):
        name = sessions.choose_runner(stage, self.params.runner_config)
        if name not in self._runners:
            self._runners[name] = self._runner_factory(stage)
        return self._runners[name]

    def shell(self, argv, cwd=None):
        return self._run(argv, cwd=str(cwd) if cwd else None)

    def git(self, *args, cwd=None):
        return self.shell(["git", *args], cwd=cwd or self.params.bolt_worktree)

    def _wt_rows(self):
        out = self.shell(["wt", "list", "--format", "json"],
                         cwd=self.params.repo_dir)
        if out.returncode != 0:
            return None
        try:
            rows = json.loads(out.stdout or "[]")
        except ValueError:
            return None
        return rows if isinstance(rows, list) else None

    def worktree_for(self, branch, base):
        """The loop is the worktree orchestrator — worktrunk's agent-handoff
        pattern: the orchestrator creates the worktree and the session is
        born inside it. No order ever tells a session to run `wt switch`.

        Idempotent: an existing worktree for the branch is adopted by path.
        Returns (path, created); (None, False) when wt cannot provide one.
        """
        rows = self._wt_rows()
        for row in rows or ():
            if row.get("branch") == branch and row.get("path"):
                return row["path"], False
        # A branch may exist with no worktree — a restart, a landing that
        # pruned, a session that got there first. Plain `wt switch` attaches
        # a worktree to an existing branch; `--create` is only for a branch
        # not born yet, and errors on one that is.
        exists = self.git("rev-parse", "--verify", "--quiet", branch,
                          cwd=self.params.repo_dir).returncode == 0
        argv = (["wt", "switch", branch, "--no-cd"] if exists else
                ["wt", "switch", "--create", branch, "--base", base, "--no-cd"])
        made = self.shell(argv, cwd=self.params.repo_dir)
        if made.returncode != 0:
            return None, False
        if not exists:
            self.record_base(branch, base)
        rows = self._wt_rows()
        for row in rows or ():
            if row.get("branch") == branch and row.get("path"):
                return row["path"], True
        return None, False

    def record_base(self, branch, base):
        """The cut point, recorded where git keeps durable facts — a ref,
        written once at creation. `branch_advanced` reads it to tell an
        empty branch from a merged one, which bare ancestry cannot."""
        sha = (self.git("rev-parse", base,
                        cwd=self.params.repo_dir).stdout or "").strip()
        if sha:
            self.git("update-ref", f"refs/flywheel/base/{branch}", sha,
                     cwd=self.params.repo_dir)

    def branch_base(self, branch):
        """The recorded cut point; merge-base with main when the branch
        predates the refs. The fallback reads a merged-but-unrecorded
        branch as empty — the safe direction, since re-driving green work
        costs a no-op session and a false "merged" costs a false landing."""
        ref = self.git("rev-parse", "--verify", "--quiet",
                       f"refs/flywheel/base/{branch}", cwd=self.params.repo_dir)
        sha = (ref.stdout or "").strip()
        if ref.returncode == 0 and sha:
            return sha
        fallback = self.git("merge-base", branch, self.params.main_branch,
                            cwd=self.params.repo_dir)
        return (fallback.stdout or "").strip() or None

    def _any_commits(self, spec, cwd=None):
        """`git rev-list --count <spec>` read as "is there anything there"."""
        proc = self.git("rev-list", "--count", spec, cwd=cwd)
        out = (proc.stdout or "").strip()
        return out.isdigit() and int(out) > 0

    def branch_advanced(self, branch):
        """Commits beyond the cut point — the fact that makes ancestry mean
        something. An empty branch's tip is an ancestor of everything it
        was cut from, so bare ancestry reads it as merged, landed and done
        (#164, observed live); an empty branch is "nothing to merge",
        never "merged"."""
        base = self.branch_base(branch)
        if not base:
            return False
        return self._any_commits(f"{base}..{branch}", cwd=self.params.repo_dir)

    def batch_merged(self, batch):
        """Git's answer to "does this batch still need driving": a build
        branch that advanced past its cut point and is fully an ancestor
        of the bolt branch awaits only the landing. A branch that does not
        exist is work not yet started; one that never advanced is work
        never done."""
        branch = f"build/{batch.slug}"
        if self.git("rev-parse", "--verify", "--quiet", branch).returncode != 0:
            return False
        if not self.branch_advanced(branch):
            return False
        return self.git("merge-base", "--is-ancestor", branch,
                        self.params.bolt_branch).returncode == 0

    def batch_worktree(self, batch):
        path, _created = self.worktree_for(f"build/{batch.slug}",
                                           self.params.bolt_branch)
        return path

    # -- objective checks: the world, not a report -------------------------

    def change_validates(self, change, cwd=None):
        """`openspec validate --strict` — green before a spec counts.

        Run in the tree that HOLDS the change: a spec committed on a build
        worktree does not exist in the main checkout, and validating there
        fails a change that is green where it lives.
        """
        proc = self.shell(["openspec", "validate", change, "--strict"],
                          cwd=cwd or self.params.repo_dir)
        return proc.returncode == 0

    def branch_has_commits(self, branch):
        return self._any_commits(f"{self.params.bolt_branch}..{branch}")

    def branch_merged(self, branch, target=None):
        target = target or self.params.bolt_branch
        return self.git("merge-base", "--is-ancestor", branch, target).returncode == 0

    def head_sha(self, ref):
        return (self.git("rev-parse", ref).stdout or "").strip()

    def clear_channel(self, cwd, rel):
        """Delete a file channel before the session that writes it runs."""
        try:
            (Path(cwd) / rel).unlink()
        except OSError:
            pass

    def read_channel(self, cwd, rel):
        """The channel's content, stripped — or None where nothing was written."""
        try:
            return (Path(cwd) / rel).read_text().strip()
        except OSError:
            return None

    def deliverables(self, batch, change=None):
        """What "done" means for a construction session, checked on disk.

        Completion is objective — settle plus the deliverable contract:
        change validates, commit on branch. Both are git's and openspec's
        answers, never the session's word. The tracker comment that used to
        be the third leg is the LOOP's to write now, at the built boundary
        — bookkeeping was never the builder's job, and a work order that
        points a session at the tracker is what primes the roaming.
        """
        missing = []
        if change and not self.change_validates(
                change, cwd=self.batch_worktree(batch)):
            missing.append(f"`openspec validate {change} --strict` is not green")
        if not self.branch_has_commits(f"build/{batch.slug}"):
            missing.append(f"no commit on build/{batch.slug} beyond {self.params.bolt_branch}")
        return missing

    # -- the tracker side of a session ------------------------------------

    def mark_verified(self, batch):
        """Record the clean verdict on the items, bound to the branch head.

        Same shape as the launch marker: a machine-readable comment, read
        back as code. A restarted loop trusts it exactly while the branch
        sha still matches — one commit later and the verdict is spent."""
        sha = self.head_sha(f"build/{batch.slug}")
        if not sha:
            return
        for number in batch.numbers:
            self.tracker.comment(
                number,
                f"Verify is clean at `{sha}`.\n\n"
                f'<!-- flywheel:verified sha="{sha}" -->')

    def verified_at(self, numbers):
        """The recorded clean-verify sha these items agree on, or None."""
        shas = []
        for number in numbers:
            found = None
            for comment in self.tracker.comments(number) or ():
                match = _VERIFIED.search(comment.get("body", ""))
                if match:
                    found = match.group("sha")
            shas.append(found)
        return (shas[0] if shas and shas[0]
                and all(sha == shas[0] for sha in shas) else None)


    def mark_launch(self, numbers, name, started):
        """Record the launch on the items — the stall clock's only carrier.

        A loop process is stateless and may be restarted at any moment; the
        4-hour budget has to be measured from when the session started, not
        from when this process did. herdr publishes no timestamp (measured:
        `herdr agent list` carries only monotonic counters), so the launch
        time goes where everything else goes, on the item.
        """
        marker = f'{SESSION_OPEN} name="{name}" started="{int(started)}" -->'
        for number in numbers:
            self.tracker.comment(number, f"Session `{name}` started.\n\n{marker}")

    def launch_origin(self, numbers, name):
        """The LATEST launch this loop (or an earlier one) recorded for the
        name. A name accumulates one marker per (re)launch; the live pane
        is the most recent one, so the newest marker is its clock — the
        oldest would measure the first corpse (#168)."""
        best = None
        for number in numbers:
            for comment in self.tracker.comments(number) or ():
                body = comment.get("body", "") if isinstance(comment, dict) else str(comment)
                for match in _SESSION.finditer(body):
                    if match.group("name") != name:
                        continue
                    started = int(match.group("started"))
                    best = started if best is None else max(best, started)
        return best

    def flip_in_progress(self, numbers):
        for number in numbers:
            if not self.tracker.has_label(number, inbox.IN_PROGRESS):
                self.tracker.add_label(number, inbox.IN_PROGRESS)
            if self.tracker.has_label(number, inbox.READY):
                self.tracker.remove_label(number, inbox.READY)

    def set_stage(self, numbers, stage):
        """`inbox.set_stage` over a batch. Returns the numbers it wrote.

        The rule — one stage label, naming the leading edge, written by
        removing the previous one — lives in `_flywheel_inbox` beside the
        vocabulary itself, because the intent loop writes stages too and a
        rule only this loop obeyed would not be a rule about the set.
        """
        return [n for n in numbers if inbox.set_stage(self.tracker, n, stage)]

    def pause(self, numbers, reason):
        """Invariant 7: the label marks a live wait, applied at the moment
        of blocking, with the reason on the item."""
        for number in numbers:
            inbox.set_needs_operator(self.tracker, number, reason)

    def andon(self, numbers):
        """The stop a session raised, read as code rather than judgment."""
        for number in numbers:
            found = inbox.find_andon(self.tracker.comments(number) or ())
            if found:
                return number, found
        return None, None

    # -- driving a session -------------------------------------------------

    def drive(self, stage, spec, numbers=(), close=True, expect_prompted=False):
        """Launch (idempotently), supervise on a real clock, collect.

        `supervise` is called once per PROMPT, which is what makes "the
        clock restarts after a plan approval" true without a counter to
        reset by hand.
        """
        runner = self.runner(stage)
        try:
            handle = runner.launch(spec)
        except sessions.SessionError as error:
            return StageOutcome(stage, "failed", f"launch: {error}")
        # Markers measure the session that is actually in the pane. Only a
        # REUSED pane may inherit one; a fresh launch after the old session
        # died starts its own clock — inheriting the corpse's marker judged
        # a new-born session stalled at 1276 minutes (#168, observed live).
        reused = bool(getattr(handle, "reused", False))
        origin = (self.launch_origin(numbers, spec.name)
                  if numbers and reused else None)
        if origin is None:
            origin = self._clock()
            if numbers and not expect_prompted:
                self.mark_launch(numbers, spec.name, origin)
        return self.settle(stage, runner, handle, numbers, origin, close=close)

    def settle(self, stage, runner, handle, numbers, origin, close=True):
        notified = {"fired": False}

        def on_notify(_handle, elapsed):
            notified["fired"] = True
            self.pause(numbers, (
                f"Session `{handle.name}` has been working ~{int(elapsed // 60)} "
                f"minutes without settling. This is a live wait — dispatch relays it."))

        watch = sessions.supervise(
            runner, handle, on_notify=on_notify, clock=self._clock, origin=origin,
            notified=self._already_notified(numbers))
        # Clear only the notice THIS watch raised. `watch.notified` is also
        # true when the label pre-existed — an andon escalation or an earlier
        # run's notice — and clearing on that read ate a live andon four
        # times (#165). A label this watch did not set outlives its settle.
        if notified["fired"] and watch.state != sessions.WaitState.STALLED:
            for number in numbers:
                inbox.clear_needs_operator(self.tracker, number)
        if watch.state == sessions.WaitState.STALLED:
            return StageOutcome(stage, "stalled",
                                f"{int(watch.elapsed // 60)} min without settling; "
                                f"pane left open", handle)
        if watch.state == sessions.WaitState.GONE:
            return StageOutcome(stage, "failed", "the session is gone", handle)
        collected = runner.collect(handle)
        if watch.state == sessions.WaitState.SETTLED_BLOCKED:
            return StageOutcome(stage, "blocked", "settled blocked — a question or a "
                                "permission ask the operator answers in the pane",
                                handle, collected.report)
        if close:
            runner.close(handle)
        return StageOutcome(stage, "done", "settled", handle, collected.report)

    def _already_notified(self, numbers):
        return any(self.tracker.has_label(n, inbox.NEEDS_OPERATOR) for n in numbers)

    def spec_for(self, stage, name, cwd, order, plan_mode=False):
        # The session id derives from the name and cwd, so ANY loop process
        # can reconstruct it with zero stored state: the pane is disposable,
        # the session is durable, and a relaunch resumes the warm
        # conversation instead of starting cold (#178).
        session_id = str(uuid.uuid5(uuid.NAMESPACE_URL,
                                    f"flywheel://{cwd}/{name}"))
        return sessions.SessionSpec(
            name=name, cwd=str(cwd), order=order, profile=PROFILE,
            model=STAGE_MODELS.get(stage), plan_mode=plan_mode,
            session_id=session_id,
            runner=sessions.choose_runner(stage, self.params.runner_config))

    # -- guards ------------------------------------------------------------

    def guards(self, snapshot):
        """Every cycle, in the record's order, each idempotent.

        `actions` records ONLY the writes made. A check that changed
        nothing records nothing — an empty list is the normal, correct
        result, and the STOP condition is built on exactly that.
        """
        actions = []
        # -1 expand, 0 scaffold, 0.5 topology, 0.6 charter, 1 flip-consume,
        # 2 route, 3 stages.
        expanded = self.guard_expand(snapshot, actions)
        if expanded is not None:
            return actions, expanded
        scaffolded = self.guard_scaffold(actions)
        if scaffolded is not None:
            return actions, scaffolded
        topology = self.guard_topology(actions)
        if topology is not None:
            return actions, topology
        charter = self.guard_charter(snapshot, actions)
        if charter is not None:
            return actions, charter
        self.guard_flip_consume(snapshot, actions)
        # A queued item on the milestone is inert to machinery: it waits
        # until an author — the planner, dispatch, or the operator — folds
        # it into a plan card. Expansion of an approved card is the only
        # birth of work items.
        self.guard_stages(snapshot, actions)
        return actions, None

    def guard_stages(self, snapshot, actions):
        """3 — re-derive `stage:built` and `stage:merged` from the tree.

        The loop is stateless by construction, so a process killed between
        an apply and its label write leaves an item whose git state is
        built and whose label is not. This repairs that without knowing
        anything about the process that died: an item whose branch advanced
        past its cut point AND is fully an ancestor of the bolt branch is
        merged — `batch_merged`, the same predicate the landing trusts —
        and otherwise an item whose branch holds a commit beyond the bolt
        branch is built, per `branch_has_commits`. Bare ancestry is not
        the merged test: an untouched branch's tip is an ancestor of
        everything it was cut from, so ancestry alone reads a never-worked
        branch as merged and closes its items (#164, re-entered here as
        #173).

        **`stage:planned` and `stage:verified` are deliberately left
        out.** Neither has a witness the tree can answer. A validated spec
        survives on disk, but the plan-mode path's `planned` is an approval
        that happened in a pane and left no artifact, so `planned` has no
        uniform witness; and `verified` has none at any time — verify being
        clean is a session's finding, and the only way a later cycle could
        re-derive it is to re-run verify, which is running a stage rather
        than reconciling a label. So a `verified` item is never walked back
        to `built` here, and no `verified` is ever invented.

        The branch names come from `analyse` — the same grouping that named
        the branch at spec time — rather than from a stored string, so an
        item whose branch genuinely does not exist is correctly read as not
        built rather than as a name this guard got wrong.

        Scoped to the milestone's open `state:in-progress` items — exactly
        the set a bolt-loop stage label may sit on, since `stage:*` refines
        `state:in-progress` and never replaces a `state:*` label, so an item
        still queued or merely released has no stage to reconcile and must
        not acquire one here — **and** its `closed:merged` items. The two
        scopes answer the two halves of the merged edge: the item whose
        close did not happen is in the first, and the item whose label did
        not is in the second. An item at `closed:done` is in neither: the
        landing is downstream of the merge, and re-derivation never
        reverses it.
        """
        items = [i for i in snapshot.on(self.params.milestone)
                 if ((i.is_open and i.in_progress) or i.merge_closed)
                 and not i.is_container]
        if not items:
            return
        for batch in analyse(items, snapshot, self.params.slug):
            branch = f"build/{batch.slug}"
            if self.batch_merged(batch):
                target = inbox.STAGE_MERGED
            elif self.branch_has_commits(branch):
                target = inbox.STAGE_BUILT
            else:
                continue                # the tree witnesses nothing; write nothing
            for item in batch.items:
                current = inbox.stage_of(item.labels, inbox.CONSTRUCTION_STAGES)
                # verified is never walked back to built: it has no witness
                # the tree can answer, so its absence proves nothing.
                witnessed = (current != target
                             and not (target == inbox.STAGE_BUILT
                                      and current == inbox.STAGE_VERIFIED))
                if witnessed and self.dry_run:
                    actions.append(f"would reconcile #{item.number} "
                                   f"{current or 'no stage'} -> {target}")
                elif witnessed and self.set_stage([item.number], target):
                    actions.append(f"#{item.number} {current or 'no stage'} "
                                   f"-> {target} (re-derived from {branch})")
                if target != inbox.STAGE_MERGED:
                    continue
                # The merged edge is ONE fact with TWO writes, so a process
                # killed between them leaves an item half-merged in the
                # tracker's eyes. Repair the close as well as the label.
                if item.is_container:
                    continue
                if item.merge_closed:
                    continue            # closed WITH the reason; nothing torn
                if not item.is_open:
                    continue            # closed some other way; `closed:done` never walked back
                # What reaches here is open — either never closed, or a
                # close torn between its label and its state.
                if self.dry_run:
                    actions.append(f"would close #{item.number} {inbox.CLOSED_MERGED}")
                    continue
                # Only what was actually written. `close_merged` returns the
                # numbers it closed and skips an item already closed with the
                # reason, so an unconditional append here would record a write
                # on every cycle for an item nothing had touched.
                if self.close_merged([item]):
                    actions.append(f"#{item.number} closed {inbox.CLOSED_MERGED} "
                                   f"(re-derived from {branch})")

    def guard_expand(self, snapshot, actions):
        """-1 — expansion: an approved plan card becomes a unit on this bolt.

        The card is `plan`-labeled, open, at board Status Ready, and
        **already on this bolt's milestone** — the planner creates
        `bolt/<slug>` and files the card onto it, so expansion reads the
        card's own home and writes no milestone at all. The test is
        `c.milestone`, not `PlanCard.bolt`: that property falls back to the
        title slug for a card filed before milestones were the planner's,
        and a card carrying another bolt's milestone, or none, is not this
        bolt's to expand.

        Board approval reaches construction here and nowhere else, and it
        reaches it once per APPROVAL rather than once per bolt. A bolt
        carries as many units as the operator approves over its life; each
        expansion adds one beside the units already there and touches
        neither them nor their items. Idempotent by construction: expansion
        swaps `plan` for `unit`, so an expanded card is no longer a plan
        card and a later pass finds nothing.

        A card with no Team refuses (an unroutable unit is a defect at
        approval time); a card whose blocking predecessor's work is not all
        in defers — the pass records the wait and stops, and the server's
        interval retries.
        """
        cards = [c for c in getattr(snapshot, "plan_cards", ())
                 if c.at_ready and c.milestone == self.params.milestone]
        if not cards:
            return None
        if self.dry_run:
            actions.append("would expand plan card(s) "
                           + ", ".join(f"#{c.number}" for c in cards))
            return None
        for card in cards:
            failure = self._expand_card(card, snapshot, actions)
            if failure:
                return failure
        return None

    def _predecessor_in(self, number, snapshot):
        """Is this blocker's work all in — the MERGE, not the close?

        Closure of the blocker itself is the wrong predicate under
        bolt-of-units, and provably deadlocking. A blocking card is now a
        sibling unit on the same milestone; the loop closes a unit card
        `closed:done` only AFTER the bolt lands, and the landing waits on
        the milestone's open unit cards. So a card blocked by a sibling
        could never expand before the landing, and the landing could never
        run.

        What "all in" means instead: the blocker is closed (however it was
        closed), or it is an expanded `unit` every one of whose work items
        is closed. An UNEXPANDED blocker is never satisfied — it has no
        work items yet, so there is nothing that could be in, and its
        dependent waits for the operator's approval. That is the book's
        deferral, never a refusal.

        Read from the snapshot the guard already holds. It is scoped to
        this milestone and carries the open items PLUS the `closed:merged`
        ones — exactly the two states a sibling unit's items can be in
        while the unit is still open, since the landing that would close
        them `closed:done` is the same act that closes the unit. So a
        sibling's verdict costs no network call. The tracker read is the
        fallback for the one case the snapshot cannot answer: a blocker
        that is not on this milestone at all.
        """
        blocker = snapshot.item(number)
        if blocker is None:
            return self.tracker.closed(number)
        if not blocker.is_open:
            return True
        if inbox.UNIT not in blocker.labels:
            return False
        # Its work items, by the parentage `backfill_parentage` derives from
        # the batches' sub-issues — the field the API does not carry and the
        # guards key on.
        work = [i for i in snapshot.items if i.parent_batch == number]
        return bool(work) and all(not i.is_open for i in work)

    def _expand_card(self, card, snapshot, actions):
        if not card.team:
            # The unroutable thing is the UNIT, not the bolt: the bolt's
            # other units and their items are untouched by this refusal.
            self.tracker.add_label(card.number, inbox.NEEDS_OPERATOR)
            self.tracker.comment(card.number, (
                "Expansion refused: the card carries no Team, so the unit "
                "is unroutable. Set Team on the board and the next pass "
                "expands it."))
            actions.append(f"card #{card.number}: no Team — needs-operator")
            return f"expansion: card #{card.number} carries no Team"
        for blocker in card.blocked_by:
            if not self._predecessor_in(blocker, snapshot):
                self.ledger.note(
                    f"expansion deferred — card #{card.number} blocked by "
                    f"#{blocker}, whose work is not all in")
                self._log(f"expansion deferred: #{card.number} waits on "
                          f"#{blocker}")
                return None
        tasks = inbox.plan_tasks(card.body)
        if not tasks:
            return (f"expansion: no task table parses from plan card "
                    f"#{card.number}")
        milestone = self.params.milestone
        self.ledger.expect(
            f"expand:{card.number}",
            f"plan card #{card.number} at Ready",
            f"{milestone}: unit + {len(tasks)} item(s), status consumed")
        # No milestone write of any kind. The milestone and the card's home
        # are the PLANNER's writes; the guard's selection already proved the
        # card is on this one, so creating it or setting it again would be a
        # write on every pass for a fact nothing had changed.
        self.tracker.swap_label(card.number, inbox.UNIT, inbox.PLAN)
        if card.stale:
            self.tracker.remove_label(card.number, inbox.STALE)
        made = []
        for task in tasks:
            # `Change:` is the item's contract line — the batcher reads it
            # to give each change its own session and branch; the title is
            # display and may drift.
            body_lines = [f"Change: {task['change']}", task.get("delivers", "")]
            if task.get("chapters"):
                body_lines.append(f"Chapters: {task['chapters']}")
            if task.get("after"):
                body_lines.append(f"After: {task['after']}")
            number = self.tracker.create_item(
                task["change"], "\n\n".join(l for l in body_lines if l),
                labels=(inbox.READY,), milestone=milestone)
            if number:
                self.tracker.attach_sub_issue(card.number, number)
                made.append(number)
        self.tracker.clear_board_status(card.number)
        self.ledger.actual(
            f"expand:{card.number}",
            f"unit #{card.number}, items {', '.join(f'#{n}' for n in made)}")
        actions.append(f"expanded plan card #{card.number} into a unit on "
                       f"{milestone} with {len(made)} item(s)")
        return None

    #: The bolt-level headings a charter opens with, in the bound schema's
    #: `bolt.md` template order. Named in the order so the session knows
    #: what a charter IS; their CONTENT stays the template's, which the
    #: order points at rather than inlines — a second copy here would drift
    #: the first time a schema version moved.
    CHARTER_SECTIONS = ("## Scope", "## Sources", "## Repos",
                        "## Merge criteria")

    def guard_scaffold(self, actions):
        """0 — charter-if-missing.

        There is no non-interactive `openspec change new`, so the scaffold
        is a session like every other act of judgment-free work the loop
        cannot do with a subprocess.

        **The test is the CHARTER, not the directory that holds it.** It
        used to be the directory — "the directory existing is the whole
        test" — and that reads a directory as a charter. They are not the
        same thing, and the post-settle check below is the proof: a settle
        is not a charter. `openspec new change` returns the moment the
        directory is there, so a scaffold session that created it and
        settled without writing `bolt.md` failed the check on the pass that
        drove it and then passed every pass after it — `change_dir.exists()`
        was true and the guard returned above the check. The record walked
        charterless through expansion, the stages and every merge, and the
        first reader to say so was `land_stage`'s refusal, after the
        operator's milestone close had already released the landing. So
        `bolt.md` is the whole test now: a change directory carrying none is
        this guard's case on every pass, and is driven to a charter on the
        pass that finds it.

        **A change that already exists is CONTINUED, not created.** The
        creating path's `/opsx:new <slug>` cannot be obeyed on a directory
        that is already there — that command's own guardrail is to suggest
        `/opsx:continue` instead — and a session that cannot obey its order
        writes nothing while reading as settled. `/opsx:continue` creates
        the first `ready` artifact, and on a bolt-bound change missing
        `bolt.md` that is `bolt`: in every `bolt-*` schema `bolt` is the
        first declared artifact with `requires: []`. `/opsx:ff` would drive
        every artifact including the `units/<slug>.md` files the loop writes
        itself. What the two orders ASK FOR is one text built once below, so
        the charter a record gets does not depend on which path wrote it;
        only the framing and the invocation differ. The session name is
        `scaffold-<slug>` on both paths, so the charterless record found on
        a later pass resumes the warm scaffold conversation — usually the
        very session that settled without writing the charter — rather than
        opening a cold second one.

        **What it asks for is a CHARTER.** `bolt.md` is the bolt's charter
        — the delivery statement, the sources, the repos, and the merge
        criteria the landing verifies — and a planner-born bolt used to get
        none of it: the order named one thing to write, the lowest-numbered
        unit's plan document, and the session obeyed. Two readers then read
        nothing: `merge_criteria()` returned `""`, and `landing_mode()`
        fell through to its `merge` default on a charter that had said
        nothing, so a bolt meaning to land by pull request landed straight
        onto main. So the order names the four bolt-level sections and asks
        for the `Landing:` line stated, and points the session at
        `openspec instructions bolt --change <slug>` for what belongs under
        each — the template stays the authority for their content.

        The `Landing:` line is the ORDER'S requirement, not a line every
        rendered template shows: only `bolt-default`'s carries one. A
        charter that leaves it out leaves the landing mode to a default
        that is indistinguishable from a declaration, which is the failure
        this closes — so it is asked for under every schema.

        **The milestone's description is the charter's stated source**, and
        it rides in the order. A milestone with none still gets its
        sections, written from what the milestone and its items say: an
        absent description is a thinner charter, never a missing one.

        **No unit's plan document is asked for, ever.** The order used to
        end by telling the session to copy the lowest-numbered unit's body
        into `bolt.md` under a `# Unit: <slug>` heading, with the rest
        appended there later. The record splits now: `bolt.md` is the
        bolt's statement and each approved unit's document is its own
        artifact at `units/<slug>.md`, which `guard_charter` writes at
        expansion. So the four sections are the whole charter whether or
        not the milestone carries unit cards, and the order says so —
        a milestone carrying cards is not a reason to write a unit and
        skip the bolt.

        **The charter is then checked, not assumed.** A settle used to be
        the whole post-condition. It is now the settle plus the reader:
        `merge_criteria()`, the SAME function the landing reads through, so
        "the guard passed" and "the landing can read it" cannot disagree.
        The check runs on BOTH driving paths and gives one reason string, so
        a charter written into an existing change is held to exactly what a
        charter written with its directory is held to.

        **A `bolt.md` that is present is never this guard's business.** It
        returns above everything, whether or not that charter reads back
        criteria: a charter that has lost its sections is the landing's
        refusal to make, and a guard that repaired it would be a second
        writer over committed prose, which outranks the state it came from.
        That return is also the dry-cycle property — a pass over a
        chartered record drives nothing, writes nothing and records nothing.
        """
        if (self.params.change_dir / "bolt.md").exists():
            return None
        # The directory without the charter: the change is there and the
        # artifact is owed. Read once, above the dry-run branch, because it
        # picks the invocation AND what a dry run says it would do.
        continuing = self.params.change_dir.exists()
        if self.dry_run:
            actions.append(
                (f"would write the charter into openspec/changes/"
                 f"{self.params.slug}, which exists carrying no bolt.md"
                 if continuing else
                 f"would scaffold openspec/changes/{self.params.slug}")
                + f" ({self.params.type_name})")
            return None
        name = session_name("scaffold", self.params.slug)
        described = (self.params.description or "").strip()
        sections = ", ".join(f"`{s}`" for s in self.CHARTER_SECTIONS)
        # ONE statement of what a charter is, used by both invocations.
        # Two copies would drift the first time either was edited, and the
        # failure that would produce — a charter whose content depends on
        # which path wrote it — is the one this guard exists to close.
        charter = (
            f"bolt.md is the BOLT'S CHARTER, and it is {sections} and nothing "
            f"else. Its merge criteria section states the landing mode on a "
            f"`Landing: merge` or `Landing: pr` line. State that line even if "
            f"the rendered template does not show one: a landing mode that was "
            f"defaulted is not a mode that was declared. Run `openspec "
            f"instructions bolt --change {self.params.slug}` for what belongs "
            f"under each heading — that template is the authority for their "
            f"content.\n\n"
            + (f"Write those sections from this bolt milestone's description, "
               f"which is the charter's stated source:\n\n{described}\n\n"
               if described else
               f"This bolt's milestone carries no description, so write those "
               f"sections from what the milestone and its items say. A thinner "
               f"charter, never a missing one — all four sections are still "
               f"written.\n\n")
            + f"No unit's plan document goes into bolt.md, whether or not the "
            f"milestone carries unit cards. Each approved unit is its own "
            f"artifact at units/<slug>.md, and the loop writes those itself at "
            f"expansion — write none of them.\n\n"
            f"Commit by pathspec, in THIS worktree on the "
            f"branch already checked out — never create a branch or worktree; "
            f"the loop cuts the bolt branch after you settle. Do not start any other work, "
            f"and do not touch the items. Deliver by settling.")
        invocation, framing = (
            (f"/opsx:continue {self.params.slug}",
             f"The bolt record for bolt/{self.params.slug} already exists at "
             f"openspec/changes/{self.params.slug}, and its charter is what is "
             f"owed: there is no bolt.md in it. Add that one artifact to the "
             f"change that is there — do not create a change and do not "
             f"scaffold a second one. That change should be bound to the "
             f"{self.params.type_name} schema; confirm the binding before you "
             f"write, and bind it if it is not, because a change bound to some "
             f"other schema has no bolt artifact to continue to.\n\n")
            if continuing else
            (f"/opsx:new {self.params.slug}",
             f"Scaffold the bolt record for bolt/{self.params.slug} and bind "
             f"the {self.params.type_name} schema.\n\n"))
        order = sessions.work_order(invocation, framing + charter)
        outcome = self.drive("scaffold", self.spec_for(
            "scaffold", name, self.params.bolt_worktree, order))
        if not outcome.ok:
            return f"scaffold: {outcome.status} — {outcome.detail}"
        if not self.params.change_dir.exists():
            tail = " ".join((outcome.report or "").split())[-300:]
            return (f"scaffold: the session settled but "
                    f"openspec/changes/{self.params.slug} is still missing"
                    + (f" — its report: {tail}" if tail else ""))
        # The reader, not a second regex. A separate parser here would be a
        # second definition of "what does this charter say", and two readers
        # disagreeing about that is the failure this change exists to close.
        if not self.merge_criteria():
            return (f"scaffold: the session settled but "
                    f"openspec/changes/{self.params.slug}/bolt.md carries no "
                    f"bolt-level `## Merge criteria` section with a body — a "
                    f"charter opens with {sections}, and the landing reads the "
                    f"merge criteria to know what to verify")
        actions.append(
            f"wrote the charter into openspec/changes/{self.params.slug}"
            if continuing else
            f"scaffolded openspec/changes/{self.params.slug}")
        return None

    def guard_topology(self, actions):
        """0.5 — the bolt branch and its worktree are the loop's to cut.

        The record is born on main at scaffold; cutting `bolt/<slug>` from
        it is the first topological act, and it is the LOOP'S — a session
        never creates a worktree (worktrunk's agent-handoff pattern).
        Idempotent: an existing worktree is adopted by path, so this writes
        nothing on a second cycle. Skipped on --dry-run and under a
        fixture tracker; wt's canonical path wins even over an explicit
        --bolt-worktree, because adoption-by-path is what a restarted
        stateless loop relies on.
        """
        if self.dry_run or isinstance(self.tracker, FixtureTracker):
            return None
        path, created = self.worktree_for(self.params.bolt_branch,
                                          self.params.main_branch)
        if path is None:
            return (f"topology: wt could not provide {self.params.bolt_branch} "
                    f"and its worktree")
        self.params.bolt_worktree = path
        if created:
            actions.append(f"cut {self.params.bolt_branch} and its worktree")
        return None

    def units_dir(self):
        """`openspec/changes/<slug>/units` — one file per approved unit."""
        return self.params.change_dir / "units"

    def _committed_units(self, rel_dir):
        """The unit file NAMES this record carries at HEAD, as a set.

        `git ls-tree -r`, never a directory listing: the question is what
        the record COMMITTED. A file the working tree holds and HEAD does
        not is precisely the torn write this guard exists to repair, and a
        listing cannot tell the two apart.
        """
        listed = self.git("ls-tree", "-r", "--name-only", "HEAD", "--", rel_dir)
        if listed.returncode != 0:
            return set()
        return {line.rsplit("/", 1)[-1]
                for line in (listed.stdout or "").splitlines() if line.strip()}

    def guard_charter(self, snapshot, actions):
        """0.6 — every approved unit's plan document, durable in git.

        A plan document is mutable tracker state while its card is
        unapproved. The operator's approval freezes it and expansion is
        what makes it prose in git, so this guard writes one file per
        expanded unit: `openspec/changes/<slug>/units/<unit-slug>.md`, the
        card's body verbatim, named by the slug the card's title carries.

        **A unit file is not written into the charter.** `bolt.md` is the
        bolt's statement — scope, sources, repos, merge criteria — and a
        unit file is the approval's; neither is appended to the other. The
        append this guard used to make is what put a unit's `##`
        subsections in the same file as the bolt's, where the criteria
        reader could find the wrong one.

        **Ordered after `guard_topology`, not folded into `_expand_card`.**
        Expansion runs at -1, before the bolt branch or its worktree exist
        on a fresh process, so a git write from there would land on
        whatever branch `repo_dir` has checked out. By 0.6
        `params.bolt_worktree` names the bolt branch's worktree and the
        write lands where the bolt's record lives. It also keeps
        expansion's failure modes to one — the tracker's — rather than two.

        **The test is the record's COMMITTED state, not a stored flag and
        not the working tree.** The loop is stateless by construction and
        re-derives what it can from the tracker and the tree, as
        `guard_stages` does for `stage:*`. So this compares the file names
        under `units/` AT HEAD against the `unit`-labeled issues on the
        milestone, and writes only what is missing. Reading the working
        tree instead would hide a torn write forever — the file is on disk
        the moment `write_text` returns, so a pass after a failed or
        interrupted commit would find it "present", report a clean dry
        cycle, and never retry the commit the requirement asks for.

        **A torn write is repaired, not read as done, and never rewritten.**
        A file on disk that HEAD does not carry keeps its content exactly
        as it stands — durable prose in git outranks the tracker state it
        came from, and the body on the card may have moved since — and only
        the add and the commit are re-run. A file already at HEAD is
        skipped entirely, whether this guard or a hand wrote it.

        **A record in the older shape needs no migration.** Its unit prose
        sits in a `# Unit: <slug>` section of `bolt.md`, so it has no unit
        file, so this same path writes one. The stale section is left
        exactly where it is: rewriting committed prose is what the rule
        above forbids, and `merge_criteria()` bounds itself to the
        charter's region so the section cannot masquerade as the bolt's.

        A pass with nothing newly expanded writes nothing and commits
        nothing — the dry-cycle property every other guard has.
        """
        if not self.params.change_dir.exists():
            return None      # nothing to write into; the scaffold owes it
        rel_dir = f"openspec/changes/{self.params.slug}/units"
        sealed = self._committed_units(rel_dir)
        wanted = []
        for item in sorted(snapshot.on(self.params.milestone),
                           key=lambda i: i.number):
            if inbox.UNIT not in item.labels:
                continue
            # The unit IS the card that was expanded, so the card's own
            # title grammar is what names its slug — and `PlanCard.slug`
            # yields `[a-z0-9][a-z0-9-]*`, which needs no sanitising to be
            # a file name. A title that parses no slug is the subject of a
            # sibling change and is left alone here.
            slug = inbox.PlanCard(number=item.number, title=item.title).slug
            if not slug or f"{slug}.md" in sealed:
                continue
            if not (item.body or "").strip():
                self._log(f"charter: unit #{item.number} has an empty body; "
                          f"nothing to write to {rel_dir}/{slug}.md")
                continue
            sealed.add(f"{slug}.md")
            wanted.append((slug, item.body))
        if not wanted:
            return None
        named = ", ".join(f"{slug}.md" for slug, _ in wanted)
        if self.dry_run:
            actions.append(f"would write unit file(s) {named} under {rel_dir}")
            return None
        if isinstance(self.tracker, FixtureTracker):
            # `guard_topology` skips itself under a fixture too, so
            # `bolt_worktree` is still `repo_dir` — the OPERATOR'S checkout,
            # on whatever branch happens to be out. A fixture run exercises
            # the tracker's filters; it never writes anyone's tree.
            return None
        self.ledger.expect(f"charter:{self.params.slug}",
                           f"{rel_dir} missing {named}",
                           f"one commit adding {named}")
        paths = []
        for slug, body in wanted:
            path = self.units_dir() / f"{slug}.md"
            paths.append(f"{rel_dir}/{slug}.md")
            if path.exists():
                continue     # a torn write: the content stays, the commit re-runs
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body.strip() + "\n")
        # By pathspec, on the branch the bolt's record lives on. Never `-a`
        # and never `add -A`: a session's uncommitted work may share this
        # worktree, and a tree-wide stage would sweep it into this commit.
        self.git("add", "--", *paths)
        committed = self.git("commit", "-m",
                             f"charter: unit {named} on {self.params.bolt_branch}",
                             "--", *paths)
        if committed.returncode != 0:
            tail = " ".join((committed.stderr or committed.stdout or "").split())
            return (f"charter: {rel_dir} gained {named} but the commit failed; "
                    f"the next pass retries it"
                    + (f" — {tail[-300:]}" if tail else ""))
        self.ledger.actual(f"charter:{self.params.slug}",
                           f"{named} committed under {rel_dir}")
        actions.append(f"charter gained unit file(s) {named} in {rel_dir}")
        return None

    def guard_flip_consume(self, snapshot, actions):
        """1 — the sub-issues a Ready unit releases.

        The operator's flip to Ready IS the approval; this guard consumes
        it. Applying the plan empties it, which is the dry-cycle property.
        """
        flipped = []
        for number in inbox.flip_consume_plan(snapshot, self.params.milestone):
            if self.dry_run:
                actions.append(f"would flip #{number} state:queued -> state:ready")
                flipped.append(number)
                continue
            self.tracker.add_label(number, inbox.READY)
            self.tracker.remove_label(number, inbox.QUEUED)
            actions.append(f"#{number} state:queued -> state:ready "
                           f"(its unit is at board Ready)")
            flipped.append(number)
        return flipped

    #: Where the charter's region ends: the first `# `-level heading that
    #: opens a unit section. Nothing writes one any more — an approved
    #: unit's document is its own file under `units/` — but records
    #: written under the older shape still carry them. Case-insensitive,
    #: matching how `PlanCard.slug` parses the title these were named from.
    UNIT_SECTION = re.compile(r"^#\s+Unit:\s*\S+\s*$",
                              re.MULTILINE | re.IGNORECASE)

    def charter_region(self, text):
        """The charter's own text: everything before the first `# Unit:`
        heading, and the whole file when there is none."""
        opened = self.UNIT_SECTION.search(text)
        return text[:opened.start()] if opened else text

    def merge_criteria(self):
        """This bolt's Merge criteria, read from the charter's region.

        **The region, not the whole file.** `bolt.md` is the bolt's
        statement and carries no unit's document — but records written
        under the older shape carry `# Unit: <slug>` sections whose plan
        documents have `##` subsections of their own, and one of those can
        be a `## Merge criteria`. Searching the whole file returns the
        first such section anywhere in it, so a charter with none of its
        own hands back a UNIT'S criteria as the bolt's, and
        `landing_mode()` then takes a `Landing:` line from prose that
        never spoke for this bolt. Bounding the read first makes "the
        bolt's criteria" mean the charter's, and makes the absent case
        genuinely absent — so the scaffold's check and the landing's
        refusal both fire on such a record instead of passing it.

        Within the region the section still ends at the next heading of
        either level, so a charter whose criteria are followed by another
        `##` section stops where it should.
        """
        record = self.params.change_dir / "bolt.md"
        if not record.exists():
            return ""
        match = re.search(
            r"^##\s+Merge criteria\s*$(?P<body>.*?)(?=^#{1,2}\s|\Z)",
            self.charter_region(record.read_text()),
            re.MULTILINE | re.DOTALL)
        return (match.group("body").strip() if match else "")

    def landing_mode(self):
        """`Landing: merge` (the default) or `Landing: pr`, per bolt.md."""
        match = re.search(r"Landing:\s*(merge|pr)\b", self.merge_criteria() or "", re.I)
        return match.group(1).lower() if match else "merge"

    def spec_stage(self, batch):
        """The type's strategy, run as prompts on one spec session.

        `ff` is one command; `new+ff` lands the proposal first; `new+continue`
        walks artifact by artifact. The hooks a type declares are the
        boundaries between these prompts — where a review attaches when
        extensions arrive. Green means the change validates, run here.
        """
        if self.params.plan_mode:
            return StageOutcome("spec", "skipped",
                                "plan-mode path: the approved plan is the spec")
        change = batch.change or batch.slug
        cwd = self.batch_worktree(batch)
        if cwd is None:
            return StageOutcome("spec", "failed",
                                f"wt could not provide build/{batch.slug} "
                                f"from {self.params.bolt_branch}")
        # A resumed batch whose change already validates needs no spec
        # session — green is green, and re-driving one costs a session per
        # restart for work that is provably done.
        if self.change_validates(change, cwd=cwd):
            return StageOutcome("spec", "done",
                                "the change already validates — nothing to spec")
        name = session_name("spec-writing", change)
        invocations = list(self.params.config.invocations)
        order = sessions.work_order(f"{invocations[0]} {change}", self.spec_brief(batch, change))
        outcome = self.drive("spec", self.spec_for(
            "spec", name, cwd, order), batch.numbers, close=False)
        runner, handle = self.runner("spec"), outcome.handle
        for invocation in invocations[1:]:
            if not outcome.ok:
                break
            rounds = MAX_CONTINUE_ROUNDS if invocation == "/opsx:continue" else 1
            for _ in range(rounds):
                origin = self._clock()
                runner.send(handle, f"{invocation} {change}")
                outcome = self.settle("spec", runner, handle, batch.numbers,
                                      origin, close=False)
                if not outcome.ok or self.change_validates(change, cwd=cwd):
                    break
        if outcome.ok and not self.change_validates(change, cwd=cwd):
            outcome = StageOutcome("spec", "failed",
                                   f"`openspec validate {change} --strict` is not green")
        if outcome.handle is not None:
            self.runner("spec").close(outcome.handle)
        return outcome

    def spec_brief(self, batch, change):
        items = ", ".join(f"#{n}" for n in batch.numbers)
        records = ", ".join(sorted({i.record for i in batch.items if i.record})) or (
            "the item bodies themselves — the assertion IS the proposal")
        book = (f"The design book lives at {self.params.book_dir} — the "
                f"items' chapter citations (books/flywheel/src/...) resolve "
                f"under its repo root. READ the cited chapters before "
                f"writing: the spec derives from the chapters as they are "
                f"NOW, not from the item's summary of them. "
                if self.params.book_dir else "")
        return (
            f"Spec for {items} on milestone {self.params.milestone}.\n\n"
            + book +
            f"One spec-driven change for these assertions, derived from {records} "
            f"and the decisions they cite, never from a restatement. You are IN "
            f"the build/{batch.slug} worktree, already cut from "
            f"{self.params.bolt_branch} by the loop — work here, and never "
            f"create a branch or worktree. "
            f"`openspec validate {change} --strict` green before it counts.\n\n"
            f"Record what you specced as a comment on each item. Commit by pathspec; "
            f"do not merge and do not push — the loop merges. Deliver by settling.")

    def build_stage(self, batch):
        """`/opsx:apply`, or the plan-mode path where the bolt declares it."""
        change = batch.change or batch.slug
        name = session_name("build", batch.slug)
        if not self.params.plan_mode and not self.deliverables(batch, change):
            # Symmetric with spec's already-validates skip — but a commit on
            # the branch proves only that something was committed, and a
            # spec session's planning artifacts satisfy that alone (observed
            # live on #260: build skipped over zero implementation). The
            # build's witness is the change's own task list: every box
            # checked, or the build still owes work.
            tasks = (Path(self.batch_worktree(batch) or self.params.repo_dir)
                     / "openspec" / "changes" / change / "tasks.md")
            unchecked = tasks.exists() and "- [ ]" in tasks.read_text()
            if not unchecked:
                return StageOutcome("build", "done",
                                    "already built — the tree proves it")
        if self.params.plan_mode:
            outcome = self.plan_mode_build(batch, name)
        else:
            # The order is the command and the commit rule, nothing else:
            # the session is launched IN the build worktree, the slug alone
            # points opsx at its context, and the tracker is the loop's —
            # items, worktree prose and escalation hints in a work order
            # are what prime the roaming (#167, extended by the operator's
            # ruling to every work session).
            order = sessions.work_order(f"/opsx:apply {change}", (
                "Commit by pathspec (git add -- <your paths>; "
                "git commit -- <your paths>); never -a, never add -A. "
                "Do not merge and do not push."))
            cwd = self.batch_worktree(batch)
            if cwd is None:
                return StageOutcome("build", "failed",
                                    f"wt could not provide build/{batch.slug}")
            outcome = self.drive("build", self.spec_for(
                "build", name, cwd, order), batch.numbers, close=False)
        if not outcome.ok:
            return outcome
        missing = self.deliverables(batch,
                                    change=None if self.params.plan_mode else change)
        if missing:
            outcome = self.reprompt_deliverables(batch, outcome, missing)
        return outcome

    def reprompt_deliverables(self, batch, outcome, missing):
        """Settle without deliverables is ONE re-prompt, then needs-operator."""
        runner, handle = self.runner("build"), outcome.handle
        told = "; ".join(missing)
        if handle is None:
            self.pause(batch.numbers, f"The build settled without its deliverables "
                                      f"({told}) and its pane is gone.")
            return StageOutcome("build", "paused", f"no deliverables: {told}")
        # ONE re-prompt across every process that will ever own this batch:
        # the marker is a tracker comment, so a restarted loop sees its
        # predecessor's re-prompt and pauses instead of re-prompting again.
        marker = f"{SESSION_OPEN} reprompt build-{batch.slug} -->"
        for comment in self.tracker.comments(batch.numbers[0]) or ():
            body = comment.get("body", "") if isinstance(comment, dict) else str(comment)
            if marker in body:
                self.pause(batch.numbers, (
                    f"The build settled without its deliverables again after an "
                    f"earlier re-prompt ({told}). The loop paused the item "
                    f"rather than re-prompting a second time."))
                return StageOutcome("build", "paused", f"no deliverables: {told}")
        self.tracker.comment(batch.numbers[0], marker)
        origin = self._clock()
        runner.send(handle, (
            f"Your batch settled without the deliverables the contract names: {told}. "
            f"Finish exactly those and settle again — no new scope."))
        again = self.settle("build", runner, handle, batch.numbers, origin, close=False)
        if not again.ok:
            return again
        still = self.deliverables(batch,
                                  change=None if self.params.plan_mode else
                                  (batch.change or batch.slug))
        if still:
            self.pause(batch.numbers, (
                f"The build settled twice without its deliverables: {'; '.join(still)}. "
                f"The loop paused the item rather than re-prompting again."))
            return StageOutcome("build", "paused", f"no deliverables: {'; '.join(still)}")
        return again

    def plan_mode_build(self, batch, name):
        """The plan-mode path: the approved plan is the spec surrogate.

        The session is started in `--permission-mode plan` and settles at
        the dialog. Approval is a judgment — does the plan do what the claim
        says, on the files the claim names — so it is asked of a session and
        the loop drives the dialog keys with the verdict it gets back. Two
        returns on one batch and the loop pauses rather than bouncing again.
        """
        order = sessions.work_order("/flywheel:build", self.plan_brief(batch))
        runner = self.runner("build")
        cwd = self.batch_worktree(batch)
        if cwd is None:
            return StageOutcome("build", "failed",
                                f"wt could not provide build/{batch.slug}")
        spec = self.spec_for("build", name, cwd, order, plan_mode=True)
        try:
            handle = runner.launch(spec)
        except sessions.SessionError as error:
            return StageOutcome("build", "failed", f"launch: {error}")
        origin = self.launch_origin(batch.numbers, name)
        if origin is None:
            origin = self._clock()
            self.mark_launch(batch.numbers, name, origin)
        while True:
            outcome = self.settle("build", runner, handle, batch.numbers,
                                  origin, close=False)
            if outcome.status in ("stalled", "failed"):
                return outcome
            verdict, why = self.judge_plan(batch, handle, outcome.report)
            if verdict == "approved":
                # The approved plan IS the spec surrogate on this path, so
                # the approval is where `stage:planned` is earned.
                self.set_stage(batch.numbers, inbox.STAGE_PLANNED)
                runner.send_keys(handle, "enter")
                origin = self._clock()          # the clock restarts at approval
                continue
            if verdict == "returned":
                returns = self._plan_returns.get(batch.slug, 0) + 1
                self._plan_returns[batch.slug] = returns
                if returns > MAX_PLAN_RETURNS:
                    self.pause(batch.numbers, (
                        f"The plan was returned {returns} times on the same batch; the "
                        f"loop paused it rather than bouncing again. Last mismatch: {why}"))
                    return StageOutcome("build", "paused",
                                        f"plan returned {returns}x", handle)
                runner.send(handle, f"MISMATCH: {why}\n\nRevise the plan and present it again.")
                origin = self._clock()
                continue
            if outcome.status == "blocked":
                return outcome                  # a real permission ask, not a plan
            return outcome                      # settled finished

    def plan_brief(self, batch):
        items = ", ".join(f"#{n}" for n in batch.numbers)
        return (
            f"PLAN-MODE PATH — read this before the skill's own steps. This bolt "
            f"writes NO spec-driven change for these items, so there is no change id "
            f"to open. You are started in --permission-mode plan: your APPROVED PLAN "
            f"is the spec surrogate. Present the plan, wait, then build exactly it.\n\n"
            f"Session type: build. Items: {items} on milestone {self.params.milestone}.\n\n"
            f"Each item's BODY IS ITS CLAIM. Read the bodies from the tracker and the "
            f"decision records they cite, and derive the work from those, never from a "
            f"restatement.\n\n"
            f"Worktree: in \"{self.params.repo_dir}\" run  wt switch --create "
            f"build/{batch.slug} --base {self.params.bolt_branch} --no-cd  and work "
            f"there. Re-read from disk every neighbour your plan claims something "
            f"about, at build time.\n\n"
            f"Flip nothing on the tracker; comment on each item what you built and what "
            f"you verified. Commit by pathspec; never -a, never add -A. Do not merge "
            f"and do not push — the loop merges.\n\n"
            f"ANDON CORD: if the work is wrong in a way no further round fixes, stop, "
            f"write the andon marker in your item comment, and settle without building. "
            f"Deliver by settling.")

    def judge_plan(self, batch, handle, pane):
        """Is this plan the claim's plan? One session, one parsed line."""
        claims = "\n\n---\n\n".join(
            f"#{i.number} {i.title}\n{i.body or '(body empty)'}" for i in batch.items)
        name = session_name("plan", batch.slug)
        order = sessions.work_order(
            f"Judge one plan-mode plan against the claims it is meant to implement.",
            (f"You are the approver, and you do none of the work yourself. The standard "
             f"is narrow: does the plan do WHAT THE CLAIM SAYS, on the files the claim "
             f"names? Not whether you would have designed it that way.\n\n"
             f"Return it when the plan contradicts a claim, silently drops one of the "
             f"items, or would edit outside what the claims name.\n\n"
             f"CLAIMS>>>\n{claims}\n<<<CLAIMS\n\n"
             f"THE PANE, as the session produced it (composer ghost text is not "
             f"input)>>>\n{pane}\n<<<PANE\n\n"
             f"Answer with exactly one line and nothing after it:\n"
             f"APPROVED: <the plan in one sentence>\n"
             f"or\n"
             f"RETURNED: <which claim, which part of the plan, in one or two sentences>"))
        outcome = self.drive("plan", self.spec_for(
            "plan", name, self.params.repo_dir, order))
        if not outcome.ok:
            return "unreadable", "the approver did not answer"
        match = _PLAN.search(outcome.report or "")
        if not match:
            return "unreadable", "the approver's verdict was unreadable"
        return match.group("verdict").lower(), match.group("why").strip()

    def verify_stage(self, batch, build):
        """`/opsx:verify` -> a findings file -> the review's ruling.

        Verify runs vanilla and writes what it found to a file the loop
        owns (#200) — never a verdict: judging the findings is not its
        job. The ruling belongs to the REVIEW session, the operator's
        proxy — proceed, refix with the exact prompt for the build
        session, or escalate. Work sessions do work, the review judges,
        the loop does bookkeeping.
        """
        if self.params.plan_mode:
            return StageOutcome("verify", "skipped",
                                "plan-mode path: there is no change to verify against")
        change = batch.change or batch.slug
        name = session_name("verify", batch.slug)
        cwd = self.batch_worktree(batch) or self.params.repo_dir
        branch_sha = self.head_sha(f"build/{batch.slug}")
        if branch_sha and self.verified_at(batch.numbers) == branch_sha:
            # The verdict is durable and the branch has not moved: a
            # restarted loop re-buys no judgment it already recorded.
            if build.handle is not None:
                self.runner("build").close(build.handle)
            return StageOutcome("verify", "done",
                                f"verified at {branch_sha[:9]} — the branch has not moved")
        for _ in range(MAX_FIX_ROUNDS + 1):
            self.clear_channel(cwd, VERIFY_REPORT)
            order = sessions.work_order(f"/opsx:verify {change}", (
                f"Write the findings to {VERIFY_REPORT} in this worktree — "
                f"plain markdown, or the single word {NO_FINDINGS} if there "
                f"are none. Fix nothing."))
            outcome = self.drive("verify", self.spec_for(
                "verify", name, cwd, order), batch.numbers)
            if not outcome.ok:
                return outcome
            report = self.read_channel(cwd, VERIFY_REPORT)
            if report is None:
                self.pause(batch.numbers, (
                    f"Verify settled without writing {VERIFY_REPORT}, so the "
                    f"loop has no report to hand the review."))
                return StageOutcome("verify", "paused", "no verify report file")
            clean = report.upper() == NO_FINDINGS
            if clean and self.change_validates(change, cwd=cwd):
                # The build pane's purpose — the build/verify conversation —
                # ends here. The session stays resumable by its id.
                if build.handle is not None:
                    self.runner("build").close(build.handle)
                self.mark_verified(batch)
                return StageOutcome("verify", "done", "verify is clean")
            if clean:
                report = (f"Verify reported no findings, but `openspec "
                          f"validate {change} --strict` is not green.")
            ruling = self.review_stage(batch, change, cwd, report)
            if ruling["action"] == "proceed":
                if build.handle is not None:
                    self.runner("build").close(build.handle)
                self.mark_verified(batch)
                return StageOutcome(
                    "verify", "done",
                    f"review ruled proceed: {ruling.get('reason', '')}".strip())
            if ruling["action"] == "escalate":
                self.pause(batch.numbers, (
                    f"The review escalated the verify findings: "
                    f"{ruling.get('reason', 'no reason given')}\n\n{report}"))
                return StageOutcome("verify", "paused", "review escalated",
                                    report=report)
            prompt = ruling.get("prompt") or (
                f"Verify raised these findings against what you built. Go fix "
                f"them — no new scope.\n\n{report}")
            fixed = self.go_fix(batch, build, prompt)
            if not fixed.ok:
                return fixed
        self.pause(batch.numbers, (
            f"Verify still has findings after {MAX_FIX_ROUNDS} refix rounds; "
            f"the loop paused the item rather than running another."))
        return StageOutcome("verify", "paused", "fix rounds exhausted")

    def review_stage(self, batch, change, cwd, report):
        """The operator's proxy: the one act of judgment in the cycle.

        Are these findings blocking, and what exactly should the build
        session be told? That is not verify's call and not the loop's —
        it is the operator's, and this session stands in for them. For
        now the proxy is whoever answers in the pane, the operator
        included; the destination is a profile that rules the way they
        would. A ruling the loop cannot read is an escalation, never a
        guess.
        """
        name = session_name("review", batch.slug)
        self.clear_channel(cwd, REVIEW_RULING)
        order = sessions.work_order(
            f"Review the verify findings for {change} and rule.",
            (f"You are the operator's proxy. Judge; fix nothing. Weigh the "
             f"findings below against the change itself, then write your "
             f"ruling to {REVIEW_RULING} in this worktree as one JSON "
             f"object, one of:\n\n"
             f'  {{"action": "proceed", "reason": "<why these findings do not block the merge>"}}\n'
             f'  {{"action": "refix", "prompt": "<the exact prompt to send the build session>"}}\n'
             f'  {{"action": "escalate", "reason": "<what the operator must look at>"}}\n\n'
             f"Escalate ONLY when the operator must decide something before "
             f"the merge. A change you judge merge-ready is a proceed, "
             f"whatever else you want the operator to know — put it in the "
             f"reason; an escalation on merge-ready work pauses the bolt "
             f"for nothing.\n\n"
             f"FINDINGS>>>\n{report}\n<<<FINDINGS"))
        outcome = self.drive("review", self.spec_for(
            "review", name, cwd, order), batch.numbers)
        if not outcome.ok:
            return {"action": "escalate",
                    "reason": f"the review session did not settle: {outcome.detail}"}
        raw = self.read_channel(cwd, REVIEW_RULING)
        try:
            ruling = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            ruling = None
        if (not isinstance(ruling, dict)
                or ruling.get("action") not in ("proceed", "refix", "escalate")):
            return {"action": "escalate",
                    "reason": f"no readable ruling at {REVIEW_RULING}"}
        return ruling

    def go_fix(self, batch, build, prompt):
        """The review's prompt — to the same build session, warm.

        The prompt arrives verbatim from the review's ruling (or the
        loop's plain fallback); this method only carries it. Same pane
        when it is open; when it is gone (a restart, a closed pane), the
        deterministic session id resumes the same conversation in a fresh
        pane — the pane is disposable, the session is durable (#178). A
        gone pane is never a reason to pause."""
        runner, handle = self.runner("build"), build.handle
        if handle is None:
            name = session_name("build", batch.slug)
            cwd = self.batch_worktree(batch) or self.params.repo_dir
            spec = self.spec_for("build", name, cwd, sessions.work_order(
                f"Fix verify findings for {batch.change or batch.slug}", prompt))
            try:
                handle = runner.launch(spec)
            except sessions.SessionError as error:
                self.pause(batch.numbers, f"The refix relaunch failed: {error}"
                                          f"\n\n{prompt}")
                return StageOutcome("build", "paused", "fix relaunch failed")
            if handle.reused:
                # Reattach never re-sends an order; the findings still must
                # arrive.
                runner.send(handle, prompt)
            outcome = self.settle("build", runner, handle, batch.numbers,
                                  self._clock(), close=False)
            if outcome.status == "blocked":
                self.pause(batch.numbers, (
                    f"The build session asked a question during a go-fix round. Its "
                    f"pane is open and waiting.\n\n{outcome.report}"))
            return outcome
        origin = self._clock()
        runner.send(handle, prompt)
        outcome = self.settle("build", runner, handle, batch.numbers, origin, close=False)
        if outcome.status == "blocked":
            self.pause(batch.numbers, (
                f"The build session asked a question during a go-fix round. Its pane is "
                f"open and waiting.\n\n{outcome.report}"))
        return outcome

    def merge_stage(self, batch, build=None):
        """Merge-back through the gate — a static step, no session.

        Merging is bookkeeping: the command is fixed, the gate is the
        repo's `[pre-merge]` hooks and runs identically either way, and
        success is ancestry, which git answers. Serialization is the
        caller's — `run` merges in a plain loop. The short-circuit asks
        `batch_merged` — advancement past the cut point as well as
        ancestry — because an untouched branch's tip is an ancestor of
        everything it was cut from (#164).

        The failure paths are where the judgment lives, and neither
        belongs to a merge agent: a RED GATE is a finding and goes back
        to the build session with the gate's own output as the prompt,
        bounded by the same fix-round budget as verify; a CONFLICT means
        a sibling moved under this branch — an agent seat is reserved
        for that, stubbed today to a pause the operator works by hand.
        """
        branch = f"build/{batch.slug}"
        if self.batch_merged(batch):
            return StageOutcome("merge", "done", f"{branch} is already merged")
        output = ""
        for attempt in range(MAX_FIX_ROUNDS + 1):
            proc = self.shell(["wt", "merge", branch, "--no-remove"],
                              cwd=self.params.bolt_worktree)
            if proc.returncode == 0:
                break
            output = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
            if "conflict" in output.lower():
                self.shell(["git", "merge", "--abort"],
                           cwd=self.params.bolt_worktree)
                self.pause(batch.numbers, (
                    f"The merge of {branch} hit conflicts — a sibling moved "
                    f"under it. The loop aborted the merge and paused the "
                    f"batch for the operator.\n\n{output}"))
                return StageOutcome("merge", "paused", "merge conflict",
                                    report=output)
            if attempt >= MAX_FIX_ROUNDS:
                self.pause(batch.numbers, (
                    f"The merge gate stayed red after {MAX_FIX_ROUNDS} refix "
                    f"rounds; the loop paused the batch.\n\n{output}"))
                return StageOutcome("merge", "paused", "gate red after refix",
                                    report=output)
            fixed = self.go_fix(
                batch, build or StageOutcome("build", "done"),
                (f"The merge gate is red for {branch}. Fix exactly what it "
                 f"names — no new scope — and commit by pathspec.\n\n{output}"))
            if not fixed.ok:
                return fixed
        if not self.branch_merged(branch):
            return StageOutcome("merge", "failed",
                                f"{branch} is not an ancestor of "
                                f"{self.params.bolt_branch} after wt merge")
        change = None if self.params.plan_mode else (batch.change or batch.slug)
        note = ""
        if change:
            # Archive on green is a loop write now, like every other piece
            # of bookkeeping. A failed archive never un-merges the branch.
            archived = self.shell(["openspec", "archive", change, "--yes"],
                                  cwd=self.params.bolt_worktree)
            if archived.returncode == 0:
                self.shell(["git", "add", "-A", "openspec"],
                           cwd=self.params.bolt_worktree)
                self.shell(["git", "commit", "-m",
                            f"chore(openspec): archive {change}"],
                           cwd=self.params.bolt_worktree)
            else:
                note = " (openspec archive failed; left for hand cleanup)"
        return StageOutcome("merge", "done", f"{branch} merged{note}")

    def close_merged(self, items, sha=None):
        """Close these work items `closed:merged`, with the SHA.

        The unit parent's progress bar is GitHub's own and counts CLOSED
        sub-issues, so the check-off happens here rather than at the
        landing. `closed:merged` — not a close with no reason — is what
        keeps tracker.md invariant 5 verbatim: exactly one `closed:*`
        reason on a closed item, at every moment. The landing upgrades it.

        Closing is the LOOP's, made against git's ancestry answer — the
        merge session comments and closes nothing, for the reason the
        landing already gives: closing is bookkeeping, not judgment.

        **The skip asks both halves.** Closing writes the reason label and
        then the state, so an item carrying `closed:merged` while still
        open is a torn close, not a finished one. Skipping on the label
        alone made this function a no-op on exactly the state the
        re-derivation guard sends here to be repaired — the item stayed
        open forever and the guard reported a write it had not made.
        `closed_with` reads both fields from the one payload `has_label`
        was already fetching, so the correction costs nothing.
        """
        sha = sha or self.head_sha(self.params.bolt_branch)
        closed = []
        for item in items:
            if self.tracker.closed_with(item.number, inbox.CLOSED_MERGED):
                continue
            self.tracker.close(
                item.number,
                f"Merged to {self.params.bolt_branch} as {sha}. Awaiting the "
                f"landing, which upgrades this to `closed:done` with the "
                f"landing SHA.",
                reason=inbox.CLOSED_MERGED)
            closed.append(item.number)
        return closed

    def land_stage(self, snapshot):
        """Landing per bolt.md: the criteria, then the mode, then closure.

        The session verifies every merge criterion by running it, and files
        the one born-ready fix item when one fails; the loop confirms the
        landing itself with git and does the bookkeeping — the SHA on each
        item and the close — because closing is bookkeeping, not judgment.

        Its item set is the milestone's open items **and** its
        `closed:merged` ones. The latter are closed and still in flight: the
        merge boundary closed them so the unit parent's bar would advance
        there, and this stage still owes each of them the upgrade to
        `closed:done` and the landing SHA. Reading open items alone would
        land a bolt and upgrade nothing.
        """
        self._landing_attempts += 1
        mode = self.landing_mode()
        on_milestone = snapshot.on(self.params.milestone)
        items = [i for i in on_milestone if i.is_open or i.merge_closed]
        # EVERY unlanded item, open or merge-closed. This set is not "what
        # the session is told to work" — the order below names the bolt, not
        # items — it is the loop's own tracker surface for this stage: the
        # launch marker the stall budget is recovered from, the notify and
        # failure pauses, and the andon the landing session may raise. Once
        # the merge boundary closes every assertion, an open-items-only set
        # is EMPTY on the handoff path, and all four of those go silent:
        # the pause writes no `needs-operator` anywhere and the andon marker
        # the landing session's own work order tells it to write is never
        # read. The landing is the last boundary, with no session downstream
        # to catch what it drops.
        numbers = [i.number for i in items]
        # Three refusals before anything is driven or closed. A live wait on
        # any item means a question is standing — landing over it is how
        # #96–#99 got closed over an unanswered andon (#164). A charter that
        # states no merge criteria gives the landing nothing to verify, and
        # "verified an empty list" is not a green landing. And a bolt
        # branch that never advanced past its cut point has nothing to
        # land: its ancestry into main is vacuously true.
        #
        # All three live HERE rather than beside the release conditions.
        # The release conditions answer "may this bolt land yet", and the
        # operator's gesture releases them; these answer "is there anything
        # to land, and anything to verify", which no gesture on the board
        # fixes — so they fail rather than hold. It is also what gives the
        # charter refusal its forced-landing behaviour for free: a force is
        # a claim about the operator's release, never about what the
        # charter says, and `land="force"` reaches this line like any
        # other landing.
        for parent in items:
            # The close-ready wait lives on the unit parent, and the close
            # that started this landing IS its answer.
            if parent.is_container and inbox.NEEDS_OPERATOR in parent.labels:
                self.tracker.remove_label(parent.number, inbox.NEEDS_OPERATOR)
        waiting = [i.number for i in items
                   if inbox.NEEDS_OPERATOR in i.labels and not i.is_container]
        if waiting:
            return StageOutcome("land", "paused",
                                "a live wait stands on "
                                + ", ".join(f"#{n}" for n in waiting)
                                + " — the landing waits for the operator")
        if not self.merge_criteria():
            # No section, an empty body, or no bolt.md at all — the reader
            # answers `""` to all three, and the refusal is the same one.
            return StageOutcome(
                "land", "failed",
                f"openspec/changes/{self.params.slug}/bolt.md — its merge "
                f"criteria could not be read: the charter carries no "
                f"bolt-level `## Merge criteria` section with a body. Nothing "
                f"was verified, nothing reached {self.params.main_branch}, "
                f"nothing closed")
        if not self.branch_advanced(self.params.bolt_branch):
            return StageOutcome("land", "failed",
                                f"{self.params.bolt_branch} carries no work "
                                f"beyond its cut point — nothing to land, "
                                f"nothing closed")
        name = session_name("land", self.params.slug)
        order = sessions.work_order(
            f"Land bolt/{self.params.slug} per its bolt.md.",
            (f"Read openspec/changes/{self.params.slug}/bolt.md on "
             f"{self.params.bolt_branch} and VERIFY every one of its Merge criteria on "
             f"that branch, by running them, not by reading the code. If any fails: "
             f"land NOTHING and report the failing criterion.\n\n"
             + (f"Its Landing line reads merge: land {self.params.bolt_branch} on "
                f"{self.params.main_branch} through the gate (wt merge, never --yes / "
                f"--no-hooks / --no-verify), one writer to main at a time.\n\n"
                if mode == "merge" else
                f"Its Landing line reads pr: push {self.params.bolt_branch} and open a "
                f"pull request to {self.params.main_branch} (gh pr create); report its "
                f"URL. Close nothing — the items close when the PR merges.\n\n")
             + f"On a failing criterion: create ONE fix item, born state:ready on this "
               f"bolt, unless an open fix item for that criterion already exists — then "
               f"report and stop. A criterion failing AGAIN after its fix landed is the "
               f"andon cord: write the andon marker on the item and settle, never "
               f"another item.\n\nDeliver by settling."))
        outcome = self.drive("land", self.spec_for(
            "land", name, self.params.repo_dir, order), numbers)
        if not outcome.ok:
            return outcome
        if mode == "pr":
            return StageOutcome("land", "done", "pull request opened; nothing closed",
                                report=outcome.report)
        if not self.branch_merged(self.params.bolt_branch, self.params.main_branch):
            paused, found = self.andon(numbers)
            if found:
                self.pause([paused], f"The landing session raised the andon cord: "
                                     f"{found.reason}")
                return StageOutcome("land", "paused", f"andon on #{paused}: {found.reason}")
            if self._landing_attempts >= MAX_LANDING_ATTEMPTS:
                self.pause(numbers, "The landing failed twice in one run; the loop "
                                    "paused the bolt rather than birthing another item.")
                return StageOutcome("land", "paused", "landing failed twice")
            return StageOutcome("land", "failed",
                                f"{self.params.bolt_branch} did not land on "
                                f"{self.params.main_branch}", report=outcome.report)
        sha = self.head_sha(self.params.main_branch)
        for item in items:
            if item.is_container:
                continue
            if inbox.CLOSED_DONE in item.labels and not item.is_open:
                continue                      # already landed; never re-closed
            # Upgrade, not close: the item is already closed at
            # `closed:merged`, and it must end carrying exactly one reason —
            # never both, never neither. An item that arrives without
            # `closed:merged` (a bolt landed by a path that never merged it
            # back, an item closed by hand) still ends at `closed:done`.
            self.tracker.reclose(
                item.number,
                f"Landed on {self.params.main_branch} as {sha}.",
                was=inbox.CLOSED_MERGED if inbox.CLOSED_MERGED in item.labels
                    else None,
                now=inbox.CLOSED_DONE)
        self.close_unit_parents(snapshot, items, sha)
        return StageOutcome("land", "done", f"landed as {sha}", report=outcome.report)

    def close_unit_parents(self, snapshot, items, sha):
        """Close the units this landing finishes. Containers only.

        A bolt milestone holds as many units as the operator has approved
        cards on it, and one landing serves them all — so this closes
        **every** open unit on the milestone, not one. By here each unit's
        bar is full and every assertion has been upgraded to `closed:done`,
        so the release each carries is finished and there is nothing further
        any of them can gate. Nothing closed them before, so a born-ready
        bolt's units stayed open at Status Ready and their milestone reported
        a job on every server sweep — before the landing, after it, and after
        the operator closed the milestone, where it collided with the
        `archive` job the same sweep adds.

        **No sub-issue is touched.** The assertions' own closes belong to the
        merge boundary and to the upgrade above; a container's close is not a
        cascade, and the tracker's rule that whoever holds the evidence closes
        with exactly one reason is not relaxed for a container. An elaboration
        on the milestone is skipped — it authorizes design work, not this
        release — and a unit already closed is not closed a second time.

        Two handles, because the two release paths put a unit in different
        places. Born-ready units sit on this bolt's milestone and are in the
        snapshot's own batches, however many of them there are. The handoff
        parent sits on the `intent/<slug>` milestone — deliberately, since it
        is born before any assertion has moved — so it is reachable only
        through a landed item's `parent_batch`, and only when the snapshot
        carries the edge at all. Where it does not, the server's Ready-batch
        condition is what keeps a stale parent from naming a job forever; the
        two answer the same finding from opposite ends.
        """
        landed = {i.number for i in items}
        numbers = {b.number for b in snapshot.batches
                   if b.kind == inbox.UNIT and b.milestone == self.params.milestone}
        numbers |= {i.parent_batch for i in items if i.parent_batch}
        for number in sorted(numbers - landed):
            batch = snapshot.batch(number)
            if batch is not None and batch.kind == inbox.ELABORATION:
                continue           # an elaboration authorizes design, not this release
            item = snapshot.item(number)
            if item is not None and not item.is_open:
                continue                              # already closed; never re-closed
            self.tracker.close(
                number,
                f"The release this unit carries is finished: "
                f"bolt/{self.params.slug} landed on {self.params.main_branch} as "
                f"{sha}, and every assertion it released is closed:done.",
                reason=inbox.CLOSED_DONE)

    # -- the cycle ---------------------------------------------------------

    def _batch_plan(self, batch):
        """One batch's drive expectations, keyed by stage — the rows the
        gate hashes and the drive records as it goes."""
        config = self.params.config
        items = ", ".join(f"#{n}" for n in batch.numbers)
        branch = f"build/{batch.slug}"
        rows = {}
        if config.runs("spec"):
            rows["spec"] = {"step": f"spec:{batch.slug}",
                            "trigger": f"{items} ready",
                            "expected": f"change validates, commit on {branch}"}
        if config.runs("build"):
            rows["build"] = {"step": f"build:{batch.slug}",
                             "trigger": "spec validated",
                             "expected": f"commit by pathspec on {branch}"}
        if config.runs("verify"):
            rows["verify"] = {"step": f"verify:{batch.slug}",
                              "trigger": "build commit landed",
                              "expected": f"{VERIFY_REPORT} = {NO_FINDINGS}"}
        if config.runs("merge"):
            rows["merge"] = {"step": f"merge:{batch.slug}",
                             "trigger": "verify clean",
                             "expected": (f"{branch} merged to "
                                          f"{self.params.bolt_branch}")}
        return rows

    def drive_plan(self, batches):
        return [row for batch in batches
                for row in self._batch_plan(batch).values()]

    def _drive(self, batch, stage_name, stage_call):
        """One drive stage, its expect written before and its actual after."""
        row = self._batch_plan(batch).get(stage_name)
        if row:
            self.ledger.expect(row["step"], row["trigger"], row["expected"])
        outcome = stage_call()
        self.ledger.actual(f"{outcome.stage}:{batch.slug}",
                           f"{outcome.status}: {outcome.detail}",
                           ok=outcome.ok)
        return outcome

    def cycle(self, number):
        result = CycleResult(number=number)
        snapshot = self.tracker.snapshot(self.params.milestone)
        actions, failure = self.guards(snapshot)
        result.actions = tuple(actions)
        if failure:
            result.halted = failure
            # The report renders the ready set; a halt before the drive must
            # not read as "nothing ready" when the queue is full.
            result.ready = tuple(
                i.number for i in inbox.bolt_inbox(snapshot, self.params.slug).ready)
            return result
        if actions:
            snapshot = self.tracker.snapshot(self.params.milestone)
        box = inbox.bolt_inbox(snapshot, self.params.slug)
        result.ready = tuple(i.number for i in box.ready)
        self.ledger.precondition(
            ("ready " + ", ".join(f"#{n}" for n in result.ready))
            if result.ready else "nothing ready")
        for index, action in enumerate(actions):
            # Guards write as they check, so expected and actual are the
            # same sentence — recorded, per the spec, but never gated.
            step = f"guard:{result.number}.{index}"
            self.ledger.expect(step, "idempotent repair", action)
            self.ledger.actual(step, action)
        if not box.ready and not box.in_progress and not actions:
            result.stopped = "nothing is ready and the guards wrote nothing"
            return result
        work, held = after_split(snapshot, inbox.unblocked(snapshot, box.ready))
        work = list(work)
        for item, why in held:
            self.ledger.note(f"deferred #{item.number}: {why}")
        resume = [i for i in inbox.unblocked(snapshot, box.in_progress)
                  if i not in work]
        if not work and not resume:
            result.stopped = (
                ("every ready item waits on the plan's chain — "
                 + ", ".join(f"#{i.number} {why}" for i, why in held))
                if held else
                "every ready item is blocked by an open item — "
                "nothing to work this cycle")
            return result
        batches = analyse(tuple(work) + tuple(resume), snapshot, self.params.slug)
        done = [b for b in batches if self.batch_merged(b)]
        batches = [b for b in batches if b not in done]
        if done:
            # merged-awaiting-landing: nothing to drive, and a restarted
            # process must still reach for the landing it never saw happen.
            self._resume_landing = True
        if not batches:
            result.stopped = (f"every batch is merged to "
                              f"{self.params.bolt_branch} — awaiting the landing")
            return result
        if self.dry_run:
            result.outcomes = tuple(
                StageOutcome("batch", "skipped",
                             f"build/{b.slug} would take "
                             + ", ".join(f"#{n}" for n in b.numbers))
                for b in batches)
            result.stopped = "dry run — nothing launched, nothing written"
            return result
        if not self.ledger.gate(self.drive_plan(batches)):
            result.stopped = ("gated — the expectation report awaits "
                              "flywheel approve")
            return result
        outcomes = []
        merged = 0
        for batch in batches:
            paused, found = self.andon(batch.numbers)
            if found:
                self.pause([paused], f"A session raised the andon cord: {found.reason}")
                self.ledger.note(f"andon on #{paused}: {found.reason}")
                outcomes.append(StageOutcome("batch", "paused",
                                             f"andon on #{paused}: {found.reason}"))
                continue
            self.flip_in_progress(batch.numbers)
            config = self.params.config
            if config.runs("spec"):
                spec = self._drive(batch, "spec",
                                   lambda: self.spec_stage(batch))
                outcomes.append(spec)
                if not spec.ok:
                    continue
                # `spec.ran`, not `spec.ok`: on the plan-mode path the spec
                # stage is SKIPPED — there is no change to validate — and
                # `plan_mode_build` writes `stage:planned` at the approval
                # instead, the one boundary that path actually has.
                if spec.ran:
                    self.set_stage(batch.numbers, inbox.STAGE_PLANNED)
            build = StageOutcome("build", "skipped",
                                 "the type declares no build stage")
            if config.runs("build"):
                build = self._drive(batch, "build",
                                    lambda: self.build_stage(batch))
                outcomes.append(build)
                if not build.ok:
                    continue
                # `build.ran` is the deliverables check having passed, not
                # the session's word: no commit on the branch and the stage
                # paused.
                if build.ran:
                    self.set_stage(batch.numbers, inbox.STAGE_BUILT)
                    # The tracker comment is the loop's — bookkeeping was
                    # never the builder's job, and the work order no longer
                    # points the session at the tracker at all.
                    sha = self.head_sha(f"build/{batch.slug}")
                    for n in batch.numbers:
                        self.tracker.comment(
                            n, f"Built on build/{batch.slug} as {sha}.")
            if config.runs("verify"):
                verify = self._drive(batch, "verify",
                                     lambda: self.verify_stage(batch, build))
                outcomes.append(verify)
                if not verify.ok:
                    continue
                # `verify.ran`, not `verify.ok`: the plan-mode path skips
                # verify while `bolt-quick` still DECLARES it, so `ok` alone
                # would label an item verified with no session ever run.
                if verify.ran:
                    self.set_stage(batch.numbers, inbox.STAGE_VERIFIED)
            if config.runs("merge"):
                merge = self._drive(batch, "merge",
                                    lambda: self.merge_stage(batch, build))
                outcomes.append(merge)
                if merge.ran:
                    # merge_stage returns done only on ancestry git confirmed.
                    # `ran` rather than `ok` for the same reason as the three
                    # boundaries above: all four write off "did it happen",
                    # so a stage that later learns to skip cannot quietly
                    # start labelling itself.
                    self.set_stage(batch.numbers, inbox.STAGE_MERGED)
                    self.close_merged(batch.items)
                    merged += 1
                    self._merged += 1
        result.outcomes = tuple(outcomes)
        if merged == 0:
            result.stopped = ("no batch reached the bolt branch this cycle — "
                              "stopping rather than re-driving the same work")
        return result

    def run(self, max_cycles=None, land="auto"):
        """Cycles until STOP, a halt, or the cycle bound.

        There is no cycle bound by default and none is needed: the ready set
        cannot refill itself (new items are queued, never ready, without the
        operator's flip) and the guards are idempotent, so `actions` drains
        and STOP fires. `max_cycles` is for a caller that wants one pass.

        **`land="auto"` lands only a bolt this run itself moved.** An empty
        ready set is not the same fact as finished work: on a live bolt it
        is also what a process sees while its siblings' sessions are still
        building, and a landing session started then would verify the merge
        criteria against a half-built branch. So the default is to land only
        when this run merged something; `land="force"` is for the operator
        or the server resuming a run that died between the last merge and
        the landing, and `land=False` never lands at all.

        **An open unit card outranks all of that.** `holding_cards` is asked
        first and its answer is final: while the operator has a card left to
        rule on this milestone the bolt is still being planned, so the run
        reports the hold — by card number, on the landing line — and reaches
        for no landing at all, `land="force"` included.
        """
        report = RunReport(milestone=self.params.milestone)
        number = 0
        while True:
            number += 1
            result = self.cycle(number)
            report.cycles.append(result)
            self._log(self.describe(result))
            if result.stopped:
                self.ledger.note(f"STOP — {result.stopped}")
            if result.halted:
                report.halted = result.halted
                self.ledger.note(f"HALTED — {result.halted}")
                self._finish_observation()
                return report
            if result.stopped:
                break
            if max_cycles and number >= max_cycles:
                break
        snapshot = self.tracker.snapshot(self.params.milestone)
        box = inbox.bolt_inbox(snapshot, self.params.slug)
        on_milestone = snapshot.on(self.params.milestone)
        open_items = [i for i in on_milestone if i.is_open]
        report.queue = [f"#{i.number} {i.title}" for i in open_items if i.queued]
        unlanded = open_items + [i for i in on_milestone if i.merge_closed]
        held = self.holding_cards(snapshot)
        if held:
            # New cards reopened the delivery: a close-ready mark placed
            # earlier is no longer true, so it comes off until the new
            # units finish too.
            if not self.dry_run:
                for parent in (i for i in open_items if i.is_container
                               and inbox.NEEDS_OPERATOR in i.labels):
                    self.tracker.remove_label(parent.number,
                                              inbox.NEEDS_OPERATOR)
                    self.ledger.note(f"close-ready withdrawn from "
                                     f"#{parent.number} — new card(s) hold "
                                     f"the landing")
            cards = ", ".join(f"#{c.number}" for c in held)
            self._log(f"landing held — unit card(s) still open: {cards}")
            self.ledger.note(
                f"landing held — the bolt still holds open unit card(s) {cards}")
            report.landing = ("held — the bolt still holds open unit "
                              f"card(s) {cards}")
            self._finish_observation()
            return report
        work = [i for i in unlanded if not i.is_container]
        close_ready = (not box.ready and work
                       and all(i.merge_closed for i in work)
                       and any(i.milestone_state == "open" for i in work))
        if close_ready and not self.dry_run:
            # The one wait only the operator can end: everything is merged
            # and every card ruled, and the milestone close releases the
            # landing. The unit parent carries the wait so Waiting On Me
            # shows it; the close is the answer, and the landing removes
            # the label as it begins.
            for parent in (i for i in open_items if i.is_container
                           and inbox.NEEDS_OPERATOR not in i.labels):
                self.tracker.comment(parent.number, (
                    f"Ready to land: every item is merged to "
                    f"{self.params.bolt_branch} and every card is ruled. "
                    f"Closing the {self.params.milestone} milestone releases "
                    f"the landing to {self.params.main_branch}; the archive "
                    f"follows it."))
                self.tracker.add_label(parent.number, inbox.NEEDS_OPERATOR)
                self.ledger.note(f"close-ready — the wait is on "
                                 f"#{parent.number} for the operator's close")
                self._log(f"close-ready: waiting on the operator's milestone "
                          f"close (marked #{parent.number})")
        if not self.landing_wanted(land, box, unlanded):
            if close_ready:
                report.landing = "awaiting the operator's milestone close"
            self._finish_observation()
            return report
        landing_plan = [{
            "step": "landing",
            "trigger": f"every assertion merged to {self.params.bolt_branch}",
            "expected": ("merge criteria green; bolt landed on "
                         f"{self.params.main_branch}")}]
        if not self.ledger.gate(landing_plan):
            report.landing = ("gated — the expectation report awaits "
                              "flywheel approve")
            self._finish_observation()
            return report
        row = landing_plan[0]
        self.ledger.expect(row["step"], row["trigger"], row["expected"])
        outcome = self.land_stage(snapshot)
        report.landing = f"{outcome.status}: {outcome.detail}"
        self.ledger.actual("landing", report.landing, ok=outcome.ok)
        self._finish_observation()
        return report

    def _finish_observation(self):
        """Render the run's report and offer it to the observer hook.
        Best-effort throughout — observation never fails a run."""
        if not self.ledger.entries:
            return
        path = self.ledger.write_report()
        if not path:
            return
        self._log(f"observation report: {path}")
        hook = os.environ.get("FLYWHEEL_OBSERVER")
        if hook:
            self.shell([hook, str(path)])

    def landing_wanted(self, land, box, unlanded):
        """Whether this run should reach for a landing.

        `unlanded` is the milestone's open items PLUS its `closed:merged`
        ones. Counting only open items was right while nothing closed
        before the landing; now the last batch of a bolt merge-closes its
        items, and a test that read open items alone would see an empty
        milestone and never land the bolt at all.
        """
        if not land or self.dry_run:
            return False
        if not self.params.config.runs("land"):
            return False               # the type's declared sequence has no landing
        if box.ready:
            return False                       # there is still released work
        if not unlanded:
            return False                       # nothing to upgrade, nothing to land
        if land != "force" and any(
                i.milestone_state == "open" for i in unlanded):
            # The landing is the operator's: their milestone close releases
            # it, and merged work never reaches main on the machinery's own
            # initiative. Every item merged and every card ruled is necessary,
            # never sufficient. A FORCED landing passes this condition — the
            # `land != "force"` guard above — because a force is a claim by
            # the operator landing deliberately, or by the server resuming a
            # run that died between its last merge and its landing, and the
            # close it stands in for is being made by that same hand. The
            # open-card hold `holding_cards` carries is a SEPARATE condition
            # that a force does not pass; neither subsumes the other.
            # Specified by `flywheel-construction-stages`, "The operator's
            # milestone close releases the landing, and the card hold is
            # asked first".
            return False
        if land == "force" or self._merged > 0 or self._resume_landing:
            return True
        # `_merged` is PER PROCESS, and the server now starts a loop for a
        # milestone whose items are all `closed:merged` precisely so it can
        # land. That fresh process merges nothing itself, so counting only
        # its own merges declines the landing it was started for.
        #
        # The caution `_merged` encodes is kept: an empty ready set is also
        # what a process sees while a sibling's session is still building.
        # But an assertion at `closed:merged` HAS reached the bolt branch,
        # so a bolt whose every unlanded assertion is merge-closed has no
        # sibling still building, and the criteria are verified against a
        # whole branch rather than a half-built one.
        work = [i for i in unlanded if not i.is_container]
        return bool(work) and all(i.merge_closed for i in work)

    def holding_cards(self, snapshot):
        """The open unit cards that hold this bolt's landing.

        The landing is the bolt's boundary, not a unit's: one landing carries
        the branch to main for every unit the milestone holds. So a card the
        operator has not ruled yet is a bolt still being planned, and while
        one sits here nothing is verified against the bolt branch, nothing
        reaches main, and no `closed:merged` is upgraded.

        **The `plan` label draws the line, not the board.** Expansion swaps
        `plan` for `unit`, and `plan_cards` is the open `plan`-labelled
        issues, so an expanded unit has already left this set — which is what
        makes the hold satisfiable at all, since a unit stays open across the
        landing precisely so the landing can close it. Board Status and
        `stale` are not read: a card at Backlog holds exactly as one at Ready
        does. A card whose own milestone is not this one — including a card
        naming no `bolt/*` milestone, which `PlanCard.bolt` answers `None`
        for — is no bolt's card to hold here.

        **This hold is not the whole of the operator's release.** The
        milestone-close condition in `landing_wanted` survives beside it and
        is enforced too: an open card means the bolt is still being
        *planned*, an open milestone means the operator has not *released*
        what is built, and the two answer different questions. The card hold
        is asked FIRST, and its answer is final — so when both are
        outstanding the landing line names the card, the gesture the
        operator can act on next, rather than the milestone. Both conditions
        are specified by `flywheel-construction-stages`, "The operator's
        milestone close releases the landing, and the card hold is asked
        first".

        **Asked before `landing_wanted`, and blind to `land`.** Two reasons,
        and both are about what the run can then say. Folding the card test
        into `landing_wanted` would collapse "held" and "nothing to land"
        into one `False` and leave the report unable to tell the operator
        which — that is how a held bolt came to read `not attempted`. And
        `land="force"` is a claim about what *this process* knows, made by an
        operator or a server resuming a run that died before its landing; an
        open card is the operator's own unfinished gesture, and the way past
        it is to rule the card, never a flag.
        """
        return [c for c in getattr(snapshot, "plan_cards", ())
                if c.bolt == self.params.milestone]

    def describe(self, result):
        parts = [f"cycle {result.number}:"]
        parts.append(f"{len(result.ready)} ready" if result.ready else "nothing ready")
        parts.append(f"{len(result.actions)} guard write(s)")
        for outcome in result.outcomes:
            parts.append(f"{outcome.stage}={outcome.status}")
        if result.stopped:
            parts.append(f"STOP — {result.stopped}")
        if result.halted:
            parts.append(f"HALTED — {result.halted}")
        return " ".join(parts)


# ---------------------------------------------------------------------------
# Small readings
# ---------------------------------------------------------------------------
