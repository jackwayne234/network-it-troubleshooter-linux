import json

import pytest

from network_it_troubleshooter.report_loader import load_report


def test_load_report_reads_json_file(tmp_path):
    path = tmp_path / "report.json"
    path.write_text('{"schema_version": "1.0", "results": []}', encoding="utf-8")

    loaded = load_report(path)

    assert loaded["schema_version"] == "1.0"


def test_load_report_rejects_non_json_suffix(tmp_path):
    path = tmp_path / "report.md"
    path.write_text("# report", encoding="utf-8")

    with pytest.raises(ValueError, match="JSON"):
        load_report(path)


def test_load_report_rejects_invalid_json(tmp_path):
    path = tmp_path / "report.json"
    path.write_text("not json", encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        load_report(path)
