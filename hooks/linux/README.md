# Linux / containers notes

Same as macOS: `scripts/install.py` bakes the exact `python3` interpreter it's run with (`sys.executable`) into the hook commands, as an absolute path in `args`-exec form. No shell involved, so there's nothing Linux-specific to configure for the hooks in `hooks/common/`.

In a minimal container image, make sure `python3` is actually installed before running the installer — there's no fallback interpreter baked in.

If you add a hook that genuinely needs Linux-specific behavior, put the Python script here — `install.py` only looks in `hooks/common/` right now, so wire this directory into the installer if you need it.
