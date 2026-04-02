#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import os
import shlex
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
VENV_DIR = ROOT / ".venv"
REQUIREMENTS_FILE = ROOT / "requirements.txt"
APP_FILE = ROOT / "app.py"
STAMP_FILE = VENV_DIR / ".requirements.sha256"
MIN_PYTHON = (3, 12)


def venv_python() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(cmd: list[str]) -> None:
    print(f"$ {shlex.join(cmd)}")
    subprocess.run(cmd, cwd=ROOT, check=True)


def needs_dependency_install(python_bin: Path) -> bool:
    expected_hash = file_sha256(REQUIREMENTS_FILE)
    if not STAMP_FILE.exists() or STAMP_FILE.read_text().strip() != expected_hash:
        return True

    check = subprocess.run(
        [str(python_bin), "-c", "import pandas, streamlit"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    return check.returncode != 0


def ensure_virtualenv() -> Path:
    python_bin = venv_python()
    if not python_bin.exists():
        run([sys.executable, "-m", "venv", str(VENV_DIR)])
    return python_bin


def ensure_dependencies(python_bin: Path) -> None:
    if not needs_dependency_install(python_bin):
        return

    run([str(python_bin), "-m", "pip", "install", "--upgrade", "pip"])
    run([str(python_bin), "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)])
    STAMP_FILE.write_text(f"{file_sha256(REQUIREMENTS_FILE)}\n")


def main() -> int:
    if sys.version_info < MIN_PYTHON:
        version = ".".join(map(str, MIN_PYTHON))
        print(
            f"This project requires Python {version}+ to bootstrap the local virtualenv.",
            file=sys.stderr,
        )
        print(
            "Run this launcher with a Python 3.12+ interpreter, for example "
            "`python3.12 run_app.py` or `py -3.12 run_app.py`.",
            file=sys.stderr,
        )
        return 1

    if not APP_FILE.exists():
        print(f"Could not find app file: {APP_FILE}", file=sys.stderr)
        return 1

    python_bin = ensure_virtualenv()
    ensure_dependencies(python_bin)

    cmd = [str(python_bin), "-m", "streamlit", "run", str(APP_FILE), *sys.argv[1:]]
    return subprocess.run(cmd, cwd=ROOT).returncode


if __name__ == "__main__":
    raise SystemExit(main())
