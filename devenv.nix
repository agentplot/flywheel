{ pkgs, config, ... }:

{
  # Two gates and a preview server, and that is the whole reason this repo has
  # a devenv. node runs both checks and the mermaid bundle they parse with;
  # python3 serves site/ locally, because the page must work as plain static
  # files or GitHub Pages will not serve it either.
  packages = [
    pkgs.nodejs_22
    pkgs.python3
  ];

  # `devenv shell -- gates` — the same two commands .config/wt.toml runs before
  # a merge and .github/workflows/gates.yml runs on every push. Three callers,
  # one definition, so a green claim in one place means the same thing in the
  # others.
  scripts.gates = {
    description = "Run every gate: plugin manifests, shipped paths, the site";
    exec = ''
      set -euo pipefail
      cd ${config.devenv.root}
      claude plugin validate ./.claude-plugin/plugin.json --strict
      claude plugin validate ./.claude-plugin/marketplace.json --strict
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
}
