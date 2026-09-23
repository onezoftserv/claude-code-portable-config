# Windows notes

`scripts/install.py` bakes the exact Python interpreter it's run with (`sys.executable`) into the hook commands in `settings.json`, as an absolute path in `args`-exec form (no shell involved). That sidesteps the usual Windows headaches:

- `python` vs `python3` vs `py` — not relevant, the installer uses the interpreter it's already running under.
- The Microsoft Store Python stub — avoided, since `sys.executable` is a real absolute path, not a PATH lookup of a bare name.
- Shell quoting differences (cmd.exe vs PowerShell vs bash) — avoided, since exec-form `args` never goes through a shell.

Run `scripts\install.py` with whichever Python you actually use day to day on this machine (a venv's `python.exe` is fine — that's the one that gets baked in).

If you add a hook that genuinely needs Windows-specific behavior (clipboard, notifications, path separators), put the Python script here and register it the same way — `install.py` only looks in `hooks/common/` right now, so wire a new OS-specific directory into the installer if you need one.
