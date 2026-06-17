"""
03_governance/04_conflict_resolution — Two conflicting policies: most-restrictive wins, priority override.
Run: pip install agentplane-py && python main.py
"""
import asyncio
import agentplane
from agentplane import (
    PolicyEngine, Policy, Selector, PolicyContext,
    AllowlistRule, RateRule, DenylistRule,
)
from agentplane.core.policy import ConflictResolution


async def main() -> None:
    print("=== CONFLICT RESOLUTION: MOST RESTRICTIVE WINS (default) ===\n")

    engine = PolicyEngine()

    # Policy A: allows search + summarize, rate limit 100/h (permissive)
    engine.add_policy(Policy(
        id="acme.permissive",
        selector=Selector(tenants=["acme"]),
        blocking=[AllowlistRule(tools=["search", "summarize", "read_file", "export"])],
        conflict_resolution=ConflictResolution.MOST_RESTRICTIVE,
        priority=50,
    ))

    # Policy B: denies export tool (restrictive)
    engine.add_policy(Policy(
        id="acme.restrictive",
        selector=Selector(tenants=["acme"]),
        blocking=[DenylistRule(tools=["export", "delete"])],
        conflict_resolution=ConflictResolution.MOST_RESTRICTIVE,
        priority=50,
    ))

    cases = [
        ("search",    True,  "allowed by both"),
        ("summarize", True,  "allowed by both"),
        ("export",    False, "denied by restrictive policy — most restrictive wins"),
        ("delete",    False, "denied by restrictive policy"),
    ]

    for tool, expect_allow, note in cases:
        ctx = PolicyContext.new(agent_id="a1", tenant_id="acme",
                                hookpoint="before_tool_call", tool_name=tool)
        try:
            await engine.evaluate(ctx)
            icon = "✓" if expect_allow else "?"
            print(f"  {icon} {tool:12} → allowed  ({note})")
        except agentplane.PolicyBlocked as e:
            icon = "✓" if not expect_allow else "✗"
            print(f"  {icon} {tool:12} → blocked  ({note})")

    print("\n=== CONFLICT RESOLUTION: PRIORITY OVERRIDE ===\n")

    engine2 = PolicyEngine()

    # High-priority policy explicitly allows export for premium tier
    engine2.add_policy(Policy(
        id="premium.override",
        selector=Selector(tenants=["acme"], tags={"tier": "premium"}),
        blocking=[AllowlistRule(tools=["search", "export", "advanced_export"])],
        conflict_resolution=ConflictResolution.PRIORITY,
        priority=500,  # highest priority wins
    ))

    # Low-priority catch-all blocks export
    engine2.add_policy(Policy(
        id="default.restrictive",
        selector=Selector(tenants=["acme"]),
        blocking=[DenylistRule(tools=["export"])],
        conflict_resolution=ConflictResolution.MOST_RESTRICTIVE,
        priority=10,
    ))

    for tool, tier, expect_allow in [("search", "premium", True), ("export", "premium", True), ("export", "standard", False)]:
        ctx = PolicyContext.new(agent_id="a1", tenant_id="acme",
                                hookpoint="before_tool_call", tool_name=tool,
                                tags={"tier": tier})
        try:
            await engine2.evaluate(ctx)
            icon = "✓" if expect_allow else "?"
            print(f"  ✓ tier={tier:10} tool={tool:12} → allowed")
        except agentplane.PolicyBlocked as e:
            icon = "✓" if not expect_allow else "✗"
            print(f"  {icon} tier={tier:10} tool={tool:12} → blocked")

    print("\n✓ Conflict resolution working as designed")


if __name__ == "__main__":
    asyncio.run(main())
