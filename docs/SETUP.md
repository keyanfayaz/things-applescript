# Moving to another Mac

The intended goal is a repeatable, local adapter that can later sit behind a
narrow tool interface. Moving an agent to a different host does not move the
checkout, Things installation, task store, or that host's Automation access.
Nothing here installs or configures another computer automatically.

## Repeatable procedure

1. On the intended Mac, obtain a reviewed checkout of this repository. For
   example, with existing GitHub access:

   ```sh
   git clone https://github.com/keyanfayaz/things-applescript.git
   cd things-applescript
   git rev-parse HEAD
   python3 --version
   python3 -B -m unittest discover -s tests -v
   python3 -B things_readonly.py --doctor
   ```

2. Requirements are Python 3.10+, macOS, system `/usr/bin/osascript`, and Things 3
   at `/Applications/Things3.app`. The active reader's app path remains fixed.
   Do not copy a task database, credentials, private exports, or old machine
   configuration into this repository. No pip dependencies are required.

3. Optionally create a local settings file yourself:

   ```sh
   cp config.example.ini .things-readonly.ini
   python3 -B things_readonly.py --config .things-readonly.ini --doctor
   ```

   Edit `default_limit` within 1–50 if wanted. Optionally set
   `expected_app_version` to the installed version shown by the diagnostic.
   Empty means no version comparison. The version check does not verify an app
   signature. Local settings are ignored by Git; no file is automatically created,
   no home-directory config is searched, and no secrets or paths belong here.
   The example contains only generic defaults. An explicit `--limit` takes priority.

4. Review the diagnostic. It reads the bundle's Info.plist and uses NSWorkspace
   metadata lookup for registration and visible running-instance count. Version
   means the installed bundle version, not a response from a running Things app.
   No Apple Events are sent to Things, no task collections are accessed, and the
   command does not launch, register, repair, or reset anything. It may start the
   system `osascript` interpreter for a JXA/AppKit lookup, with a 10-second deadline.

5. A failed prerequisite check exits 1. Unsupported OS, missing executable/app,
   app-discovery failure, malformed settings, and a configured version mismatch
   fail clearly. There are no retries or permission-repair commands. If access is
   denied, stop; do not reset permissions or change security settings through this
   workflow. A registration failure can depend on the execution session and does
   not establish that Things is absent or closed on the user's desktop.

6. A successful diagnostic leaves `apple_events_access` and `live_task_reads`
   explicitly `not_probed`. Open Things yourself in the intended interactive
   session. Only when a narrow task read is separately wanted and existing access
   permits it, use:

   ```sh
   python3 -B things_readonly.py --config .things-readonly.ini --list inbox --limit 1
   ```

   This last command **does return private task data**. It is not part of the
   diagnostic. Do not run it in CI, persist its output in the repository, or treat
   the setup guide as permission to extract tasks from another computer.

Keep the checkout commit and generic setup instructions portable. Keep actual
task data, host-specific access, and private settings on the intended machine.
