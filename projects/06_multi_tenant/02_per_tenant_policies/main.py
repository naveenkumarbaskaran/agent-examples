"""
06_multi_tenant/02_per_tenant_policies — Different rate limits and cost budgets per tenant.
Run: pip install agentplane-py && python main.py
"""
import asyncio
import agentplane
from agentplane import (
    PolicyEngine, Policy, Selector, PolicyContext,
    AllowlistRule, RateRule, CostBudgetRule, AuditRule,
)


async def main() -> None:
    engine = PolicyEngine()

    # Standard tier: 5 calls/hour, $1/day
    engine.add_policy(Policy(
        id="standard.tier",
        selector=Selector(tenants=["startup-a", "startup-b"]),
        blocking=[
            AllowlistRule(tools=["search", "summarize"]),
            RateRule(limit=5, window="1h", per="tenant", on_breach="block"),
            CostBudgetRule(max_usd=1.0, window="1d", per="tenant"),
        ],
        non_blocking=[AuditRule()],
        priority=100,
    ))

    # Premium tier: 50 calls/hour, $20/day
    engine.add_policy(Policy(
        id="premium.tier",
        selector=Selector(tenants=["acme", "siemens"]),
        blocking=[
            AllowlistRule(tools=["search", "summarize", "charge_card", "report", "export"]),
            RateRule(limit=50, window="1h", per="tenant", on_breach="block"),
            CostBudgetRule(max_usd=20.0, window="1d", per="tenant"),
        ],
        non_blocking=[AuditRule()],
        priority=100,
    ))

    async def run_calls(tenant: str, tool: str, n: int, cost_per_call: float) -> dict:
        allowed = 0
        blocked = 0
        for i in range(n):
            ctx = PolicyContext.new(
                agent_id="shared-agent", tenant_id=tenant,
                hookpoint="before_tool_call", tool_name=tool,
                cost_usd=cost_per_call, token_count=100,
            )
            try:
                await engine.evaluate(ctx)
                allowed += 1
            except (agentplane.PolicyBlocked, agentplane.PolicyDegraded):
                blocked += 1
        return {"allowed": allowed, "blocked": blocked}

    print("=== PER-TENANT POLICIES ===\n")

    # Standard tenants: hit rate limit at 6th call
    print("Standard tier (startup-a) — limit: 5/hour")
    r = await run_calls("startup-a", "search", 8, 0.01)
    print(f"  8 calls → {r['allowed']} allowed, {r['blocked']} blocked (limit=5)")

    # Premium tenant: much higher limit
    print("\nPremium tier (acme) — limit: 50/hour")
    r2 = await run_calls("acme", "search", 8, 0.01)
    print(f"  8 calls → {r2['allowed']} allowed, {r2['blocked']} blocked (limit=50)")

    # Tool access difference
    print("\nTool access by tier:")
    for tenant, tool, tier in [
        ("startup-a", "export",      "standard"),
        ("acme",      "export",      "premium"),
        ("startup-b", "charge_card", "standard"),
        ("siemens",   "charge_card", "premium"),
    ]:
        ctx = PolicyContext.new(agent_id="a", tenant_id=tenant, hookpoint="before_tool_call", tool_name=tool, cost_usd=0.001)
        try:
            await engine.evaluate(ctx)
            print(f"  ✓ {tier:10} tenant={tenant:12} tool={tool:12} → allowed")
        except agentplane.PolicyBlocked:
            print(f"  ✗ {tier:10} tenant={tenant:12} tool={tool:12} → blocked")


if __name__ == "__main__":
    asyncio.run(main())
