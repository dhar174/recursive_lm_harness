#!/usr/bin/env python3

from __future__ import annotations

import os
import subprocess
import stat
import sys
from pathlib import Path


def _is_safe_permissions(path: Path) -> bool:
    if os.name != "posix":
        return True
    mode = path.stat().st_mode
    return (mode & stat.S_IWGRP) == 0 and (mode & stat.S_IWOTH) == 0


def _has_safe_permissions_chain(path: Path, root: Path) -> bool:
    if os.name != "posix":
        return True

    current = path.resolve()
    root = root.resolve()
    while True:
        if not _is_safe_permissions(current):
            return False
        if current == root:
            return True
        if current.parent == current:
            return False
        current = current.parent


def _is_within_root(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _hook_environment() -> dict[str, str]:
    allowed_keys = {
        "HOME",
        "LANG",
        "LC_ALL",
        "LC_CTYPE",
        "VIRTUAL_ENV",
        "PATHEXT",
        "SYSTEMROOT",
        "TEMP",
        "TMP",
        "USER",
        "USERNAME",
        "USERPROFILE",
        "WINDIR",
    }
    env = {key: value for key, value in os.environ.items() if key in allowed_keys}
    path_value = os.environ.get("PATH")
    if path_value is not None:
        if os.name == "posix":
            safe_entries = []
            for entry in path_value.split(os.pathsep):
                if not entry:
                    continue
                entry_path = Path(entry)
                resolved_entry = entry_path.resolve()
                if resolved_entry.is_dir() and _has_safe_permissions_chain(
                    resolved_entry,
                    Path(resolved_entry.anchor),
                ):
                    safe_entries.append(str(resolved_entry))
            env["PATH"] = os.pathsep.join(safe_entries)
        else:
            env["PATH"] = path_value
    return env


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: run_mem0ry4ai_hook.py <pre_invocation|stop>", file=sys.stderr)
        return 2

    hook_name = sys.argv[1]
    if hook_name not in {"pre_invocation", "stop"}:
        print(f"unknown hook: {hook_name}", file=sys.stderr)
        return 2

    hook_path = Path.home() / "mem0ry4ai" / "hooks" / f"antigravity_{hook_name}.py"
    home = Path.home().resolve()
    resolved_hook_path = hook_path.resolve()

    if not resolved_hook_path.is_file():
        print(f"hook not found: {resolved_hook_path}", file=sys.stderr)
        return 1

    if not _is_within_root(resolved_hook_path, home):
        print(f"hook is outside the home directory: {resolved_hook_path}", file=sys.stderr)
        return 1

    if not _has_safe_permissions_chain(resolved_hook_path, home):
        print(f"insecure hook permissions: {resolved_hook_path}", file=sys.stderr)
        return 1

    completed = subprocess.run(
        [sys.executable, str(resolved_hook_path)],
        check=False,
        env=_hook_environment(),
    )
    if completed.returncode != 0:
        print(f"hook exited with status {completed.returncode}: {resolved_hook_path}", file=sys.stderr)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
