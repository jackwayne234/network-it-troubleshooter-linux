from network_it_troubleshooter.work_package import (
    WorkPackageResult,
    dns_work_package_steps,
    gateway_router_work_package_steps,
    healthy_work_package_steps,
    internet_isp_work_package_steps,
    live_all_tests_steps,
    normalize_website_target,
    unknown_mixed_work_package_steps,
    parse_default_gateway,
    summarize_work_package,
    upsert_work_result,
    web_https_work_package_steps,
)


def assert_safe_no_shell(steps):
    for step in steps:
        assert isinstance(step.command, list)
        assert step.command
        assert "&&" not in step.command
        assert ";" not in step.command
        assert step.safe_read_only


def test_dns_work_package_has_safe_button_steps():
    steps = dns_work_package_steps()

    assert [step.label for step in steps] == [
        "Check local IP",
        "Check default gateway",
        "Ping router/gateway",
        "Ping public internet IP",
        "Test DNS lookup",
    ]
    assert_safe_no_shell(steps)


def test_healthy_work_package_has_safe_button_steps_for_still_broken_cases():
    steps = healthy_work_package_steps("https://status.example.org/outage")

    assert [step.label for step in steps] == [
        "Check local IP",
        "Check default gateway",
        "Ping router/gateway",
        "Ping public internet IP",
        "Test DNS lookup",
        "Check website HTTP status",
        "Check HTTPS/TLS connection",
    ]
    commands = {step.label: step.command for step in steps}
    assert commands["Test DNS lookup"] == ["getent", "hosts", "status.example.org"]
    assert commands["Check website HTTP status"] == ["curl", "-I", "--max-time", "8", "--location", "https://status.example.org"]
    assert commands["Check HTTPS/TLS connection"] == ["openssl", "s_client", "-connect", "status.example.org:443", "-servername", "status.example.org", "-brief"]
    assert_safe_no_shell(steps)


def test_healthy_flow_maps_to_work_package_steps():
    from network_it_troubleshooter.work_package import steps_for_flow

    steps = steps_for_flow("Healthy Flow", "status.example.org")

    assert steps[0].label == "Check local IP"
    assert steps[-1].command == ["openssl", "s_client", "-connect", "status.example.org:443", "-servername", "status.example.org", "-brief"]


def test_unknown_mixed_work_package_has_safe_broad_snapshot_steps():
    steps = unknown_mixed_work_package_steps("https://status.example.org/outage")

    assert [step.label for step in steps] == [
        "Check local IP",
        "Check default gateway",
        "Ping router/gateway",
        "Ping public internet IP",
        "Test DNS lookup",
        "Check website HTTP status",
        "Show route table",
    ]
    commands = {step.label: step.command for step in steps}
    assert commands["Test DNS lookup"] == ["getent", "hosts", "status.example.org"]
    assert commands["Check website HTTP status"] == ["curl", "-I", "--max-time", "8", "--location", "https://status.example.org"]
    assert_safe_no_shell(steps)


def test_unknown_mixed_flow_maps_to_work_package_steps():
    from network_it_troubleshooter.work_package import steps_for_flow

    steps = steps_for_flow("Unknown/Mixed Issue Flow", "status.example.org")

    assert steps[0].label == "Check local IP"
    assert steps[-1].label == "Show route table"


def test_live_all_tests_uses_safe_broad_snapshot_without_json_report():
    steps = live_all_tests_steps("https://status.example.org/outage")

    assert [step.label for step in steps] == [
        "Check local IP",
        "Check default gateway",
        "Ping router/gateway",
        "Ping public internet IP",
        "Test DNS lookup",
        "Check website HTTP status",
        "Show route table",
    ]
    assert steps[4].command == ["getent", "hosts", "status.example.org"]
    assert_safe_no_shell(steps)


def test_gateway_router_work_package_has_safe_button_steps():
    steps = gateway_router_work_package_steps()

    assert [step.label for step in steps] == [
        "Check local IP",
        "Check default gateway",
        "Ping router/gateway",
        "Show route table",
        "Check neighbor/ARP table",
    ]
    assert_safe_no_shell(steps)


def test_internet_isp_work_package_has_safe_button_steps():
    steps = internet_isp_work_package_steps()

    assert [step.label for step in steps] == [
        "Check local IP",
        "Check default gateway",
        "Ping router/gateway",
        "Ping public internet IP",
        "Trace route to public IP",
        "Test DNS lookup",
    ]
    assert_safe_no_shell(steps)


