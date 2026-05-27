from pathlib import Path

from network_it_troubleshooter.engine import analyze_report
from network_it_troubleshooter.report_loader import load_report


SAMPLES = Path(__file__).resolve().parents[1] / "sample_reports"


def test_dns_flow_has_reviewable_step_by_step_flowchart():
    analysis = analyze_report(load_report(SAMPLES / "dns-problem.json"))

    assert analysis.flow_used == "DNS Problem Flow"
    assert analysis.flow_steps == [
        "Confirm the computer has a local IP address.",
        "Confirm a default router/gateway exists.",
        "Confirm the router/gateway is reachable.",
        "Confirm public internet by IP works.",
        "Check DNS name lookup.",
        "If DNS lookup fails while earlier checks pass, treat this as a DNS problem.",
        "Try VPN off, router restart, DNS settings, then ISP/IT support if still failing.",
    ]


def test_dns_it_summary_includes_flow_steps():
    analysis = analyze_report(load_report(SAMPLES / "dns-problem.json"))

    assert "Troubleshooting flow:" in analysis.it_summary
    assert "1. Confirm the computer has a local IP address." in analysis.it_summary
    assert "7. Try VPN off" in analysis.it_summary
