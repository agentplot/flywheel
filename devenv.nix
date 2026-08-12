{ pkgs, config, ... }:

{
  # Three gates and a preview server, and that is the whole reason this repo
  # has a devenv. node runs two of the three checks and the mermaid bundle the
  # site check parses with, while sh runs the manifest validator;
  # python3 serves site/ locally, because the page must work as plain static
  # files or GitHub Pages will not serve it either.
  packages = [
    pkgs.nodejs_22
    pkgs.python3
  ];

  # `devenv shell -- gates` — the same three commands .config/wt.toml runs
  # before a merge and .github/workflows/gates.yml runs on every push. Three
  # callers, one definition, so a green claim in one place means the same thing
  # in the others.
  scripts.gates = {
    description = "Run every gate: plugin manifests, shipped paths, the site";
    exec = ''
      set -euo pipefail
      cd ${config.devenv.root}
      sh scripts/validate-manifests.sh
      node scripts/check-paths.mjs
      node scripts/check-site.mjs
    '';
  };

  # `devenv shell -- site-up` — serve site/ at http://127.0.0.1:8451/.
  # A static server rather than opening the file: the page loads its mermaid
  # bundle by relative path, and file:// and http:// resolve those differently
  # enough that a page that works one way can fail the other.
  scripts.site-up = {
    description = "Serve site/ at http://127.0.0.1:8451";
    exec = ''
      exec ${pkgs.python3}/bin/python3 -m http.server 8451 \
        --directory ${config.devenv.root}/site --bind 127.0.0.1
    '';
  };

  # `devenv shell -- vendor-mermaid` — refresh site/vendor/mermaid.min.js from
  # the pinned devDependency. The bundle is committed on purpose: the page
  # loads no CDN, so what a reader renders is a file in this repository, and
  # scripts/check-site.mjs parses that exact file.
  scripts.vendor-mermaid = {
    description = "Copy the pinned mermaid bundle into site/vendor/";
    exec = ''
      set -euo pipefail
      cd ${config.devenv.root}
      npm ci
      cp node_modules/mermaid/dist/mermaid.min.js site/vendor/mermaid.min.js
      echo "vendored $(node -p "require('./node_modules/mermaid/package.json').version")"
    '';
  };

  # Claude Code sessions in this repo run the flywheel's own machinery —
  # the agentplot fleet's dispatch and conductors start here — so the
  # plugin enables itself. Never edit .claude/settings.json directly:
  # this block generates it, activation rewrites it, and drift from the
  # declaration shows up as a git diff.
  claude.code = {
    enable = true;

    # Empty on purpose: the module's default would write a .mcp.json
    # (mcp.devenv.sh) that this repo does not use.
    mcpServers = { };
  };

  files."${config.claude.code.settingsPath}" = {
    # A real committed file, not the default symlink into /nix/store:
    # sessions open in fresh worktrees before anything activates devenv,
    # and git is the one delivery mechanism every worktree-creation path
    # shares.
    copyMode = "copy";

    json.enabledPlugins = {
      "flywheel@flywheel" = true;
    };
    json.extraKnownMarketplaces = {
      flywheel = {
        source = {
          source = "github";
          repo = "agentplot/flywheel";
        };
      };
    };
  };
}
