# Capability and security contract

This describes the current local CLI. It is not a security certification, a
complete hardening milestone, an MCP server, an installed agent tool, or a
promise that a newly configured host can access Things.

| Capability | Current behavior |
| --- | --- |
| Task reads | Explicit Inbox/Today page, open-project catalog page, or one open project's open items |
| Output | Schema 1; exact page allowlist in README; item `id`, `title`, `status` only |
| Excluded fields | No notes, private JSON, attachments, checklists, headings or recurrence rules |
| Mutations | No active task writes, scheduling, moving, deleting, UI commands or reordering |
| Pagination | 1–50 emitted items; default 30 unless configured; zero-based offsets; no automatic crawl |
| Diagnostic | Disk metadata and NSWorkspace lookup; no task reads, launch, repair or permission probe |
| Configuration | Explicit INI file: default page limit and optional installed-version comparison only |
| Storage/network | No task export, credential store, network client, listener, daemon or persistent cache |
| Supported method | Public native Things AppleScript interface on macOS |

The interface method is documented by [Cultured Code](https://culturedcode.com/things/support/articles/4562654/).
That does not make this custom code vendor-maintained or endorsed. Built-in list
ID constants are historically discovered identifiers, not a promised vendor
compatibility contract. The fixed app path and session-dependent discovery remain
portability limits. Installed app metadata is not a live Apple Events permission test.

## Boundaries the code does provide

The active script makes explicit public-property reads and filters open items.
Python rejects unexpected fields and inconsistent pages before emitting JSON.
Arguments are passed directly to a fixed system executable without a shell or
interpolation into AppleScript code. Errors from script execution are sanitized;
there is no automatic retry. Apple Events have a 60-second timeout and the task
reader process a 65-second deadline. The task-free diagnostic has a separate
10-second subprocess deadline. The CLI saves no task data itself.

## Boundaries it does not provide

- macOS Automation access is not reduced to an enforced read-only capability by
  this code. A process able to modify the scripts or run arbitrary commands is
  outside this adapter's protection. App signatures and runtime script integrity
  are not verified. The optional version comparison is not identity attestation.
- Collections are loaded before slicing. String lengths, captured subprocess
  bytes and collection memory have no hard cap. The row limit does not make the
  total resource footprint bounded. These are known gaps left open by this update.
- Pages are not atomic snapshots; membership/order changes can skip or repeat
  items. Collection membership, including behavior of trashed projects, has not
  been live verified. No complete inventory or incremental-sync guarantee is made.
- Names and IDs remain private. Stdout may be retained or transmitted by a caller.
  Task text is untrusted data and must not become instructions to an agent.
  Git ignore rules do not prevent forced commits or external logging.
- The historical scan is a separate, broader artifact. Its unfiltered project
  metadata loop must not be treated as the active adapter's scope.
- Synthetic tests mock AppleScript results. They establish wrapper behavior,
  not an independent proof of live read-only Apple Events or working permissions.
  Live task access remains pending after the previously recorded `-10827` failure.
- CI uses version-tagged third-party actions; those tags are not immutable pins.

No Things Cloud protocol, cloud credentials, reverse-engineered remote API, or
remote access is implemented. Any future tool registration, stronger resource
bounds, process isolation, live verification, or additional integration needs its
own review and scope. Retaining this adapter does not authorize those next steps.
