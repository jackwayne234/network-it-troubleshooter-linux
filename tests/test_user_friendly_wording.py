from pathlib import Path

from network_it_troubleshooter.engine import analyze_report
from network_it_troubleshooter.report_loader import load_report


SAMPLES = Path(__file__).resolve().parents[1] / "sample_reports"


def test_healthy_wording_is_clear_without_overpromising():
    analysis = analyze_report(load_report(SAMPLES / "healthy.json"))

    assert "basic network checks passed" in analysis.why
    assert "from this report" in analysis.why
    assert "not working" in analysis.next_step


def test_dns_wording_is_plain_english_and_actionable():
    analysis = analyze_report(load_report(SAMPLES / "dns-problem.json"))

    assert "website names" in analysis.why
    assert "internet addresses" in analysis.why
    assert "VPN" in analysis.next_step
    assert "Restart" in analysis.next_step
    assert "contact your ISP/IT" in analysis.next_step


def test_gateway_wording_mentions_router_connection_first():
    analysis = analyze_report(load_report(SAMPLES / "gateway-router-problem.json"))

    assert "network information" in analysis.why
    assert "router/gateway" in analysis.why
    assert "Check Wi-Fi/Ethernet first" in analysis.next_step
    assert "router power" in analysis.next_step
    assert "another device can use the same network" in analysis.next_step


def test_internet_isp_wording_separates_home_network_from_isp():
    analysis = analyze_report(load_report(SAMPLES / "internet-isp-problem.json"))

    assert "router may be working" in analysis.why
    assert "internet beyond your router" in analysis.why
    assert "another device" in analysis.next_step
    assert "also has no internet" in analysis.next_step
    assert "ISP" in analysis.next_step


def test_web_https_wording_mentions_site_or_browser_style_problem():
    analysis = analyze_report(load_report(SAMPLES / "web-https-problem.json"))

    assert "DNS worked" in analysis.why
    assert "website name was found" in analysis.why
    assert "web connection still failed" in analysis.why
    assert "different website or browser" in analysis.next_step
    assert "sign-in page/captive portal" in analysis.next_step
    assert "problem with the website itself" in analysis.next_step


def test_unknown_wording_says_mixed_or_incomplete_results():
    analysis = analyze_report(load_report(SAMPLES / "unknown-mixed-issue.json"))

    assert "mixed or incomplete results" in analysis.why
    assert "one clear cause" in analysis.why
    assert "Open the report details" in analysis.next_step
    assert "warnings, skipped checks, or failed checks" in analysis.next_step
    assert "Network Diagnostics Report Tool" in analysis.next_step
