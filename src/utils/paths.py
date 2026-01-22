from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path


APP_NAME = "SistemaContratos"


def project_root() -> Path:
    """
    Base directory of the project when running from source.
    This file lives in src/utils/paths.py -> parents[2] == project root.
    """
    return Path(__file__).resolve().parents[2]


def runtime_base_dir() -> Path:
    """
    Base directory to resolve packaged resources.
    - PyInstaller onefile: sys._MEIPASS points to extracted temp dir.
    - PyInstaller onedir: use folder containing the executable.
    - From source: use project root.
    """
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return project_root()


def resource_path(*parts: str) -> Path:
    """Absolute path to a bundled resource (read-only)."""
    return runtime_base_dir().joinpath(*parts)


def user_data_dir(app_name: str = APP_NAME) -> Path:
    """
    Writable data directory for the app (recommended for DB/model).
    Windows: %LOCALAPPDATA%\\{app_name}
    """
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA")
        if not base:
            base = str(Path.home())
        p = Path(base) / app_name
    else:
        p = Path.home() / f".{app_name}"
    p.mkdir(parents=True, exist_ok=True)
    return p


def ensure_user_file(resource_rel_path: str, dest_filename: str, app_name: str = APP_NAME) -> Path:
    """
    Ensure a file exists in user_data_dir by copying it from packaged resources
    the first time. Returns the destination path.
    """
    dest = user_data_dir(app_name) / dest_filename
    if dest.exists():
        return dest

    src = resource_path(*resource_rel_path.split("/"))
    if src.exists():
        shutil.copy2(src, dest)
    return dest


