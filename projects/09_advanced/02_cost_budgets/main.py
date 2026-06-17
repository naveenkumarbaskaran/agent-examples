"""
09_advanced/02_cost_budgets — $0.03/day limit, 5 calls at $0.008 each.
Shows blocking at budget exhaustion.
Run: pip install agentplane-py && python main.py
"""
import asyncio
import agentplane
from agentplane import (
    PolicyEngine, Policy, Selector, PolicyContext,
    AllowlistRule, CostBudgetRule, CostTrackingRule, AuditRule,
)


async def main() -> None:
    tracker = CostTrackingRule(track_per="tenant")

    engine = PolicyEngine()
    engine.add_policy(Policy(
        id="budget-demo",
        selector=Selector(tenants=["acme"]),
        blocking=[
            AllowlistRule(tools=["search", "analyze", "report"]),
            CostBudgetRule(max_usd=0.03, window="1d", per="tenant", on_breach="block"),
        ],
        non_blocking=[tracker, AuditRule()],
    ))

    print("=== COST BUDGET CONTROL ===\n")
    print(f"Budget: $0.03/day per tenant")
    print(f"Each call costs: $0.008\n")

    total_spent = 0.0
    for i in range(1, 7):
        cost = 0.008
        ctx = PolicyContext.new(
            agent_id="search-agent", tenant_id="acme",
            hookpoint="before_tool_call", tool_name="search",
            cost_usd=cost, token_count=100,
        )
        try:
            await engine.evaluate(ctx)
            total_spent += cost
            print(f"  Call {i}: ✓ allowed   spent=${total_spent:.3f}  remaining=${0.03-total_spent:.3f}")
        except agentplane.PolicyBlocked as e:
            print(f"  Call {i}: ✗ BLOCKED   spent=${total_spent:.3f}  reason={e.reason[:50]}")

    await asyncio.sleep(0.05)
    print(f"\nTracked cost: ${tracker.get_total('acme'):.4f}")
    print(f"Budget limit: $0.0300")
    print(f"\n✓ Budget enforcement working — blocked at exhaustion")


if __name__ == "__main__":
    asyncio.run(main())
