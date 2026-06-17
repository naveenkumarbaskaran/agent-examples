"""
04_observability/04_metrics
=============================
MetricsRule (non-blocking counters) + CostTrackingRule (USD totals per tenant).
Runs 10 evaluations across 2 tenants, prints cost totals and metric counts.
"""
import asyncio
import agentplane
from agentplane import (
    PolicyEngine, Policy, Selector, PolicyContext,
    AllowlistRule, MetricsRule, CostTrackingRule, AuditRule,
)


async def main() -> None:
    cost_tracker = CostTrackingRule(track_per="tenant")
    metrics = MetricsRule(emit_otel=False)

    engine = PolicyEngine()
    engine.add_policy(Policy(
        id="metrics-policy",
        selector=Selector(agents=["*"], tenants=["*"]),
        blocking=[AllowlistRule(tools=["search", "summarize", "read_file"])],
        non_blocking=[AuditRule(include_inputs=False), cost_tracker, metrics],
        priority=100,
    ))

    evals = [
        ("acme",    "search",    0.005, 100),
        ("acme",    "summarize", 0.012, 300),
        ("siemens", "search",    0.003,  80),
        ("acme",    "read_file", 0.002,  50),
        ("siemens", "search",    0.004,  90),
        ("acme",    "search",    0.008, 200),
        ("siemens", "summarize", 0.015, 350),
        ("acme",    "search",    0.006, 150),
        ("siemens", "read_file", 0.001,  40),
        ("siemens", "search",    0.007, 180),
    ]

    print("=== Metrics Demo ===\n")
    print("Running 10 evaluations across 2 tenants...\n")

    for tenant, tool, cost, tokens in evals:
        ctx = PolicyContext.new(
            agent_id=f"{tenant}-agent",
            tenant_id=tenant,
            hookpoint="before_tool_call",
            tool_name=tool,
            cost_usd=cost,
            token_count=tokens,
        )
        try:
            await engine.evaluate(ctx)
            print(f"  ✓ tenant={tenant:8} tool={tool:12} cost=${cost:.3f} tokens={tokens}")
        except agentplane.PolicyBlocked as e:
            print(f"  ✗ blocked: {e.reason[:50]}")

    await asyncio.sleep(0.05)

    print(f"\n--- Cost Totals per Tenant ---")
    acme_total    = cost_tracker.get_total("acme")
    siemens_total = cost_tracker.get_total("siemens")
    print(f"  acme:    ${acme_total:.4f}")
    print(f"  siemens: ${siemens_total:.4f}")
    print(f"  total:   ${acme_total + siemens_total:.4f}")

    print(f"\n--- MetricsRule Call Counts ---")
    for key, count in sorted(metrics._counts.items()):
        print(f"  {key}: {count}")

    print(f"\n✓ Metrics collection demonstrated.\n")


if __name__ == "__main__":
    asyncio.run(main())