def test_web_https_work_package_has_safe_button_steps():
    steps = web_https_work_package_steps()

    assert [step.label for step in steps] == [
        "Test DNS lookup",
        "Ping public internet IP",
        "Check website HTTP status",
        "Check HTTPS/TLS connection",
        "Check TCP port 443",
        "Check TCP port 80",
    ]
    assert_safe_no_shell(steps)


def test_web_https_work_package_uses_user_website_target():
    steps = web_https_work_package_steps("https://status.example.org/outage?from=chat")
    commands = {step.label: step.command for step in steps}

    assert commands["Test DNS lookup"] == ["getent", "hosts", "status.example.org"]
    assert commands["Check website HTTP status"] == ["curl", "-I", "--max-time", "8", "--location", "https://status.example.org"]
    assert commands["Check HTTPS/TLS connection"] == ["openssl", "s_client", "-connect", "status.example.org:443", "-servername", "status.example.org", "-brief"]
    assert commands["Check TCP port 443"] == ["nc", "-vz", "-w", "5", "status.example.org", "443"]
    assert commands["Check TCP port 80"] == ["nc", "-vz", "-w", "5", "status.example.org", "80"]
    assert_safe_no_shell(steps)


def test_web_https_work_package_defaults_to_example_dot_com_for_blank_target():
    steps = web_https_work_package_steps("   ")

    assert steps[0].command == ["getent", "hosts", "example.com"]


def test_normalize_website_target_rejects_unsafe_target_text():
    assert normalize_website_target("example.com; rm -rf / && bad") == "example.com"


def test_parse_default_gateway_from_ip_route_output():
    output = "default via 192.168.0.1 dev enp4s0 proto dhcp src 192.168.0.70 metric 100\n"

    assert parse_default_gateway(output) == "192.168.0.1"


def test_parse_default_gateway_returns_none_when_missing():
    assert parse_default_gateway("192.168.0.0/24 dev enp4s0 proto kernel") is None


def test_summarize_all_dns_steps_passed():
    results = [WorkPackageResult(step.label, "pass", "This check passed.", "ok") for step in dns_work_package_steps()]

    summary = summarize_work_package("DNS Problem Flow", results)

    assert "All DNS troubleshooting checks passed" in summary
    assert "not happening right now" in summary
    assert "run a fresh Network Diagnostics Report Tool report" in summary


def test_summarize_all_healthy_steps_passed():
    results = [WorkPackageResult(step.label, "pass", "This check passed.", "ok") for step in healthy_work_package_steps()]

    summary = summarize_work_package("Healthy Flow", results)

    assert "All healthy/still-broken troubleshooting checks passed" in summary
    assert "basic network and website checks passed right now" in summary
    assert "try the app or website again" in summary


def test_summarize_healthy_steps_with_failures():
    results = [
        WorkPackageResult("Ping public internet IP", "pass", "This check passed.", "ok"),
        WorkPackageResult("Check website HTTP status", "fail", "This check failed.", "bad"),
    ]

    summary = summarize_work_package("Healthy Flow", results)

    assert "Some healthy/still-broken troubleshooting checks did not pass" in summary
    assert "Check website HTTP status" in summary
    assert "Focus on the failed or warning checks" in summary


def test_summarize_all_unknown_mixed_steps_passed():
    results = [WorkPackageResult(step.label, "pass", "This check passed.", "ok") for step in unknown_mixed_work_package_steps()]

    summary = summarize_work_package("Unknown/Mixed Issue Flow", results)

    assert "All unknown/mixed troubleshooting checks passed" in summary
    assert "No clear network failure is showing right now" in summary
    assert "copy these Work Package results" in summary


def test_summarize_unknown_mixed_steps_with_failures():
    results = [
        WorkPackageResult("Check local IP", "pass", "This check passed.", "ok"),
        WorkPackageResult("Test DNS lookup", "fail", "This check failed.", "bad"),
    ]

    summary = summarize_work_package("Unknown/Mixed Issue Flow", results)

    assert "Some unknown/mixed troubleshooting checks did not pass" in summary
    assert "Test DNS lookup" in summary
    assert "Focus on the failed or warning checks" in summary


def test_summarize_dns_steps_with_failures():
    results = [
        WorkPackageResult("Check local IP", "pass", "This check passed.", "ok"),
        WorkPackageResult("Test DNS lookup", "fail", "This check failed.", "bad"),
    ]

    summary = summarize_work_package("DNS Problem Flow", results)

    assert "Some DNS troubleshooting checks did not pass" in summary
    assert "Test DNS lookup" in summary
    assert "Focus on the failed or warning checks" in summary


