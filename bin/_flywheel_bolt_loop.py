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
itself; the merge-criteria test that routes a discovery (guard 2); the
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
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _flywheel_inbox as inbox        # noqa: E402
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
    "route": "sonnet",     # the merge-criteria test — one item, one verdict
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

#: One retry of a failed landing per run: the first failure births the fix
#: item, the second is the andon cord's business, not another item's.
MAX_LANDING_ATTEMPTS = 2

#: A session's launch time, on the item, so a restarted loop measures the
#: stall budget from the launch rather than from its own start. Same shape
#: as the andon marker in `_flywheel_inbox`, and read the same way: code,
#: not judgment — half a marker is not a launch record.
SESSION_OPEN = "<!-- flywheel:session"
_SESSION = re.compile(
    r"<!--\s*flywheel:session\s+name=\"(?P<name>[^\"]+)\"\s+"
    r"started=\"(?P<started>\d+)\"\s*-->"
)

#: The one line a judgment session's answer is read from. Anything else is
#: unreadable on purpose: a verdict the loop cannot parse is a verdict it
#: does not act on.
_ROUTE = re.compile(r"^ROUTE:[ \t]*(?P<route>keep|intent/[\w.-]+|unmilestoned)[ \t]*$",
                    re.MULTILINE)
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
    block, inside = {}, False
    pending = None
    for line in (text or "").splitlines():
        if not inside:
            if re.match(r"^loop:\s*(#.*)?$", line):
                inside = True
            continue
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line[:1].isspace():
            break                              # dedent ends the block
        stripped = line.strip()
        if stripped.startswith("- "):
            if pending is not None:
                block.setdefault(pending, []).append(_scalar(stripped[2:]))
            continue
        match = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", stripped)
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


