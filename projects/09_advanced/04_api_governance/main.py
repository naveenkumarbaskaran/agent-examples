"""
09_advanced/04_api_governance
================================
ApiAllowlistRule + ApiDenylistRule.
Tests /api/v1/* allowed, /admin/* denied, GET allowed, DELETE blocked.
"""
import asyncio
import agentplane
from agentplane import (
    PolicyEngine, Policy, Selector, PolicyContext,
)
from agentplane.rules.api import ApiAllowlistRule, ApiDenylistRule


async def check_api(engine: PolicyEngine, path: str, method: str) -> tuple[bool, str]:
    """Evaluate an API call. Returns (allowed, reason)."""
    ctx = PolicyContext.new(
        agent_id="api-agent",
        tenant_id="acme",
        hookpoint="before_tool_call",
        tool_name="call_api",
        metadata={"api_path": path, "api_method": method},
    )
    try:
        await engine.evaluate(ctx)
        return True, "allowed"
    except agentplane.PolicyBlocked as e:
        return False, e.reason[:60]


async def main() -> None:
    engine = PolicyEngine()
    engine.add_policy(Policy(
        id="api-governance-policy",
        selector=Selector(agents=["*"], tenants=["*"]),
        blocking=[
            ApiAllowlistRule(paths=["/api/v1/*", "/api/v2/*"], methods=["GET", "POST"]),
            ApiDenylistRule(paths=["/admin/*", "/internal/*", "/debug/*"]),
        ],
        priority=100,
    ))

    print("=== API Governance Demo ===\n")
    print("Allowlist: /api/v1/* + /api/v2/* — GET, POST only")
    print("Denylist:  /admin/*, /internal/*, /debug/*\n")

    test_cases = [
        # (path,                    method,  expect_allowed, description)
        ("/api/v1/search",         "GET",   True,  "GET /api/v1/search — allowed"),
        ("/api/v1/users",          "POST",  True,  "POST /api/v1/users — allowed"),
        ("/api/v2/reports",        "GET",   True,  "GET /api/v2/reports — allowed"),
        ("/api/v1/users",          "DELETE",False, "DELETE /api/v1/users — method not allowed"),
        ("/admin/settings",        "GET",   False, "GET /admin/settings — denylist"),
        ("/internal/metrics",      "GET",   False, "GET /internal/metrics — denylist"),
        ("/debug/trace",           "GET",   False, "GET /debug/trace — denylist"),
        ("/api/v1/search",         "GET",   True,  "GET /api/v1/search — still allowed"),
        ("/other/endpoint",        "GET",   False, "GET /other/endpoint — not in allowlist"),
    ]

    for path, method, expect_allowed, desc in test_cases:
        allowed, reason = await check_api(engine, path, method)
        icon = "✓" if allowed == expect_allowed else "✗"
        status = "ALLOWED" if allowed else f"BLOCKED: {reason}"
        print(f"  {icon} {method:7} {path:30} → {status}")

    print(f"\n✓ API governance demonstrated.\n")


if __name__ == "__main__":
    asyncio.run(main())
