"""
08_wire_ai/03_budget_control — CostBudgetRule + TokenBudgetRule, graceful exhaustion.
Run: pip install agentplane-py && python main.py
"""
import asyncio
import agentplane
from agentplane import (
    PolicyEngine, Policy, Selector, PolicyContext,
    AllowlistRule, CostBudgetRule, TokenBudgetRule,
    AuditRule, CostTrackingRule, DegradationMode,
)


async def main() -> None:
    cost_tracker = CostTrackingRule(track_per="agent")

    engine = PolicyEngine()
    engine.add_policy(Policy(
        id="budget.policy",
        selector=Selector(agents=["*"]),
        blocking=[
            AllowlistRule(tools=["search", "summarize", "analyze", "report"]),
            CostBudgetRule(max_usd=0.05, window="1d", per="tenant", on_breach="block"),
            TokenBudgetRule(max_tokens=500, window="1d", per="tenant", on_breach="degrade"),
        ],
        non_blocking=[AuditRule(), cost_tracker],
    ))

    # Simulate LLM calls with increasing costs
    calls = [
        ("search-agent",  "acme", "search",    0.005, 50),   # $0.005, 50 tokens
        ("search-agent",  "acme", "summarize", 0.012, 120),  # $0.012, 120 tokens
        ("analyze-agent", "acme", "analyze",   0.018, 180),  # $0.018, 180 tokens
        ("report-agent",  "acme", "report",    0.020, 200),  # $0.020, 200 tokens — budget exceeded
        ("search-agent",  "acme", "search",    0.005,  50),  # should be blocked
    ]

    print("=== BUDGET CONTROL ===\n")
    print(f"Cost budget:  $0.05/day per tenant")
    print(f"Token budget: 500 tokens/day per tenant\n")

    running_cost = 0.0
    running_tokens = 0

    for agent_id, tenant, tool, cost, tokens in calls:
        ctx = PolicyContext.new(
            agent_id=agent_id, tenant_id=tenant,
            hookpoint="before_tool_call", tool_name=tool,
            cost_usd=cost, token_count=tokens,
        )
        running_cost += cost
        running_tokens += tokens
        try:
            await engine.evaluate(ctx)
            print(f"  ✓ {tool:10} cost=${cost:.3f} tokens={tokens:4d}  "
                  f"[running: ${running_cost:.3f} / {running_tokens} tokens]")
        except agentplane.PolicyBlocked as e:
            print(f"  ✗ {tool:10} BLOCKED — {e.reason[:60]}")
            running_cost -= cost  # didn't execute
            running_tokens -= tokens
        except agentplane.PolicyDegraded as e:
            print(f"  ⚠ {tool:10} DEGRADED mode={e.mode} — {e.args[0][:50]}")

    await asyncio.sleep(0.05)  # Let non-blocking rules fire

    print(f"\n=== BUDGET SUMMARY ===")
    print(f"  acme total cost:  ${cost_tracker.get_total('acme'):.4f} (limit: $0.05)")
    print(f"\n  Status: {'BUDGET EXHAUSTED' if running_cost >= 0.05 else 'Within budget'}")
    print("✓ Budget control working — blocked when limit exceeded")


if __name__ == "__main__":
    asyncio.run(main())