def test_summarize_all_gateway_router_steps_passed():
    results = [WorkPackageResult(step.label, "pass", "This check passed.", "ok") for step in gateway_router_work_package_steps()]

    summary = summarize_work_package("Gateway/Router Problem Flow", results)

    assert "All gateway/router troubleshooting checks passed" in summary
    assert "not happening right now" in summary
    assert "run a fresh Network Diagnostics Report Tool report" in summary


def test_summarize_gateway_router_steps_with_failures():
    results = [
        WorkPackageResult("Check local IP", "pass", "This check passed.", "ok"),
        WorkPackageResult("Ping router/gateway", "fail", "This check failed.", "bad"),
    ]

    summary = summarize_work_package("Gateway/Router Problem Flow", results)

    assert "Some gateway/router troubleshooting checks did not pass" in summary
    assert "Ping router/gateway" in summary
    assert "Focus on the failed or warning checks" in summary


def test_summarize_all_internet_isp_steps_passed():
    results = [WorkPackageResult(step.label, "pass", "This check passed.", "ok") for step in internet_isp_work_package_steps()]

    summary = summarize_work_package("Internet/ISP Problem Flow", results)

    assert "All internet/ISP troubleshooting checks passed" in summary
    assert "not happening right now" in summary
    assert "run a fresh Network Diagnostics Report Tool report" in summary


def test_summarize_internet_isp_steps_with_failures():
    results = [
        WorkPackageResult("Ping router/gateway", "pass", "This check passed.", "ok"),
        WorkPackageResult("Ping public internet IP", "fail", "This check failed.", "bad"),
    ]

    summary = summarize_work_package("Internet/ISP Problem Flow", results)

    assert "Some internet/ISP troubleshooting checks did not pass" in summary
    assert "Ping public internet IP" in summary
    assert "Focus on the failed or warning checks" in summary


def test_summarize_all_web_https_steps_passed():
    results = [WorkPackageResult(step.label, "pass", "This check passed.", "ok") for step in web_https_work_package_steps()]

    summary = summarize_work_package("Web/HTTPS Problem Flow", results)

    assert "All web/HTTPS troubleshooting checks passed" in summary
    assert "not happening right now" in summary
    assert "run a fresh Network Diagnostics Report Tool report" in summary


def test_summarize_web_https_steps_with_failures():
    results = [
        WorkPackageResult("Test DNS lookup", "pass", "This check passed.", "ok"),
        WorkPackageResult("Check website HTTP status", "fail", "This check failed.", "bad"),
    ]

    summary = summarize_work_package("Web/HTTPS Problem Flow", results)

    assert "Some web/HTTPS troubleshooting checks did not pass" in summary
    assert "Check website HTTP status" in summary
    assert "Focus on the failed or warning checks" in summary


def test_summarize_no_work_package_results_yet():
    summary = summarize_work_package("DNS Problem Flow", [])

    assert "No Work Package checks have been run yet" in summary


def test_text_from_timeout_parts_handles_bytes_and_strings():
    from network_it_troubleshooter.work_package import text_from_timeout_parts

    assert text_from_timeout_parts(b"hello", " world") == "hello world"


def test_timeout_summary_for_trace_route_with_partial_output_is_not_scary():
    from network_it_troubleshooter.work_package import timeout_summary

    summary = timeout_summary("Trace route to public IP", "1: router\n2: isp\n")

    assert "did not fully finish" in summary
    assert "reached several network hops" in summary
    assert "can happen normally" in summary


def test_tls_output_with_successful_handshake_is_pass():
    from network_it_troubleshooter.work_package import status_from_completed_command

    status, summary = status_from_completed_command(
        "Check HTTPS/TLS connection",
        0,
        "CONNECTION ESTABLISHED\nVerification: OK\n",
    )

    assert status == "pass"
    assert "TLS connection succeeded" in summary


def test_tls_timeout_with_successful_handshake_is_warning_not_failure():
    from network_it_troubleshooter.work_package import timeout_summary

    summary = timeout_summary("Check HTTPS/TLS connection", "CONNECTION ESTABLISHED\nVerification: OK\n")

    assert "TLS connection succeeded" in summary
    assert "kept the connection open" in summary


def test_upsert_work_result_replaces_prior_result_with_same_label():
    old = WorkPackageResult("Test DNS lookup", "fail", "old", "bad")
    new = WorkPackageResult("Test DNS lookup", "pass", "new", "ok")

    results = upsert_work_result([old], new)

    assert results == [new]


def test_upsert_work_result_preserves_other_steps():
    first = WorkPackageResult("Check local IP", "pass", "ok", "out")
    second = WorkPackageResult("Test DNS lookup", "pass", "ok", "out")

    results = upsert_work_result([first], second)

    assert results == [first, second]
