"""
03_governance/01_policy_versioning — Publish v1/v2/v3, diff, rollback, history.
Run: pip install agentplane-py && python main.py
"""
import asyncio
import agentplane
from agentplane import (
    PolicyEngine, Policy, Selector, PolicyContext,
    AllowlistRule, RateRule, RedactRule, TokenBudgetRule,
    AuditRule, VersionManager,
)


async def main() -> None:
    vm = VersionManager()
    engine = PolicyEngine()

    # v1 — basic allowlist + rate limit
    p1 = Policy(
        id="acme.search-policy",
        selector=Selector(tenants=["acme"]),
        blocking=[
            AllowlistRule(tools=["search", "summarize"]),
            RateRule(limit=100, window="1h"),
        ],
        non_blocking=[AuditRule()],
        version=1,
        description="Initial search policy",
    )
    vm.publish(p1, changelog="Initial: allowlist + rate limit")
    engine.add_policy(p1)
    print(f"✓ Published v1: {p1}")

    # v2 — add redaction, tighter rate limit
    p2 = Policy(
        id="acme.search-policy",
        selector=Selector(tenants=["acme"]),
        blocking=[
            AllowlistRule(tools=["search", "summarize", "read_file"]),
            RateRule(limit=50, window="1h"),          # tighter
            RedactRule(fields=["api_key", "password"]), # new
        ],
        non_blocking=[AuditRule()],
        version=2,
        description="Add redaction, tighten rate limit",
    )
    vm.publish(p2, changelog="Tighten rate limit to 50/h, add redaction")
    engine.add_policy(p2)
    print(f"✓ Published v2: {p2}")

    # v3 — add token budget
    p3 = Policy(
        id="acme.search-policy",
        selector=Selector(tenants=["acme"]),
        blocking=[
            AllowlistRule(tools=["search", "summarize", "read_file"]),
            RateRule(limit=50, window="1h"),
            RedactRule(fields=["api_key", "password", "ssn"]),
            TokenBudgetRule(max_tokens=100_000, window="1d"),  # new
        ],
        non_blocking=[AuditRule()],
        version=3,
        description="Add token budget control",
    )
    vm.publish(p3, changelog="Add 100k daily token budget")
    engine.add_policy(p3)
    print(f"✓ Published v3: {p3}")

    # Diff v1 → v2
    print(f"\n=== DIFF v1 → v2 ===")
    diff = vm.diff("acme.search-policy", 1, 2)
    print(f"  Added blocking:   {diff.added_blocking}")
    print(f"  Removed blocking: {diff.removed_blocking}")

    # Diff v2 → v3
    print(f"\n=== DIFF v2 → v3 ===")
    diff2 = vm.diff("acme.search-policy", 2, 3)
    print(f"  Added blocking:   {diff2.added_blocking}")

    # Full history
    print(f"\n=== VERSION HISTORY ===")
    for v in vm.history("acme.search-policy"):
        print(f"  v{v.version}: {v.changelog}")

    # Rollback to v1
    print(f"\n=== ROLLBACK TO v1 ===")
    restored = vm.rollback("acme.search-policy", to_version=1)
    engine.add_policy(restored)
    print(f"  Restored as: v{restored.version} (history preserved, no destructive reset)")
    print(f"  Full history now has {len(vm.history('acme.search-policy'))} versions")

    # Test restored policy
    print(f"\n=== TEST AFTER ROLLBACK ===")
    ctx = PolicyContext.new(agent_id="a1", tenant_id="acme",
                            hookpoint="before_tool_call", tool_name="search")
    await engine.evaluate(ctx)
    print("  ✓ search — allowed on restored v1")

    try:
        ctx2 = PolicyContext.new(agent_id="a1", tenant_id="acme",
                                 hookpoint="before_tool_call", tool_name="delete_db")
        await engine.evaluate(ctx2)
    except agentplane.PolicyBlocked as e:
        print(f"  ✗ delete_db — blocked: {e.reason[:60]}")


if __name__ == "__main__":
    asyncio.run(main())
