# inbox/2026-08-06-dispatch-retry-timeout.md

From: dispatch

The gateway's retry timeout is 30s and should be 5s — it's one constant in
`packages/gateway/src/config.ts` in atlas-kit. The widget gateway proposal
in your bolt already touches that file. One line.
