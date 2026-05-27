from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_report(path: str | Path) -> dict[str, Any]:
    report_path = Path(path)
    if report_path.suffix.lower() != ".json":
        raise ValueError("Network IT Troubleshooter v0.1 imports JSON reports only.")
    return json.loads(report_path.read_text(encoding="utf-8"))
