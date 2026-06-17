"""
04_observability/02_live_dashboard
=====================================
Run 5 policy evaluations against a real PolicyEngine, then print
an agentobserve dashboard snapshot with rich output.
"""
import asyncio
import agentplane
from agentplane import (
    PolicyEngine, Policy, Selector, PolicyContext,
    AllowlistRule, RateRule, AuditRule, CostTrackingRule,
)
from agentobserve import ObserveDashboard


async def main() -> None:
    engine = PolicyEngine()
    engine.add_policy(Policy(
        id="acme.search",
        selector=Selector(agents=["search-agent"], tenants=["acme"]),
        blocking=[
            AllowlistRule(tools=["search", "summarize"]),
            RateRule(limit=5, window="1m"),
        ],
        non_blocking=[AuditRule(), CostTrackingRule()],
        priority=100,
    ))

    tools = ["search", "summarize", "search", "drop_table", "search"]

    print("=== Running Policy Evaluations ===\n")
    for tool in tools:
        ctx = PolicyContext.new(
            agent_id="search-agent",
            tenant_id="acme",
            hookpoint="before_tool_call",
            tool_name=tool,
            cost_usd=0.001,
        )
        try:
            await engine.evaluate(ctx)
            print(f"  ✓ {tool:15} → allowed")
        except agentplane.PolicyBlocked as e:
            print(f"  ✗ {tool:15} → blocked: {e.reason[:50]}")
        except agentplane.PolicyDegraded as e:
            print(f"  ⚠ {tool:15} → degraded")

    print("\n=== Dashboard Snapshot ===\n")
    dash = ObserveDashboard(engine=engine)
    snap = dash.snapshot()
    print(f"Active agents:  {snap.active_count}")
    print(f"Degraded:       {snap.degraded_count}")
    print(f"Total evals:    {snap.total_evals}")
    print(f"Block rate:     {snap.block_rate:.1%}")
    print()
    dash.print_snapshot()


if __name__ == "__main__":
    asyncio.run(main())
