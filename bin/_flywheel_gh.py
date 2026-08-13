"""Shared GitHub plumbing for the flywheel bin/ tools.

Token resolution, gh invocation, GraphQL, and the org-project lookups the
tracker tools share. Import from a sibling script:

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from _flywheel_gh import resolve_token, gh, graphql, GraphqlError
"""

import datetime
import json
import os
import subprocess
import sys
from pathlib import Path


class GraphqlError(Exception):
    pass


def resolve_token(org):
    """GH_TOKEN if set; otherwise mint via the sibling flywheel-token."""
    token = os.environ.get("GH_TOKEN")
    if token:
        return token
    helper = Path(__file__).resolve().parent / "flywheel-token"
    proc = subprocess.run([str(helper), "--org", org],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        sys.exit(proc.stderr.strip() or "flywheel: could not mint a token")
    return proc.stdout.strip()


def gh(token, *args, input_json=None):
    env = dict(os.environ, GH_TOKEN=token)
    stdin = json.dumps(input_json) if input_json is not None else None
    proc = subprocess.run(
        ["gh", *args], env=env, input=stdin, capture_output=True, text=True
    )
    if proc.returncode != 0:
        sys.exit(f"flywheel: gh {' '.join(args[:2])} failed: "
                 f"{proc.stderr.strip() or proc.stdout.strip()}")
    out = proc.stdout.strip()
    if not out:
        return {}
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        # NOT every gh subcommand speaks JSON. `gh api` does; `gh issue edit`,
        # `gh issue comment`, `gh issue create` and `gh issue close` print a URL
        # or a human line, and parsing one of those as JSON raised on SUCCESS.
        # Measured 2026-08-13: `gh issue edit 73 --add-label state:in-progress`
        # prints `https://github.com/agentplot/flywheel/issues/73`. Every write
        # in `_flywheel_inbox.Tracker` goes through one of those four, so the
        # raw text is returned rather than thrown: a caller that wants JSON is
        # calling `gh api` and still gets it.
        return out


def graphql(token, query, variables=None):
    body = {"query": query, "variables": variables or {}}
    data = gh(token, "api", "/graphql", "--input", "-", input_json=body)
    if data.get("errors"):
        raise GraphqlError(data["errors"][0]["message"])
    return data["data"]


def find_project(token, org, title):
    """The org project's node id, or None."""
    nodes = graphql(token, """
      query($org: String!) {
        organization(login: $org) {
          projectsV2(first: 100) { nodes { id title } }
        }
      }""", {"org": org})["organization"]["projectsV2"]["nodes"]
    for node in nodes:
        if node["title"] == title:
            return node["id"]
    return None


def project_single_select(token, project_id, field_name):
    """(field_id, {option name: option id}) for a single-select field."""
    nodes = graphql(token, """
      query($project: ID!) {
        node(id: $project) {
          ... on ProjectV2 {
            fields(first: 50) {
              nodes {
                ... on ProjectV2SingleSelectField {
                  id name options { id name }
                }
              }
            }
          }
        }
      }""", {"project": project_id})["node"]["fields"]["nodes"]
    for node in nodes:
        if node and node.get("name") == field_name:
            return node["id"], {o["name"]: o["id"] for o in node["options"]}
    return None, {}


def add_to_project(token, project_id, content_node_id):
    """Add an issue to the project; returns the project item id."""
    return graphql(token, """
      mutation($project: ID!, $content: ID!) {
        addProjectV2ItemById(
          input: {projectId: $project, contentId: $content}
        ) { item { id } }
      }""", {"project": project_id, "content": content_node_id}
    )["addProjectV2ItemById"]["item"]["id"]


def set_item_option(token, project_id, item_id, field_id, option_id):
    graphql(token, """
      mutation($project: ID!, $item: ID!, $field: ID!, $option: String!) {
        updateProjectV2ItemFieldValue(input: {
          projectId: $project, itemId: $item, fieldId: $field,
          value: {singleSelectOptionId: $option}
        }) { projectV2Item { id } }
      }""", {"project": project_id, "item": item_id,
             "field": field_id, "option": option_id})


def set_select_default(token, project_id, item_id, field_name, choice=None):
    """Set a single-select field, defaulting to its FIRST option.

    The first option is the org's default (setup seeds Team from --team
    order and Quarter from the current quarter forward). Returns the
    chosen option name, or None when the field does not exist or the
    named choice is unknown.
    """
    try:
        field_id, options = project_single_select(token, project_id,
                                                  field_name)
    except Exception:
        return None
    if not options:
        return None
    if choice and choice not in options:
        return None
    name = choice or next(iter(options))
    set_item_option(token, project_id, item_id, field_id, options[name])
    return name


def ensure_milestone(token, org, repo, title, due_on=None):
    """The milestone's number, created open if missing.

    A due date makes the milestone visible on the roadmap; pass due_on as
    YYYY-MM-DD to set it at creation, or to add it to an existing
    milestone that has none. Dates default aggressively — a new
    milestone with no due_on is due TODAY; an agent that judges the
    work bigger overrides with a later date and a stated reason.
    """
    due = {"due_on": f"{due_on}T23:59:59Z"} if due_on else {}
    for ms in gh(token, "api", f"/repos/{org}/{repo}/milestones?state=all",
                 "--paginate"):
        if ms["title"] == title:
            if due and not ms.get("due_on"):
                gh(token, "api", "-X", "PATCH",
                   f"/repos/{org}/{repo}/milestones/{ms['number']}",
                   "--input", "-", input_json=due)
            return ms["number"]
    if not due:
        due = {"due_on": datetime.date.today().isoformat() + "T23:59:59Z"}
    return gh(token, "api", f"/repos/{org}/{repo}/milestones", "--input", "-",
              input_json={"title": title, **due})["number"]


def project_iterations(token, project_id, field_name="Iteration"):
    """(field_id, {iteration title: iteration id}) for an iteration field."""
    nodes = graphql(token, """
      query($project: ID!) {
        node(id: $project) {
          ... on ProjectV2 {
            fields(first: 50) {
              nodes {
                ... on ProjectV2IterationField {
                  id name
                  configuration { iterations { id title } }
                }
              }
            }
          }
        }
      }""", {"project": project_id})["node"]["fields"]["nodes"]
    for node in nodes:
        if node and node.get("name") == field_name:
            its = node["configuration"]["iterations"]
            return node["id"], {i["title"]: i["id"] for i in its}
    return None, {}


def project_date_field(token, project_id, field_name):
    """The field id of a DATE field, or None."""
    nodes = graphql(token, """
      query($project: ID!) {
        node(id: $project) {
          ... on ProjectV2 {
            fields(first: 50) {
              nodes { ... on ProjectV2FieldCommon { id name dataType } }
            }
          }
        }
      }""", {"project": project_id})["node"]["fields"]["nodes"]
    for node in nodes:
        if node and node.get("name") == field_name \
                and node.get("dataType") == "DATE":
            return node["id"]
    return None


def set_item_value(token, project_id, item_id, field_id, value):
    """Set a project item field: {"date": ...}, {"iterationId": ...}, or
    {"singleSelectOptionId": ...}."""
    graphql(token, """
      mutation($project: ID!, $item: ID!, $field: ID!,
               $value: ProjectV2FieldValue!) {
        updateProjectV2ItemFieldValue(input: {
          projectId: $project, itemId: $item, fieldId: $field, value: $value
        }) { projectV2Item { id } }
      }""", {"project": project_id, "item": item_id,
             "field": field_id, "value": value})
