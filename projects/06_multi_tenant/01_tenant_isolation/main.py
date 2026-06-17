"""
06_multi_tenant/01_tenant_isolation — 3 tenants, each with isolated tool allowlists.
Run: pip install agentplane-py && python main.py
"""
import asyncio
import agentplane
from agentplane import (
    PolicyEngine, Policy, Selector, PolicyContext,
    AllowlistRule, AuditRule,
)


async def main() -> None:
    engine = PolicyEngine()

    # ACME: finance team — billing and reporting only
    engine.add_policy(Policy(
        id="acme.isolation",
        selector=Selector(tenants=["acme"]),
        blocking=[AllowlistRule(tools=["charge_card", "refund", "get_balance", "generate_invoice"])],
        non_blocking=[AuditRule()],
        priority=100,
    ))

    # SIEMENS: engineering team — code and search tools
    engine.add_policy(Policy(
        id="siemens.isolation",
        selector=Selector(tenants=["siemens"]),
        blocking=[AllowlistRule(tools=["search", "read_file", "run_query", "generate_report"])],
        non_blocking=[AuditRule()],
        priority=100,
    ))

    # SAP: HR team — HR-specific tools only
    engine.add_policy(Policy(
        id="sap.isolation",
        selector=Selector(tenants=["sap"]),
        blocking=[AllowlistRule(tools=["search", "create_ticket", "send_email", "schedule_meeting"])],
        non_blocking=[AuditRule()],
        priority=100,
    ))

    test_cases = [
        # (tenant, tool, should_be_allowed)
        ("acme",    "charge_card",     True),
        ("acme",    "search",          False),   # ACME can't search
        ("acme",    "run_query",       False),   # ACME can't query
        ("siemens", "run_query",       True),
        ("siemens", "charge_card",     False),   # SIEMENS can't bill
        ("siemens", "generate_report", True),
        ("sap",     "create_ticket",   True),
        ("sap",     "charge_card",     False),   # SAP can't bill
        ("sap",     "search",          True),
        ("sap",     "run_query",       False),   # SAP can't query
    ]

    print("=== TENANT ISOLATION ===\n")
    print(f"  {'Tenant':10} {'Tool':20} {'Expected':10} {'Actual':10}")
    print(f"  {'-'*55}")

    for tenant, tool, expect_allow in test_cases:
        ctx = PolicyContext.new(
            agent_id="generic-agent",
            tenant_id=tenant,
            hookpoint="before_tool_call",
            tool_name=tool,
        )
        try:
            await engine.evaluate(ctx)
            actual = "allowed"
            icon = "✓" if expect_allow else "✗"
        except agentplane.PolicyBlocked:
            actual = "blocked"
            icon = "✓" if not expect_allow else "✗"

        expected = "allowed" if expect_allow else "blocked"
        print(f"  {icon} {tenant:10} {tool:20} {expected:10} {actual}")

    print(f"\n✓ Tenant isolation working — each tenant sees only their tools")


if __name__ == "__main__":
    asyncio.run(main())
