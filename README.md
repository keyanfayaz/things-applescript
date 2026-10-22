# Things AppleScript

A small, local, read-only Things 3 adapter plus the recovered original scan.
Reads use native AppleScript and public properties. Python validates a strict
field allowlist before emitting JSON. No third-party dependencies or installation.

For another Mac, follow the [repeatable setup guide](docs/SETUP.md), starting with
the task-free `--doctor` check. Read the [capability and security contract](docs/CONTRACT.md)
before integration. This is a local CLI, not an installed MCP server or Dot tool.

## Setup and use

Requirements: macOS, Python 3.10+, and Things 3 installed at
`/Applications/Things3.app`. Run from an interactive Mac session that can resolve
the app. Open Things yourself before reading. The executing process must already
have appropriate Apple Events access; this adapter does not grant access, change
security settings, or retry a denial. macOS may present its own Automation prompt
on a first read; stop if access is unavailable.

```sh
python3 things_readonly.py --help
python3 things_readonly.py --doctor
python3 things_readonly.py --list inbox --limit 10
python3 things_readonly.py --list today --offset 10 --limit 10
python3 things_readonly.py --projects --limit 10
python3 things_readonly.py --project PROJECT_ID --limit 10
```

Each command makes one bounded read. `--projects` returns open project summaries;
`--project` returns open items in one open project. Only Inbox and Today are
accepted list targets. No arguments means usage help and an error, never a scan.
Limits are 1–50 (default 30); offsets are zero-based, 0–1,000,000. Follow
`next_offset` while `has_more` is true if more pages are wanted. Pagination is
explicit; there is no automatic crawl.

`--config .things-readonly.ini` explicitly loads optional machine-local settings.
The [example](config.example.ini) supplies a default page limit and optional
installed-version comparison. `--limit` overrides the configured default.
Configuration cannot add commands, change the fixed app path, or grant access.

Success: exit 0 and one validated JSON page on stdout. Failure: exit 1 and a
sanitized diagnostic on stderr, no page. Invalid arguments: exit 2. Nothing is
saved by the adapter. Titles, names and IDs are private even when notes are absent;
do not paste real output into commits, issues, fixtures, or CI logs.
`--doctor` instead emits a prerequisite report; exit 0 means those checks passed,
not that Apple Events access or live task reads work. Failed checks exit 1.

## Read and output allowlist

The active script reads only app `version`, list/project `id` and `name`, project
and item `status`, and item `id` and `name`. It requests open collections and their
counts. Item names become `title`. It does not request whole property records.

| Output location | Exact fields |
| --- | --- |
| Page | `schema_version`, `kind`, `container_id`, `container_name`, `app_version`, `offset`, `limit`, `total_count`, `returned_count`, `next_offset`, `has_more`, `items` |
| Each item | `id`, `title`, `status` |

`schema_version` is 1. Status is always `open`. `total_count` counts the eligible
open collection for that request; it is not a total across Things. Empty titles,
duplicate titles, Unicode and collection order are preserved. Duplicate IDs
within a page, unknown fields, closed statuses, and inconsistent pagination fail
validation and discard the output.

Excluded: notes, archived/completed/canceled item contents, private JSON,
checklists, headings, recurrence rules, attachments, database files, task edits,
UI commands and experimental reorder commands. There is no HTTP service, plugin,
agent tool registration, background worker, credential store, or persistent cache.

## Tests and compilation

```sh
python3 -m unittest discover -s tests -v
python3 -m py_compile things_readonly.py
# macOS with Things installed; compile only, no live read:
osacompile -o /tmp/things-readonly.scpt src/read.applescript
```

Tests use synthetic values and mocked process results, never a live Things app.
GitHub Actions runs these tests and Python compilation on Linux. It does not
compile AppleScript or test live Apple Events. Review [provenance](docs/PROVENANCE.md)
for the recovery boundary and [verification](docs/VERIFICATION.md) for observed checks.

## Known limits

- This is a newly hardened derivative of a recovered scan, not a recovered copy
  of the later metadata wrapper. See `historical/scan.applescript` for the original.
- The app path is fixed. App discovery and Apple Events may behave differently
  in a sandbox, remote session, or different process even when the app is open.
- Pages load the eligible collection before slicing. This limits emitted items,
  not Things' internal work, and is not server-side pagination.
- Item count is bounded; string lengths, subprocess output bytes and collection
  memory are not. This portability update does not close those resource gaps.
- Read-only behavior comes from the reviewed code, not an OS-enforced read-only
  permission. Runtime script integrity and app code signatures are not verified.
- Pages are not atomic snapshots. Changes between calls may skip or repeat IDs.
  Deduplicate IDs across pages and refresh a changing container. A status change
  detected during one read discards the page.
- List membership and project nesting follow the public scripting interface.
  No UI comparison or guarantee of recursive subtree coverage is provided.
- Reads preserve returned order and do not establish a priority or urgency score.
- Apple Events have a 60-second timeout; Python has a 65-second process deadline.
  Killing the reader does not guarantee cancellation inside Things. There is no
  retry, incremental sync, mutation API, or full inventory guarantee.
- `-10827` indicates app launch/discovery failure; `-1728` can indicate app or
  object resolution failure. Neither alone proves a permission denial.
  `-1742`/`-1743` stop as Apple Events access denials. Do not retry denied access
  or change security settings as part of using this repository.
