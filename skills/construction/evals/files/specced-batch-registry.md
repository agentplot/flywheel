# Proposals — bolt `widget-gateway`

| proposal | repo | change id | review | status | branch | owner |
|---|---|---|---|---|---|---|
| the widget gateway endpoint | atlas-kit | `widget-gateway-endpoint` | agent | specced | - | - |
| the registry client | atlas-kit | `widget-registry-client` | agent | specced | - | - |
| the scout's config schema | cortex-kit | `widget-scout-config` | human | specced | - | - |
| the scout runner | cortex-kit | `widget-scout-runner` | agent | specced | - | - |
| the telemetry emitter | atlas-kit | `widget-telemetry-emit` | agent | specced | - | - |

Notes carried on the rows:

- `widget-scout-config` and `widget-scout-runner` both name the scout's
  configuration keys; the runner's tasks were written first.
- `widget-telemetry-emit` writes two files that do not exist yet
  (`packages/telemetry/src/emit.ts`, `packages/telemetry/src/schema.ts`).
  Every other proposal edits files already in the repo.
- All five cite `decisions/gateway-retry-policy.md`; only the endpoint
  proposal restates the policy in its own tasks.
- `widget-scout-config` carries `human` because its apply agent asked for
  the operator's eyes on the key names, with the reason recorded on its
  task line.
