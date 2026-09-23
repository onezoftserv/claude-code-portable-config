# macOS notes

Same as Linux: `scripts/install.py` bakes the exact `python3` interpreter it's run with (`sys.executable`) into the hook commands, as an absolute path in `args`-exec form. No shell involved, so there's nothing macOS-specific to configure for the hooks in `hooks/common/`.

If you add a hook that genuinely needs macOS-specific behavior (`osascript`, notifications, Keychain access), put the Python script here — `install.py` only looks in `hooks/common/` right now, so wire this directory into the installer if you need it.
