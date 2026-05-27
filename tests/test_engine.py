from network_it_troubleshooter.engine import analyze_report


def report(overall=None, results=None):
    return {
        "schema_version": "1.0",
        "app": "Network Diagnostics Report Tool",
        "diagnostic_run": {"report_kind": "network_diagnostics", "platform": "linux"},
        "overall": overall,
        "results": results or [],
    }


def result(name, status, summary=""):
    return {"name": name, "status": status, "summary": summary, "details": {}}


def test_healthy_report_uses_healthy_flow():
    analysis = analyze_report(report(overall={"status": "healthy", "likely_problem_area": None}))

    assert analysis.likely_problem == "No obvious network problem found"
    assert analysis.flow_used == "Healthy Flow"
    assert "specific website" in analysis.next_step


def test_dns_problem_uses_dns_flow_from_overall():
    analysis = analyze_report(report(overall={"status": "problem_detected", "likely_problem_area": "dns"}))

    assert analysis.likely_problem == "DNS problem"
    assert analysis.flow_used == "DNS Problem Flow"
    assert "DNS" in analysis.why


def test_gateway_problem_uses_gateway_flow_from_overall():
    analysis = analyze_report(report(overall={"status": "problem_detected", "likely_problem_area": "gateway_or_local_network"}))

    assert analysis.likely_problem == "Gateway/router problem"
    assert analysis.flow_used == "Gateway/Router Problem Flow"


def test_internet_problem_uses_isp_flow_from_overall():
    analysis = analyze_report(report(overall={"status": "problem_detected", "likely_problem_area": "internet_or_isp"}))

    assert analysis.likely_problem == "Internet/ISP problem"
    assert analysis.flow_used == "Internet/ISP Problem Flow"


def test_falls_back_to_results_when_overall_missing():
    analysis = analyze_report(
        report(
            results=[
                result("Interfaces", "pass"),
                result("Routes", "pass"),
                result("Ping 1.1.1.1", "pass"),
                result("DNS lookup example.com", "fail"),
            ]
        )
    )

    assert analysis.likely_problem == "DNS problem"
    assert analysis.flow_used == "DNS Problem Flow"


def test_it_summary_is_copyable_plain_text():
    analysis = analyze_report(report(overall={"status": "problem_detected", "likely_problem_area": "dns"}))

    assert "Likely problem: DNS problem" in analysis.it_summary
    assert "Flow used: DNS Problem Flow" in analysis.it_summary
    assert "Next step:" in analysis.it_summary
