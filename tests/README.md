# tests/

The unit suite for the loop programs' substrate. Run it three ways, one
definition:

```sh
sh scripts/test.sh          # the definition
npm test                    # the conventional entry point
devenv shell -- tests       # inside the dev shell
```

**Stdlib `unittest`, no pytest, no requirements file.** Everything under
`bin/` is a zero-dependency stdlib script — that is this repo's stated bar —
and a test runner that needed a package install would be the first thing here
that did not clear it. `pkgs.python3` is already in `devenv.nix` for the site
server, so the suite adds no dependency at all.

`context.py` holds the one `sys.path` insert. The modules under test live
beside extensionless executables (`bin/` is on every installed user's `PATH`,
so what lands there is commands), which means `bin/` is not importable by
name and each test would otherwise repeat the same three lines.

Discovery runs with `-t tests` rather than `-t .` so that `tests/` itself goes
on `sys.path`; it is a directory of scripts, not a package, and there is no
`__init__.py` to make `-t .` work.

## What the suite is for

These tests exist because `design/loop-programs.md` claims the loops are
"ordinary Python … unit-testable, no agent asked to behave like code." That
claim is only true if the claims underneath it are checkable without herdr,
without `claude`, without a token, and without sleeping — so the runners take
an injected `run=`, `supervise` takes an injected `clock=`, and the inbox
filters are pure functions over a snapshot.

Two of them are properties rather than examples, and they are the ones worth
protecting:

- **the dry cycle** — applying a guard plan empties it, which is the bolt's
  own merge criterion ("two consecutive cycles against an unchanged tracker
  produce the same tracker state, and the second writes nothing") stated in a
  form a test can hold;
- **containment** — every milestone on which a loop filter finds work is a
  milestone the server filter hands out a job for. A server may
  over-approximate; a loop must be exact. When this one fails, work exists
  that no process will ever be started to do.

## Not a merge gate

`scripts/test.sh` is deliberately **not** registered in `.config/wt.toml`'s
`[pre-merge]` hooks. Those three are approval-gated in
`~/.config/worktrunk/approvals.toml`, and a fourth entry would make every
merge fail with `Cannot prompt for approval in non-interactive environment`
until the operator granted it by hand — which the bolt record forbids working
around. Wiring the suite into the gate and into CI is a separate item, with
the approval taken first.
