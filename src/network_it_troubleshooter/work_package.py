from __future__ import annotations

from dataclasses import dataclass
import re
import shutil
import subprocess
from urllib.parse import urlparse


@dataclass(frozen=True)
class WorkPackageStep:
    label: str
    plain_english: str
    command: list[str]
    safe_read_only: bool = True


@dataclass(frozen=True)
class WorkPackageResult:
    label: str
    status: str
    summary: str
    output: str


def healthy_work_package_steps(target: str | None = None) -> list[WorkPackageStep]:
    website = normalize_website_target(target)
    https_url = f"https://{website}"
    return [
        WorkPackageStep("Check local IP", "Checks whether this computer has a local network address.", ["ip", "-4", "addr", "show"]),
        WorkPackageStep("Check default gateway", "Checks whether the computer has a default router/gateway.", ["ip", "route", "show", "default"]),
        WorkPackageStep("Ping router/gateway", "Checks whether the current router/gateway responds.", ["ping", "-c", "3", "-W", "2", "<gateway>"]),
        WorkPackageStep("Ping public internet IP", "Checks whether public internet works by IP.", ["ping", "-c", "3", "-W", "2", "1.1.1.1"]),
        WorkPackageStep("Test DNS lookup", "Checks whether the specific website name resolves.", ["getent", "hosts", website]),
        WorkPackageStep("Check website HTTP status", "Checks whether the specific website responds over HTTPS.", ["curl", "-I", "--max-time", "8", "--location", https_url]),
        WorkPackageStep("Check HTTPS/TLS connection", "Checks whether a TLS connection can be made to the specific website.", ["openssl", "s_client", "-connect", f"{website}:443", "-servername", website, "-brief"]),
    ]


def unknown_mixed_work_package_steps(target: str | None = None) -> list[WorkPackageStep]:
    website = normalize_website_target(target)
    https_url = f"https://{website}"
    return [
        WorkPackageStep("Check local IP", "Checks whether this computer has a local network address.", ["ip", "-4", "addr", "show"]),
        WorkPackageStep("Check default gateway", "Checks whether the computer has a default router/gateway.", ["ip", "route", "show", "default"]),
        WorkPackageStep("Ping router/gateway", "Checks whether the current router/gateway responds.", ["ping", "-c", "3", "-W", "2", "<gateway>"]),
        WorkPackageStep("Ping public internet IP", "Checks whether public internet works by IP.", ["ping", "-c", "3", "-W", "2", "1.1.1.1"]),
        WorkPackageStep("Test DNS lookup", "Checks whether the specific website name resolves.", ["getent", "hosts", website]),
        WorkPackageStep("Check website HTTP status", "Checks whether the specific website responds over HTTPS.", ["curl", "-I", "--max-time", "8", "--location", https_url]),
        WorkPackageStep("Show route table", "Shows the current route table so mixed routing clues can be reviewed.", ["ip", "route"]),
    ]


def dns_work_package_steps() -> list[WorkPackageStep]:
    return [
        WorkPackageStep("Check local IP", "Checks whether this computer has a local network address.", ["ip", "-4", "addr", "show"]),
        WorkPackageStep("Check default gateway", "Checks whether the computer has a default router/gateway.", ["ip", "route", "show", "default"]),
        WorkPackageStep("Ping router/gateway", "Checks whether the current router/gateway responds.", ["ping", "-c", "3", "-W", "2", "<gateway>"]),
        WorkPackageStep("Ping public internet IP", "Checks whether a public internet IP responds without using DNS.", ["ping", "-c", "3", "-W", "2", "1.1.1.1"]),
        WorkPackageStep("Test DNS lookup", "Checks whether website names can be turned into internet addresses.", ["getent", "hosts", "example.com"]),
    ]


def gateway_router_work_package_steps() -> list[WorkPackageStep]:
    return [
        WorkPackageStep("Check local IP", "Checks whether this computer has a local network address.", ["ip", "-4", "addr", "show"]),
        WorkPackageStep("Check default gateway", "Checks whether the computer has a default router/gateway.", ["ip", "route", "show", "default"]),
        WorkPackageStep("Ping router/gateway", "Checks whether the current router/gateway responds.", ["ping", "-c", "3", "-W", "2", "<gateway>"]),
        WorkPackageStep("Show route table", "Shows the current route table so gateway/routing problems can be reviewed.", ["ip", "route"]),
        WorkPackageStep("Check neighbor/ARP table", "Shows nearby local network devices the computer has recently seen.", ["ip", "neighbor"]),
    ]


def internet_isp_work_package_steps() -> list[WorkPackageStep]:
    return [
        WorkPackageStep("Check local IP", "Checks whether this computer has a local network address.", ["ip", "-4", "addr", "show"]),
        WorkPackageStep("Check default gateway", "Checks whether the computer has a default router/gateway.", ["ip", "route", "show", "default"]),
        WorkPackageStep("Ping router/gateway", "Checks whether the current router/gateway responds.", ["ping", "-c", "3", "-W", "2", "<gateway>"]),
        WorkPackageStep("Ping public internet IP", "Checks whether a public internet IP responds without using DNS.", ["ping", "-c", "3", "-W", "2", "1.1.1.1"]),
        WorkPackageStep("Trace route to public IP", "Shows the path toward a public internet IP.", ["tracepath", "1.1.1.1"]),
        WorkPackageStep("Test DNS lookup", "Checks whether website names can be turned into internet addresses.", ["getent", "hosts", "example.com"]),
    ]


