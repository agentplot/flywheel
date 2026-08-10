# Environment probe, run at the start of this session

```
$ ls ~/.claude/skills/
1password/       agent-deck/      defuddle/        gh-cli/
git-commit/      herdr/           json-canvas/     lavish/
mermaid-diagrams/ pdf/            recutils/        restish/
worktrunk/
```

```
$ head -4 ~/.claude/skills/lavish/SKILL.md
---
name: lavish
description: Turn complex or visual agent responses into rich, reviewable HTML artifacts the user can annotate and send feedback on, using the lavish-axi CLI.
---
```

```
$ which lavish-axi
lavish-axi not found
```

```
$ npm ls -g --depth 0 2>/dev/null | grep lavish
(no output)
```

```
$ node --version
v22.14.0
$ npx --version
10.9.2
```
