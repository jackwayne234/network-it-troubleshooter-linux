from pathlib import Path

import pytest

from network_it_troubleshooter.engine import analyze_report
from network_it_troubleshooter.report_loader import load_report


SAMPLES = Path(__file__).resolve().parents[1] / "sample_reports"


@pytest.mark.parametrize(
    ("filename", "expected_problem", "expected_flow"),
    [
        ("healthy.json", "No obvious network problem found", "Healthy Flow"),
        ("dns-problem.json", "DNS problem", "DNS Problem Flow"),
        ("gateway-router-problem.json", "Gateway/router problem", "Gateway/Router Problem Flow"),
        ("internet-isp-problem.json", "Internet/ISP problem", "Internet/ISP Problem Flow"),
        ("web-https-problem.json", "Web/HTTPS problem", "Web/HTTPS Problem Flow"),
        ("unknown-mixed-issue.json", "Unknown or mixed network issue", "Unknown/Mixed Issue Flow"),
    ],
)
def test_sample_reports_map_to_expected_flows(filename, expected_problem, expected_flow):
    report = load_report(SAMPLES / filename)
    analysis = analyze_report(report)

    assert analysis.likely_problem == expected_problem
    assert analysis.flow_used == expected_flow
    assert analysis.next_step
    assert analysis.it_summary