def normalize_website_target(target: str | None) -> str:
    raw_target = (target or "").strip()
    if not raw_target:
        return "example.com"

    parsed = urlparse(raw_target if "://" in raw_target else f"//{raw_target}")
    host = parsed.hostname or raw_target.split("/", 1)[0]
    match = re.match(r"[A-Za-z0-9.-]+", host.strip())
    if not match:
        return "example.com"
    return match.group(0).lower() or "example.com"


def web_https_work_package_steps(target: str | None = None) -> list[WorkPackageStep]:
    website = normalize_website_target(target)
    https_url = f"https://{website}"
    return [
        WorkPackageStep("Test DNS lookup", "Checks whether the website name resolves.", ["getent", "hosts", website]),
        WorkPackageStep("Ping public internet IP", "Checks whether the internet works by IP without relying on the website.", ["ping", "-c", "3", "-W", "2", "1.1.1.1"]),
        WorkPackageStep("Check website HTTP status", "Checks whether the website responds over HTTPS.", ["curl", "-I", "--max-time", "8", "--location", https_url]),
        WorkPackageStep("Check HTTPS/TLS connection", "Checks whether a TLS connection can be made to the website.", ["openssl", "s_client", "-connect", f"{website}:443", "-servername", website, "-brief"]),
        WorkPackageStep("Check TCP port 443", "Checks whether HTTPS port 443 is reachable.", ["nc", "-vz", "-w", "5", website, "443"]),
        WorkPackageStep("Check TCP port 80", "Checks whether HTTP port 80 is reachable.", ["nc", "-vz", "-w", "5", website, "80"]),
    ]


def live_all_tests_steps(target: str | None = None) -> list[WorkPackageStep]:
    """Broad live snapshot used when the user has no JSON report.

    This intentionally mirrors the Unknown/Mixed work package: it checks the
    current machine and network directly with safe read-only commands.
    """
    return unknown_mixed_work_package_steps(target)


def steps_for_flow(flow_used: str, website_target: str | None = None) -> list[WorkPackageStep]:
    if flow_used == "Healthy Flow":
        return healthy_work_package_steps(website_target)
    if flow_used == "Unknown/Mixed Issue Flow":
        return unknown_mixed_work_package_steps(website_target)
    if flow_used == "DNS Problem Flow":
        return dns_work_package_steps()
    if flow_used == "Gateway/Router Problem Flow":
        return gateway_router_work_package_steps()
    if flow_used == "Internet/ISP Problem Flow":
        return internet_isp_work_package_steps()
    if flow_used == "Web/HTTPS Problem Flow":
        return web_https_work_package_steps(website_target)
    return []


def run_step(step: WorkPackageStep, gateway: str | None = None) -> WorkPackageResult:
    if "<gateway>" in step.command and gateway is None:
        gateway = live_default_gateway()
    command = [gateway if part == "<gateway>" and gateway else part for part in step.command]
    if "<gateway>" in command:
        return WorkPackageResult(step.label, "skipped", "No current gateway was detected, so this step was skipped.", "")

    tool = command[0]
    if shutil.which(tool) is None:
        return WorkPackageResult(step.label, "skipped", f"Required tool is missing: {tool}", "")

    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=8, check=False, input="")
    except subprocess.TimeoutExpired as exc:
        output = text_from_timeout_parts(exc.stdout, exc.stderr)
        return WorkPackageResult(step.label, "warning", timeout_summary(step.label, output), output)

    output = (completed.stdout or "") + (completed.stderr or "")
    status, summary = status_from_completed_command(step.label, completed.returncode, output)
    return WorkPackageResult(step.label, status, summary, output.strip())


def status_from_completed_command(label: str, returncode: int, output: str) -> tuple[str, str]:
    if label == "Check HTTPS/TLS connection" and "CONNECTION ESTABLISHED" in output and "Verification: OK" in output:
        return "pass", "TLS connection succeeded and certificate verification is OK."
    if returncode == 0:
        return "pass", "This check passed."
    return "fail", "This check failed."


def timeout_summary(label: str, output: str) -> str:
    if label == "Check HTTPS/TLS connection" and "CONNECTION ESTABLISHED" in output and "Verification: OK" in output:
        return "TLS connection succeeded and certificate verification is OK, but the test command kept the connection open until timeout."
    if label == "Trace route to public IP" and output.strip():
        return "Trace route did not fully finish, but it reached several network hops. This can happen normally if some networks block trace route replies."
    return "This check timed out."


def text_from_timeout_parts(stdout, stderr) -> str:
    parts = []
    for part in (stdout, stderr):
        if part is None:
            continue
        if isinstance(part, bytes):
            parts.append(part.decode("utf-8", errors="replace"))
        else:
            parts.append(str(part))
    return "".join(parts).strip()


