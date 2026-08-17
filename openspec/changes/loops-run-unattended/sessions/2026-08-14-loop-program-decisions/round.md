# Six decisions, plain and short

Each one is a yes/no with my recommendation. Annotate anything you
disagree with; hit Approve if it all looks right.

## 1. A doc is out of date — update it to match the code

The background server that wakes the work loops already casts a
slightly wider net than the design doc says it should — on purpose, so
no work ever gets stranded. The code is right and tested; the doc is
stale.

**Recommendation: update the doc. No code changes.**

## 2. Leave the shared Python files where they are

Some helper modules live next to the commands that use them. A README
note questions whether they should move to a different folder. Moving
them would churn five commands and change nothing you can see.

**Recommendation: leave them; fix the README so it stops calling this
an open question.**

## 3. The design loop should create its own project folder

Right now, if a design project's folder doesn't exist on disk, nothing
creates it — proof: this very project had no folder until this session
made one by hand. There's a one-line command that creates it; no AI
involved.

**Recommendation: yes — the loop creates the folder automatically when
it's missing.**

## 4. Make the design loop configurable like the build loop

The build loop reads its settings (which models, how much review) from
a config block you can override per repo. The design loop's settings
are hard-coded in Python — you can't change them without editing the
code.

**Recommendation: give the design loop the same config block. A
placeholder for now, wired up later, same as the build loop's.**

## 5. A restarted loop should reconnect to running sessions

Today, if the loop restarts while sessions are mid-flight, it forgets
them — nobody watches them, nobody notices if one hangs.

**Recommendation: on restart, reconnect to sessions that are still
alive. If a session died mid-work, flag it for you — never blindly
re-run it, since that could redo or clobber finished work.**

## 6. Approval bundles get a summary

When work gets bundled up for your approval, the bundle has no
summary — one recently hit 19 items with an empty description, so
approving meant opening all 19 by hand.

**Recommendation: a cheap, quick AI pass writes a short brief into
each bundle: the themes, what's routine, what's risky, what needs your
call. Refreshed as the bundle grows; frozen the moment you approve.**
