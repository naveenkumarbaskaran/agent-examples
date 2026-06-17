"""
01_basics/02_first_policy
=========================
Your first agentplane policy. Covers Policy creation, selectors,
blocking rules, non-blocking rules, and evaluation.
"""
import asyncio
import agentplane
from agentplane import (
    PolicyEngine, Policy, Selector, PolicyContext,
    AllowlistRule, RateRule, RedactRule,
    AuditRule, CostTrackingRule, MetricsRule,
)


async def main() -> None:
    engine = PolicyEngine()

    engine.add_policy(Policy(
        id="acme.search-policy.v1",
        description="Controls search agent behaviour for ACME tenant",
        selector=Selector(
            agents=["search-agent"],
            tenants=["acme"],
            tools=["search", "summarize", "read_file"],
        ),
        blocking=[
            AllowlistRule(tools=["search", "summarize", "read_file"]),
            RateRule(limit=100, window="1h", per="tenant"),
            RedactRule(fields=["api_key", "password", "ssn"]),
        ],
        non_blocking=[
            AuditRule(include_inputs=True),
            CostTrackingRule(track_per="tenant"),
            MetricsRule(emit_otel=False),
        ],
        priority=100,
    ))

    cases = [
        ("search",     "acme",    True),
        ("summarize",  "acme",    True),
        ("delete_db",  "acme",    False),
        ("search",     "unknown", True),   # no policy matches unknown tenant
    ]

    for tool, tenant, expect_allow in cases:
        ctx = PolicyContext.new(
            agent_id="search-agent",
            tenant_id=tenant,
            hookpoint="before_tool_call",
            tool_name=tool,
            tool_inputs={"query": "test", "api_key": "secret123"},
            cost_usd=0.001,
            token_count=50,
        )
        try:
            await engine.evaluate(ctx)
            icon = "✓" if expect_allow else "?"
            print(f"{icon} tenant={tenant!r:10} tool={tool!r:12} → allowed")
        except agentplane.PolicyBlocked as e:
            icon = "✓" if not expect_allow else "✗"
            print(f"{icon} tenant={tenant!r:10} tool={tool!r:12} → blocked: {e.reason[:50]}")


if __name__ == "__main__":
    asyncio.run(main())