def live_default_gateway() -> str | None:
    if shutil.which("ip") is None:
        return None
    try:
        completed = subprocess.run(["ip", "route", "show", "default"], capture_output=True, text=True, timeout=4, check=False)
    except subprocess.TimeoutExpired:
        return None
    if completed.returncode != 0:
        return None
    return parse_default_gateway(completed.stdout)


def parse_default_gateway(output: str) -> str | None:
    for line in output.splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[0] == "default" and parts[1] == "via":
            return parts[2]
    return None


def summarize_work_package(flow_used: str, results: list[WorkPackageResult]) -> str:
    if not results:
        return "Work Package Summary:\nNo Work Package checks have been run yet."

    if flow_used not in {"Healthy Flow", "Unknown/Mixed Issue Flow", "DNS Problem Flow", "Gateway/Router Problem Flow", "Internet/ISP Problem Flow", "Web/HTTPS Problem Flow"}:
        return "Work Package Summary:\nNo summary is available for this flow yet."

    bad_results = [result for result in results if result.status != "pass"]

    if flow_used == "Unknown/Mixed Issue Flow" and not bad_results and len(results) >= len(unknown_mixed_work_package_steps()):
        return (
            "Work Package Summary:\n"
            "All unknown/mixed troubleshooting checks passed.\n\n"
            "Conclusion:\n"
            "No clear network failure is showing right now.\n\n"
            "Likely meaning:\n"
            "- The issue may have been temporary, or\n"
            "- The imported report did not contain enough detail to choose one cause.\n\n"
            "Next step:\n"
            "If the problem continues, copy these Work Package results into chat/support and run a fresh Network Diagnostics Report Tool report."
        )
    if flow_used == "Healthy Flow" and not bad_results and len(results) >= len(healthy_work_package_steps()):
        return (
            "Work Package Summary:\n"
            "All healthy/still-broken troubleshooting checks passed.\n\n"
            "Conclusion:\n"
            "The basic network and website checks passed right now.\n\n"
            "Likely meaning:\n"
            "- The issue may be inside the specific app/service, or\n"
            "- The issue may have been temporary.\n\n"
            "Next step:\n"
            "try the app or website again. If it still fails, copy these Work Package results into chat/support."
        )
    if flow_used == "DNS Problem Flow" and not bad_results and len(results) >= len(dns_work_package_steps()):
        return _all_passed_summary("DNS", "DNS problem")
    if flow_used == "Gateway/Router Problem Flow" and not bad_results and len(results) >= len(gateway_router_work_package_steps()):
        return _all_passed_summary("gateway/router", "gateway/router problem")
    if flow_used == "Internet/ISP Problem Flow" and not bad_results and len(results) >= len(internet_isp_work_package_steps()):
        return _all_passed_summary("internet/ISP", "internet/ISP problem")
    if flow_used == "Web/HTTPS Problem Flow" and not bad_results and len(results) >= len(web_https_work_package_steps()):
        return _all_passed_summary("web/HTTPS", "web/HTTPS problem")

    failed_names = ", ".join(result.label for result in bad_results)
    problem_label = _problem_label(flow_used)
    return (
        "Work Package Summary:\n"
        f"Some {problem_label} troubleshooting checks did not pass.\n\n"
        f"Checks to review: {failed_names}\n\n"
        "Next step:\n"
        "Focus on the failed or warning checks above."
    )


def _problem_label(flow_used: str) -> str:
    if flow_used == "Healthy Flow":
        return "healthy/still-broken"
    if flow_used == "Unknown/Mixed Issue Flow":
        return "unknown/mixed"
    if flow_used == "DNS Problem Flow":
        return "DNS"
    if flow_used == "Gateway/Router Problem Flow":
        return "gateway/router"
    if flow_used == "Internet/ISP Problem Flow":
        return "internet/ISP"
    if flow_used == "Web/HTTPS Problem Flow":
        return "web/HTTPS"
    return "network"


def _all_passed_summary(label: str, imported_problem: str) -> str:
    return (
        "Work Package Summary:\n"
        f"All {label} troubleshooting checks passed.\n\n"
        "Conclusion:\n"
        f"The {imported_problem} shown in the imported report is not happening right now.\n\n"
        "Likely meaning:\n"
        "- The issue was temporary, or\n"
        "- The imported/sample report does not match the current network.\n\n"
        "Next step:\n"
        "If the problem returns, run a fresh Network Diagnostics Report Tool report."
    )


def upsert_work_result(results: list[WorkPackageResult], new_result: WorkPackageResult) -> list[WorkPackageResult]:
    updated = [result for result in results if result.label != new_result.label]
    updated.append(new_result)
    return updated


def gateway_from_report(report: dict) -> str | None:
    for result in report.get("results", []):
        name = str(result.get("name", ""))
        if name.startswith("Ping ") and "1.1.1.1" not in name:
            candidate = name.removeprefix("Ping ").strip()
            if candidate:
                return candidate
    return None
