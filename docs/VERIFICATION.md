# Verification — 2026-10-18

| Check | Observed result |
| --- | --- |
| Historical file survival | Original temporary directory absent; scan recovered from supported task output |
| Recovered scan SHA-256 | `eb5e227974f60545454a0c1a7f55039629a6fab2ecd6d38337577bcdf76daaa3` (normalized text) |
| Synthetic tests | 9 tests passed with mocked subprocess results; no live data fixtures |
| Python compilation | Passed with `python3 -m py_compile things_readonly.py` |
| Active AppleScript compilation | Passed with macOS `osacompile`; no live read needed |
| Single live probe | One Inbox request with limit 1 failed with `-10827` (app launch/discovery); no retry |
| Live record output | None persisted, logged, or committed |
| Live project / Today / catalog reads | Not run |
| Notes, archive, writes, permissions changes | Not requested or performed |

The live failure leaves current end-to-end Apple Events access **unverified**.
It does not establish a permission denial. A successful compile and synthetic
tests establish syntax and the wrapper contract, not successful Things reads.
Any future live verification belongs in a functioning interactive Mac session
with existing access; do not retry a denied permission or change security settings.

Repository publication and GitHub checks must be verified against the actual
remote commit. Their final result is reported separately so this document does
not imply a successful push or CI run before it happens.

## Portability update — 2026-10-18

- 19 synthetic tests passed, including strict machine-local configuration,
  default/CLI precedence, bundle-version comparison, diagnostic success/failure,
  sanitized errors, and the absence of task-reader calls from `--doctor`.
- A task-free macOS diagnostic found valid app metadata and system prerequisites,
  but failed the NSWorkspace app-registration check. Apple Events access and
  task reads remained `not_probed`. No retry or repair was attempted.
- The active task AppleScript and historical scan were unchanged by this update.
- No live task extraction, other-host setup, credential changes, daemon, cloud
  protocol, permission reset, or new security-hardening claim was introduced.
- Output byte/string limits, collection-memory limits and live verification
  remain open as documented in the capability and security contract.

## Independent source snapshot — 2026-10-22

The publication snapshot excludes private execution identifiers and task output.
Synthetic tests can be repeated without Things or Automation access. No live task
read, permission repair, other-host installation, or complete-security claim is
part of this publication. Existing resource and live-verification limits remain.
