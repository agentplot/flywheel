# Proposals — bolt `widget-gateway`

| proposal | repo | change id | review | status | branch | owner |
|---|---|---|---|---|---|---|
| the widget gateway endpoint | atlas-kit | `widget-gateway-endpoint` | agent | in-review | `bolt/widget-gateway` | review-gateway |
| the registry client | atlas-kit | `widget-registry-client` | agent | approved | - | - |
| the scout's config schema | cortex-kit | `widget-scout-config` | agent | specced | - | - |

## Review history on `widget-gateway-endpoint`

- **Round 1** — bounced. The reviewer found the retry policy unspecified
  and the error taxonomy missing from the proposal's tasks. Row returned to
  `to-spec`; a spec agent fixed both.
- **Round 2** — bounced. The reviewer found that the retry wording added in
  the fix contradicts the batching wording added in the same fix, and that
  the new error taxonomy names a status code the endpoint section does not
  list. Neither defect existed before round 1's fixes.

The proposal's decision record is
`openspec/changes/widget-loop/decisions/gateway-retry-policy.md`, and it is
unchanged since the proposal was first written.
