from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TroubleshootingAnalysis:
    likely_problem: str
    flow_used: str
    why: str
    next_step: str
    it_summary: str
    flow_steps: list[str]


def analyze_report(report: dict[str, Any]) -> TroubleshootingAnalysis:
    problem_area = _problem_area(report)

    if problem_area in {None, "none", "healthy"}:
        return _analysis(
            likely_problem="No obvious network problem found",
            flow_used="Healthy Flow",
            why="The basic network checks passed. This means your connection looks okay from this report.",
            next_step="If you are still having trouble, test the specific website, app, or service that is not working.",
        )

    if problem_area in {"local_adapter_or_dhcp", "adapter", "interfaces"}:
        return _analysis(
            likely_problem="Local adapter/IP problem",
            flow_used="Local Adapter/IP Problem Flow",
            why="The report suggests the computer may not have a healthy local network address or interface state.",
            next_step="Check whether Wi-Fi or Ethernet is connected and whether the computer received an IP address.",
        )

    if problem_area in {"routing_or_dhcp", "gateway_or_local_network", "gateway", "router"}:
        return _analysis(
            likely_problem="Gateway/router problem",
            flow_used="Gateway/Router Problem Flow",
            why="Your computer has network information, but it could not reach the router/gateway.",
            next_step="Check Wi-Fi/Ethernet first. Then check router power. If possible, test whether another device can use the same network.",
        )

    if problem_area in {"internet_or_isp", "isp", "internet"}:
        return _analysis(
            likely_problem="Internet/ISP problem",
            flow_used="Internet/ISP Problem Flow",
            why="Your router may be working, but the internet beyond your router failed.",
            next_step="Test another device on the same network. If that device also has no internet, check the router internet/WAN light or contact your ISP.",
        )

    if problem_area == "dns":
        return _analysis(
            likely_problem="DNS problem",
            flow_used="DNS Problem Flow",
            why="DNS problem: your computer appears connected, but it cannot turn website names like example.com into internet addresses.",
            next_step="If using a VPN, turn it off and test again. Restart the router. If it still fails, check DNS settings or contact your ISP/IT.",
            flow_steps=[
                "Confirm the computer has a local IP address.",
                "Confirm a default router/gateway exists.",
                "Confirm the router/gateway is reachable.",
                "Confirm public internet by IP works.",
                "Check DNS name lookup.",
                "If DNS lookup fails while earlier checks pass, treat this as a DNS problem.",
                "Try VPN off, router restart, DNS settings, then ISP/IT support if still failing.",
            ],
        )

    if problem_area in {"web_tls_proxy_or_site", "https", "web"}:
        return _analysis(
            likely_problem="Web/HTTPS problem",
            flow_used="Web/HTTPS Problem Flow",
            why="DNS worked, so the website name was found, but the web connection still failed.",
            next_step="Try a different website or browser. Also check for a sign-in page/captive portal, VPN, proxy, firewall, or a problem with the website itself.",
        )

    return _analysis(
        likely_problem="Unknown or mixed network issue",
        flow_used="Unknown/Mixed Issue Flow",
        why="The report has mixed or incomplete results, so the app cannot choose one clear cause yet.",
        next_step="Open the report details and look for warnings, skipped checks, or failed checks. Then run a more specific check in the Network Diagnostics Report Tool.",
    )


def _problem_area(report: dict[str, Any]) -> str | None:
    overall = report.get("overall") or {}
    status = str(overall.get("status") or "").lower()
    likely = overall.get("likely_problem_area")
    if status == "healthy":
        return "healthy"
    if likely:
        return str(likely).lower()

    results = report.get("results") or []
    by_name = {str(r.get("name", "")).lower(): str(r.get("status", "")).lower() for r in results}

    interfaces = _find_status(by_name, "interfaces")
    routes = _find_status(by_name, "routes")
    gateway_ping = _find_gateway_ping_status(by_name)
    internet_ping = _find_status(by_name, "ping 1.1.1.1")
    dns = _find_prefix_status(by_name, "dns lookup")
    https = _find_prefix_status(by_name, "https check") or _find_prefix_status(by_name, "http status")

    if interfaces and interfaces != "pass":
        return "local_adapter_or_dhcp"
    if routes and routes != "pass":
        return "routing_or_dhcp"
    if gateway_ping == "fail":
        return "gateway_or_local_network"
    if internet_ping == "fail":
        return "internet_or_isp"
    if dns == "fail":
        return "dns"
    if https == "fail":
        return "web_tls_proxy_or_site"
    if results and all(str(r.get("status", "")).lower() == "pass" for r in results):
        return "healthy"
    return "unknown"


def _find_status(by_name: dict[str, str], name: str) -> str | None:
    return by_name.get(name.lower())


def _find_prefix_status(by_name: dict[str, str], prefix: str) -> str | None:
    prefix = prefix.lower()
    for name, status in by_name.items():
        if name.startswith(prefix):
            return status
    return None


def _find_gateway_ping_status(by_name: dict[str, str]) -> str | None:
    for name, status in by_name.items():
        if name.startswith("ping ") and "1.1.1.1" not in name:
            return status
    return None


def _analysis(
    likely_problem: str,
    flow_used: str,
    why: str,
    next_step: str,
    flow_steps: list[str] | None = None,
) -> TroubleshootingAnalysis:
    flow_steps = flow_steps or []
    summary_lines = [
        f"Likely problem: {likely_problem}",
        f"Flow used: {flow_used}",
        f"Why: {why}",
        f"Next step: {next_step}",
    ]
    if flow_steps:
        summary_lines.extend(["", "Troubleshooting flow:"])
        summary_lines.extend(f"{index}. {step}" for index, step in enumerate(flow_steps, start=1))
    it_summary = "\n".join(summary_lines)
    return TroubleshootingAnalysis(
        likely_problem=likely_problem,
        flow_used=flow_used,
        why=why,
        next_step=next_step,
        it_summary=it_summary,
        flow_steps=flow_steps,
    )