def _scalar(raw):
    return raw.strip().strip("'\"").strip()


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
    binding = {}
    pending = None
    for line in path.read_text().splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        stripped = line.strip()
        if stripped.startswith("- ") and pending is not None:
            binding.setdefault(pending, []).append(_scalar(stripped[2:]))
            continue
        match = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if not match:
            continue
        key, raw = match.group(1), match.group(2).strip()
        if raw.startswith("["):
            binding[key] = [_scalar(v) for v in raw.strip("[]").split(",") if v.strip()]
            pending = None
        elif raw:
            binding[key] = _scalar(raw)
            pending = None
        else:
            # A key with no value on its line opens a block list. It is
            # recorded even if no `- ` item follows, so an empty declaration
            # is still a declaration and still refusable.
            binding[key] = []
            pending = key
    return binding


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
        if comment:
            self.comment(number, comment)
        self.add_label(number, reason)
        self._api(f"/issues/{number}", "PATCH", {"state": "closed"})

    def reclose(self, number, comment=None, was=None, now=inbox.CLOSED_DONE):
        """Swap one `closed:*` reason for another on an already-closed item.

        The landing's upgrade. It must not depend on the item being open —
        it was closed at merge-back — and it must never leave the item
        carrying both reasons or neither, so the new label goes on before
        the old one comes off. The `state: closed` PATCH is repeated because
        an item that reached the landing without ever merging back (a bolt
        landed by another path, an item closed by hand) still has to end
        closed with the SHA on it.
        """
        if comment:
            self.comment(number, comment)
        self.add_label(number, now)
        if was and was != now:
            self.remove_label(number, was)
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

    WRITES = ("add_label", "remove_label", "comment", "set_milestone",
              "clear_milestone", "close", "reclose", "create_item")

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
                milestone=milestone)
        return snap

    def comments(self, number):
        raw = self._item(number) or {}
        return [c if isinstance(c, dict) else {"body": c}
                for c in raw.get("comments", ())]

    def has_label(self, number, label):
        raw = self._item(number) or {}
        return label in raw.get("labels", ())

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
    the unit an item was released in. Items sharing a parent ride together;
    an unparented item rides alone. Computed from the fields — this step
    reads and writes nothing, and reasons about nothing.
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
        change = {i.change for i in members if i.change}
        name = change.pop() if len(change) == 1 else (
            f"{slug}-{members[0].number}" if slug else f"item-{members[0].number}")
        batches.append(WorkBatch(slug=name, items=tuple(members)))
    return batches


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
        return self.status in ("done", "skipped")


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
                 clock=time.time, log=None, dry_run=False):
        self.params = params
        self.tracker = tracker
        self.dry_run = dry_run
        self._run = run
        self._clock = clock
        self._log = log or (lambda message: None)
        self._runner_factory = runner_factory or self._default_runner
        self._runners = {}
        self._plan_returns = {}
        self._fix_rounds = {}
        self._landing_attempts = 0
        self._merged = 0

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

    # -- objective checks: the world, not a report -------------------------

    def change_validates(self, change):
        """`openspec validate --strict` — green before a spec counts."""
        proc = self.shell(["openspec", "validate", change, "--strict"],
                          cwd=self.params.repo_dir)
        return proc.returncode == 0

    def branch_has_commits(self, branch):
        proc = self.git("rev-list", "--count",
                        f"{self.params.bolt_branch}..{branch}")
        return (proc.stdout or "0").strip().isdigit() and int(proc.stdout.strip()) > 0

    def branch_merged(self, branch, target=None):
        target = target or self.params.bolt_branch
        return self.git("merge-base", "--is-ancestor", branch, target).returncode == 0

    def head_sha(self, ref):
        return (self.git("rev-parse", ref).stdout or "").strip()

    def commented_since(self, number, since):
        """A comment on the item is the third leg of the deliverable
        contract. Comments the loop itself wrote do not count."""
        for comment in self.tracker.comments(number) or ():
            body = comment.get("body", "") if isinstance(comment, dict) else str(comment)
            if SESSION_OPEN in body:
                continue
            stamp = comment.get("created_at") if isinstance(comment, dict) else None
            if stamp is None:
                return True
            if _epoch(stamp) >= since:
                return True
        return False

    def deliverables(self, batch, since, change=None):
        """What "done" means for a construction session, checked on disk.

        "completion is objective — settle plus the deliverable contract
        (change validates, commit on branch, comment on item)". Missing
        deliverables are named, so the re-prompt can name them too.
        """
        missing = []
        if change and not self.change_validates(change):
            missing.append(f"`openspec validate {change} --strict` is not green")
        if not self.branch_has_commits(f"build/{batch.slug}"):
            missing.append(f"no commit on build/{batch.slug} beyond {self.params.bolt_branch}")
        silent = [n for n in batch.numbers if not self.commented_since(n, since)]
        if silent:
            missing.append("no comment on " + ", ".join(f"#{n}" for n in silent))
        return missing

    # -- the tracker side of a session ------------------------------------

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
        """The launch time this loop (or an earlier one) already recorded."""
        best = None
        for number in numbers:
            for comment in self.tracker.comments(number) or ():
                body = comment.get("body", "") if isinstance(comment, dict) else str(comment)
                for match in _SESSION.finditer(body):
                    if match.group("name") != name:
                        continue
                    started = int(match.group("started"))
                    best = started if best is None else min(best, started)
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
        origin = self.launch_origin(numbers, spec.name) if numbers else None
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
        if watch.notified and watch.state != sessions.WaitState.STALLED:
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
        return sessions.SessionSpec(
            name=name, cwd=str(cwd), order=order, profile=PROFILE,
            model=STAGE_MODELS.get(stage), plan_mode=plan_mode,
            runner=sessions.choose_runner(stage, self.params.runner_config))

    # -- guards ------------------------------------------------------------

    def guards(self, snapshot):
        """Every cycle, in the record's order, each idempotent.

        `actions` records ONLY the writes made. A check that changed
        nothing records nothing — an empty list is the normal, correct
        result, and the STOP condition is built on exactly that.
        """
        actions = []
        scaffolded = self.guard_scaffold(actions)
        if scaffolded is not None:
            return actions, scaffolded
        flipped = self.guard_flip_consume(snapshot, actions)
        failure = self.guard_route(snapshot, actions, skip=flipped)
        if failure is None:
            self.guard_stages(snapshot, actions)
        return actions, failure

    def guard_stages(self, snapshot, actions):
        """3 — re-derive `stage:built` and `stage:merged` from the tree.

        The loop is stateless by construction, so a process killed between
        an apply and its label write leaves an item whose git state is
        built and whose label is not. This repairs that without knowing
        anything about the process that died: an item whose branch is an
        ancestor of the bolt branch is merged, and otherwise an item whose
        branch holds a commit beyond the bolt branch is built. Both use the
        same two checks the boundary writes use — `branch_merged` and
        `branch_has_commits` — so the label and the boundary cannot
        disagree.

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
                 and not ({inbox.UNIT, inbox.ELABORATION} & i.labels)]
        if not items:
            return
        for batch in analyse(items, snapshot, self.params.slug):
            branch = f"build/{batch.slug}"
            if self.branch_merged(branch):
                target = inbox.STAGE_MERGED
            elif self.branch_has_commits(branch):
                target = inbox.STAGE_BUILT
            else:
                continue                # the tree witnesses nothing; write nothing
            for item in batch.items:
                current = inbox.stage_of(item.labels, inbox.CONSTRUCTION_STAGES)
                if current != target:
                    if target == inbox.STAGE_BUILT and current == inbox.STAGE_VERIFIED:
                        pass            # verified has no witness; never walked back
                    elif self.dry_run:
                        actions.append(f"would reconcile #{item.number} "
                                       f"{current or 'no stage'} -> {target}")
                    elif self.set_stage([item.number], target):
                        actions.append(f"#{item.number} {current or 'no stage'} "
                                       f"-> {target} (re-derived from {branch})")
                if target != inbox.STAGE_MERGED:
                    continue
                # The merged edge is ONE fact with TWO writes, so a process
                # killed between them leaves an item half-merged in the
                # tracker's eyes. Repair the close as well as the label.
                if not item.is_assertion:
                    continue
                if item.merge_closed or not item.is_open:
                    continue            # already closed; `closed:done` never walked back
                if self.dry_run:
                    actions.append(f"would close #{item.number} {inbox.CLOSED_MERGED}")
                    continue
                self.close_merged(WorkBatch(slug=batch.slug, items=(item,)))
                actions.append(f"#{item.number} closed {inbox.CLOSED_MERGED} "
                               f"(re-derived from {branch})")

    def guard_scaffold(self, actions):
        """0 — scaffold-if-missing.

        There is no non-interactive `openspec change new`, so the scaffold
        is a session like every other act of judgment-free work the loop
        cannot do with a subprocess. Idempotent: the directory existing is
        the whole test.
        """
        if self.params.change_dir.exists():
            return None
        if self.dry_run:
            actions.append(f"would scaffold openspec/changes/{self.params.slug} "
                           f"({self.params.type_name})")
            return None
        name = session_name("scaffold", self.params.slug)
        order = sessions.work_order(f"/opsx:new {self.params.slug}", (
            f"Scaffold the bolt record for bolt/{self.params.slug} and bind the "
            f"{self.params.type_name} schema. Write bolt.md from what the milestone "
            f"and its items say; commit by pathspec. Do not start any other work, "
            f"and do not touch the items. Deliver by settling."))
        outcome = self.drive("scaffold", self.spec_for(
            "scaffold", name, self.params.bolt_worktree, order))
        if not outcome.ok:
            return f"scaffold: {outcome.status} — {outcome.detail}"
        if not self.params.change_dir.exists():
            tail = " ".join((outcome.report or "").split())[-300:]
            return (f"scaffold: the session settled but "
                    f"openspec/changes/{self.params.slug} is still missing"
                    + (f" — its report: {tail}" if tail else ""))
        actions.append(f"scaffolded openspec/changes/{self.params.slug}")
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

    def guard_route(self, snapshot, actions, skip=()):
        """2 — discovery routing, by the merge-criteria test.

        The record's test is "a discovery joins the bolt's milestone only
        when the bolt's merge criteria need it; otherwise it goes to the
        intent that owns its subject, or unmilestoned for dispatch". That
        is a judgment about this bolt's criteria and this item's subject,
        so the loop asks one short session per orphan — with the criteria
        and the item body in front of it — and then makes the move itself.

        Idempotent in both directions: a routed item leaves the milestone
        and the next snapshot cannot see it; a kept item is composed into a
        unit and is no longer an orphan. So a second cycle asks nothing and
        writes nothing.
        """
        claimed = parented(snapshot)
        orphans = [
            i for i in snapshot.on(self.params.milestone)
            if i.is_open and i.queued and i.number not in skip
            and i.parent_batch is None and i.number not in claimed
        ]
        if not orphans:
            return None
        if self.dry_run:
            actions.append("would apply the merge-criteria test to " +
                           ", ".join(f"#{i.number}" for i in orphans))
            return None
        criteria = self.merge_criteria()
        intents = self.open_intents()
        keep = []
        for item in orphans:
            route, why = self.route_discovery(item, criteria, intents)
            if route == "keep":
                keep.append(item)
                continue
            reason = (f"Routed off bolt/{self.params.slug} by the merge-criteria "
                      f"test: this bolt can land without it. {why}".strip())
            if route == "unmilestoned":
                self.tracker.comment(item.number, reason +
                                     "\n\nUnmilestoned for dispatch to triage.")
                self.tracker.clear_milestone(item.number)
                actions.append(f"#{item.number} unmilestoned for triage")
            else:
                self.tracker.comment(item.number, reason +
                                     f"\n\nMoved to {route}, the intent that owns its subject.")
                self.tracker.set_milestone(item.number, route)
                actions.append(f"#{item.number} moved to {route}")
        if keep:
            composed = self.compose(keep)
            if composed:
                actions.append(composed)
        return None

    def merge_criteria(self):
        """The Merge criteria section of this bolt's bolt.md, from disk."""
        record = self.params.change_dir / "bolt.md"
        if not record.exists():
            return ""
        text = record.read_text()
        match = re.search(r"^##\s+Merge criteria\s*$(?P<body>.*?)(?=^##\s|\Z)",
                          text, re.MULTILINE | re.DOTALL)
        return (match.group("body").strip() if match else "")

    def landing_mode(self):
        """`Landing: merge` (the default) or `Landing: pr`, per bolt.md."""
        match = re.search(r"Landing:\s*(merge|pr)\b", self.merge_criteria() or "", re.I)
        return match.group(1).lower() if match else "merge"

    def open_intents(self):
        try:
            rows = self.tracker.milestones("open")
        except Exception:
            return []
        return [r["title"] for r in rows
                if str(r.get("title", "")).startswith(inbox.INTENT_PREFIX)]

    def route_discovery(self, item, criteria, intents):
        """One item, one verdict: the merge-criteria test, asked of a session.

        Unreadable answers route `keep`. Nothing leaves this bolt on a
        verdict the loop could not parse — the safe direction, because a
        kept item is visible in the queue and a wrongly-routed one is not.
        """
        name = session_name("route", f"{self.params.slug}-{item.number}")
        destinations = ", ".join(intents) or "(no open intent milestones)"
        order = sessions.work_order(
            f"Apply the merge-criteria test to one discovery on bolt/{self.params.slug}.",
            (f"The test, from the flywheel's tracker contract: a discovery made "
             f"during construction joins the bolt's milestone ONLY when the bolt's "
             f"merge criteria need it; otherwise it goes to the intent that owns its "
             f"subject, or stays unmilestoned for dispatch to triage.\n\n"
             f"THE ITEM — #{item.number} {item.title}\n{item.body}\n\n"
             f"THIS BOLT'S MERGE CRITERIA\n{criteria or '(none recorded)'}\n\n"
             f"Open intent milestones: {destinations}\n\n"
             f"Decide, and write nothing anywhere — the loop makes the move. "
             f"Answer with exactly two lines and nothing after them:\n"
             f"ROUTE: keep | intent/<slug> | unmilestoned\n"
             f"WHY: <one sentence naming the criterion that needs it, or why none does>"))
        outcome = self.drive("route", self.spec_for(
            "route", name, self.params.repo_dir, order))
        if not outcome.ok:
            return "keep", "the routing session did not answer; kept on the bolt"
        match = _ROUTE.search(outcome.report or "")
        if not match:
            return "keep", "the routing verdict was unreadable; kept on the bolt"
        route = match.group("route")
        why = ""
        found = re.search(r"^WHY:[ \t]*(?P<why>.+)$", outcome.report or "", re.MULTILINE)
        if found:
            why = found.group("why").strip()
        if route.startswith("intent/") and intents and route not in intents:
            return "keep", f"the verdict named {route}, which is not an open intent"
        return route, why

    def compose(self, items):
        """What stays on the bolt becomes one unit at Backlog.

        Backlog, never Ready: composing is the loop's, approving is the
        operator's, and a batch born at Ready would make the loop the
        approver of its own discoveries.
        """
        numbers = [str(i.number) for i in items]
        batch = Path(__file__).resolve().parent / "flywheel-batch"
        proc = self.shell([
            str(batch), "--kind", "unit", "--org", self.params.org,
            "--repo", self.params.repo, "--milestone", self.params.milestone,
            "--title", f"Work the discoveries queued on bolt/{self.params.slug}",
            *numbers], cwd=self.params.repo_dir)
        if proc.returncode != 0:
            self._log(f"compose failed: {(proc.stderr or proc.stdout or '').strip()}")
            return None
        return f"composed #{', #'.join(numbers)} into a unit at Backlog"

    # -- stages ------------------------------------------------------------

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
        name = session_name("spec-writing", change)
        invocations = list(self.params.config.invocations)
        order = sessions.work_order(f"{invocations[0]} {change}", self.spec_brief(batch, change))
        outcome = self.drive("spec", self.spec_for(
            "spec", name, self.params.repo_dir, order), batch.numbers, close=False)
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
                if not outcome.ok or self.change_validates(change):
                    break
        if outcome.ok and not self.change_validates(change):
            outcome = StageOutcome("spec", "failed",
                                   f"`openspec validate {change} --strict` is not green")
        if outcome.handle is not None:
            self.runner("spec").close(outcome.handle)
        return outcome

    def spec_brief(self, batch, change):
        items = ", ".join(f"#{n}" for n in batch.numbers)
        records = ", ".join(sorted({i.record for i in batch.items if i.record})) or (
            "the item bodies themselves — the assertion IS the proposal")
        return (
            f"Spec for {items} on milestone {self.params.milestone}.\n\n"
            f"One spec-driven change for these assertions, derived from {records} "
            f"and the decisions they cite, never from a restatement. Worktree: in "
            f"\"{self.params.repo_dir}\" run  wt switch --create build/{batch.slug} "
            f"--base {self.params.bolt_branch} --no-cd  and work there. "
            f"`openspec validate {change} --strict` green before it counts.\n\n"
            f"Record what you specced as a comment on each item. Commit by pathspec; "
            f"do not merge and do not push — the loop merges. Deliver by settling.")

    def build_stage(self, batch):
        """`/opsx:apply`, or the plan-mode path where the bolt declares it."""
        since = self._clock()
        change = batch.change or batch.slug
        name = session_name("build", batch.slug)
        if self.params.plan_mode:
            outcome = self.plan_mode_build(batch, name)
        else:
            order = sessions.work_order(f"/opsx:apply {change}", self.build_brief(batch))
            outcome = self.drive("build", self.spec_for(
                "build", name, self.params.repo_dir, order), batch.numbers, close=False)
        if not outcome.ok:
            return outcome
        missing = self.deliverables(batch, since,
                                    change=None if self.params.plan_mode else change)
        if missing:
            outcome = self.reprompt_deliverables(batch, outcome, missing)
        return outcome

    def build_brief(self, batch):
        items = ", ".join(f"#{n}" for n in batch.numbers)
        return (
            f"Build for {items} on milestone {self.params.milestone}.\n\n"
            f"Apply the change on the build/{batch.slug} worktree. Re-read from disk "
            f"every neighbour the spec claims something about — build time is when the "
            f"neighbours have had longest to move.\n\n"
            f"Comment on each item what you built and what you verified on disk versus "
            f"relayed. Commit by pathspec (git add <your paths>; git commit -- <your "
            f"paths>); never -a, never add -A. Do not merge and do not push — the loop "
            f"merges.\n\n"
            f"ANDON CORD: if the work is wrong in a way no further round fixes — the "
            f"spec contradicts the decision it cites, the tree contradicts the spec — "
            f"stop, write the andon marker in your item comment, and settle without "
            f"building. Deliver by settling.")

    def reprompt_deliverables(self, batch, outcome, missing):
        """Settle without deliverables is ONE re-prompt, then needs-operator."""
        runner, handle = self.runner("build"), outcome.handle
        told = "; ".join(missing)
        if handle is None:
            self.pause(batch.numbers, f"The build settled without its deliverables "
                                      f"({told}) and its pane is gone.")
            return StageOutcome("build", "paused", f"no deliverables: {told}")
        origin = self._clock()
        runner.send(handle, (
            f"Your batch settled without the deliverables the contract names: {told}. "
            f"Finish exactly those and settle again — no new scope."))
        again = self.settle("build", runner, handle, batch.numbers, origin, close=False)
        if not again.ok:
            return again
        still = self.deliverables(batch, origin,
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
        spec = self.spec_for("build", name, self.params.repo_dir, order, plan_mode=True)
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
        """`/opsx:verify`, then go-fix rounds on the SAME build session.

        The findings are handled the way the operator does it by hand: the
        loop re-prompts the session that built the work, relays what it
        asks by commenting on the item, and re-runs verify. Two rounds on
        the same finding and the item is paused with `needs-operator` — the
        finding is keyed by its own text, so "the same finding" is decided
        by comparison rather than by opinion.
        """
        if self.params.plan_mode:
            return StageOutcome("verify", "skipped",
                                "plan-mode path: there is no change to verify against")
        change = batch.change or batch.slug
        name = session_name("verify", batch.slug)
        seen = {}
        for _ in range(MAX_FIX_ROUNDS + 1):
            order = sessions.work_order(f"/opsx:verify {change}", (
                f"Verify what was built for {', '.join('#' + str(n) for n in batch.numbers)} "
                f"against the change's artifacts, on the build/{batch.slug} worktree. "
                f"Report the findings plainly, or say plainly that there are none. "
                f"Fix nothing. Deliver by settling."))
            outcome = self.drive("verify", self.spec_for(
                "verify", name, self.params.repo_dir, order), batch.numbers)
            if not outcome.ok:
                return outcome
            findings = (outcome.report or "").strip()
            if self.change_validates(change) and _no_findings(findings):
                return StageOutcome("verify", "done", "verify is clean")
            key = _finding_key(findings)
            seen[key] = seen.get(key, 0) + 1
            if seen[key] > MAX_FIX_ROUNDS - 1:
                self.pause(batch.numbers, (
                    f"Verify raised the same finding twice and the loop paused the item "
                    f"rather than a third round.\n\n{findings}"))
                return StageOutcome("verify", "paused", "same finding twice", report=findings)
            fixed = self.go_fix(batch, build, findings)
            if not fixed.ok:
                return fixed
        return StageOutcome("verify", "paused", "verify rounds exhausted")

    def go_fix(self, batch, build, findings):
        """"Go fix these" — to the same session, in the same pane."""
        runner, handle = self.runner("build"), build.handle
        if handle is None:
            self.pause(batch.numbers, f"Verify raised findings and the build session's "
                                      f"pane is gone.\n\n{findings}")
            return StageOutcome("build", "paused", "no session to re-prompt")
        origin = self._clock()
        runner.send(handle, (
            f"Verify raised these findings against what you built. Go fix them — no new "
            f"scope, and comment on the items what you changed.\n\n{findings}"))
        outcome = self.settle("build", runner, handle, batch.numbers, origin, close=False)
        if outcome.status == "blocked":
            self.pause(batch.numbers, (
                f"The build session asked a question during a go-fix round. Its pane is "
                f"open and waiting.\n\n{outcome.report}"))
        return outcome

    def merge_stage(self, batch):
        """Merge-back through the gate, one writer to the target branch.

        Serialization is the caller's — `run` merges in a plain loop and
        awaits each one — and the gate is the repo's `[pre-merge]` hooks,
        never suppressed. Success is ancestry, which git answers.
        """
        branch = f"build/{batch.slug}"
        if self.branch_merged(branch):
            return StageOutcome("merge", "done", f"{branch} is already merged")
        name = session_name("merge", batch.slug)
        change = None if self.params.plan_mode else (batch.change or batch.slug)
        order = sessions.work_order(
            f"Merge {branch} back to {self.params.bolt_branch} through the gate.",
            (f"Merge-back for {', '.join('#' + str(n) for n in batch.numbers)}.\n\n"
             f"In \"{self.params.bolt_worktree}\" run:  wt merge {branch} --no-remove  "
             f"— NEVER --yes, --no-hooks or --no-verify; this repo's [pre-merge] hooks "
             f"ARE the gate and are never suppressed or hand-substituted. If you hit "
             f"\"Cannot prompt for approval in non-interactive environment\", stop and "
             f"report it rather than working around it.\n\n"
             + (f"On green: openspec archive {change}, and commit.\n\n" if change else "")
             + f"On red: fix NOTHING and report the gate output verbatim. Do not "
               f"comment the SHA, do not label, do not close: the LOOP closes each "
               f"assertion `closed:merged` with the merge SHA once git confirms "
               f"the ancestry, and the landing upgrades that to `closed:done`; "
               f"closing is bookkeeping, and the loop and the session must not "
               f"race for it. THE ANDON CORD IS THE EXCEPTION and is always "
               f"yours: if the work has gone wrong in a way no further round "
               f"fixes, write the andon marker in an item comment and settle — "
               f"the loop reads that marker back and pauses the batch. "
               f"Deliver by settling."))
        outcome = self.drive("merge", self.spec_for(
            "merge", name, self.params.bolt_worktree, order), batch.numbers)
        if not outcome.ok:
            return outcome
        if not self.branch_merged(branch):
            return StageOutcome("merge", "failed",
                                f"{branch} is not an ancestor of {self.params.bolt_branch} "
                                f"after the merge session settled")
        return StageOutcome("merge", "done", f"{branch} merged", report=outcome.report)

    def close_merged(self, batch, sha=None):
        """Close the batch's assertion items `closed:merged`, with the SHA.

        The unit parent's progress bar is GitHub's own and counts CLOSED
        sub-issues, so the check-off happens here rather than at the
        landing. `closed:merged` — not a close with no reason — is what
        keeps tracker.md invariant 5 verbatim: exactly one `closed:*`
        reason on a closed item, at every moment. The landing upgrades it.

        **Only `type:assertion` items.** A discovery queued on the bolt
        closes on its own evidence, as it does today, and a batch merging
        past it must not sweep it up.

        Closing is the LOOP's, made against git's ancestry answer — the
        merge session comments and closes nothing, for the reason the
        landing already gives: closing is bookkeeping, not judgment.
        """
        sha = sha or self.head_sha(self.params.bolt_branch)
        closed = []
        for item in batch.items:
            if not item.is_assertion:
                continue
            if self.tracker.has_label(item.number, inbox.CLOSED_MERGED):
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
            if not item.is_assertion:
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
        return StageOutcome("land", "done", f"landed as {sha}", report=outcome.report)

    # -- the cycle ---------------------------------------------------------

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
        if not box.ready and not actions:
            result.stopped = "nothing is ready and the guards wrote nothing"
            return result
        work = inbox.unblocked(snapshot, box.ready)
        if not work:
            result.stopped = ("every ready item is blocked by an open item — "
                              "nothing to work this cycle")
            return result
        batches = analyse(work, snapshot, self.params.slug)
        if self.dry_run:
            result.outcomes = tuple(
                StageOutcome("batch", "skipped",
                             f"build/{b.slug} would take "
                             + ", ".join(f"#{n}" for n in b.numbers))
                for b in batches)
            result.stopped = "dry run — nothing launched, nothing written"
            return result
        outcomes = []
        merged = 0
        for batch in batches:
            paused, found = self.andon(batch.numbers)
            if found:
                self.pause([paused], f"A session raised the andon cord: {found.reason}")
                outcomes.append(StageOutcome("batch", "paused",
                                             f"andon on #{paused}: {found.reason}"))
                continue
            self.flip_in_progress(batch.numbers)
            config = self.params.config
            if config.runs("spec"):
                spec = self.spec_stage(batch)
                outcomes.append(spec)
                if not spec.ok:
                    continue
                # On the plan-mode path there is no spec to validate, and
                # `plan_mode_build` writes `stage:planned` at the approval
                # instead — the one boundary that path actually has.
                if not self.params.plan_mode:
                    self.set_stage(batch.numbers, inbox.STAGE_PLANNED)
            build = StageOutcome("build", "skipped",
                                 "the type declares no build stage")
            if config.runs("build"):
                build = self.build_stage(batch)
                outcomes.append(build)
                if not build.ok:
                    continue
                # `build.ok` is the deliverables check having passed, not the
                # session's word: no commit on the branch and the stage paused.
                self.set_stage(batch.numbers, inbox.STAGE_BUILT)
            if config.runs("verify"):
                verify = self.verify_stage(batch, build)
                outcomes.append(verify)
                if not verify.ok:
                    continue
                self.set_stage(batch.numbers, inbox.STAGE_VERIFIED)
            if config.runs("merge"):
                merge = self.merge_stage(batch)
                outcomes.append(merge)
                if merge.ok:
                    # merge_stage returns done only on ancestry git confirmed.
                    self.set_stage(batch.numbers, inbox.STAGE_MERGED)
                    self.close_merged(batch)
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
        """
        report = RunReport(milestone=self.params.milestone)
        number = 0
        while True:
            number += 1
            result = self.cycle(number)
            report.cycles.append(result)
            self._log(self.describe(result))
            if result.halted:
                report.halted = result.halted
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
        if not self.landing_wanted(land, box, unlanded):
            return report
        outcome = self.land_stage(snapshot)
        report.landing = f"{outcome.status}: {outcome.detail}"
        return report

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
        if land == "force" or self._merged > 0:
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
        assertions = [i for i in unlanded if i.is_assertion]
        return bool(assertions) and all(i.merge_closed for i in assertions)

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

def _finding_key(text):
    """The identity of a finding: its own text, whitespace-collapsed.

    "The same finding twice" has to be decided by comparison rather than by
    opinion, or the two-rounds-then-pause bound is one more judgment the
    loop is not entitled to make.
    """
    return hashlib.sha256(" ".join((text or "").split()).lower().encode()).hexdigest()[:16]


def _no_findings(text):
    """Whether a verify report says, in so many words, that it found nothing."""
    collapsed = " ".join((text or "").split()).lower()
    if not collapsed:
        return True
    return bool(re.search(r"\bno (findings|issues|problems)\b|\bnothing to (fix|report)\b"
                          r"|\bverify (is )?clean\b|\ball (checks|criteria) pass",
                          collapsed))


def _epoch(stamp):
    """GitHub's ISO timestamps, as seconds. Unreadable reads as very old."""
    try:
        from datetime import datetime
        return datetime.fromisoformat(str(stamp).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return 0.0
