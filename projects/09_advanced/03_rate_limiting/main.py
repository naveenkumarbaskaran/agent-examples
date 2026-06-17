"""
09_advanced/03_rate_limiting
==============================
RateRule with 5/minute limit per session.
Rapid-fire 8 calls — first 5 pass, next 3 blocked.
"""
import asyncio
import agentplane
from agentplane import (
    PolicyEngine, Policy, Selector, PolicyContext,
    AllowlistRule, RateRule, AuditRule,
)


async def main() -> None:
    engine = PolicyEngine()
    engine.add_policy(Policy(
        id="rate-limit-policy",
        selector=Selector(agents=["*"], tenants=["*"]),
        blocking=[
            AllowlistRule(tools=["search", "read_file"]),
            RateRule(limit=5, window="1m", per="session"),
        ],
        non_blocking=[AuditRule()],
        priority=100,
    ))

    session_id = "session-abc123"

    print("=== Rate Limiting Demo ===\n")
    print("Rate limit: 5 calls/minute per session\n")
    print("Firing 8 rapid calls — expect first 5 to pass, next 3 to block:\n")

    passed = 0
    blocked_calls = []

    for i in range(1, 9):
        ctx = PolicyContext.new(
            agent_id="search-agent",
            tenant_id="acme",
            hookpoint="before_tool_call",
            tool_name="search",
        )
        # Override session_id to control per-session limiting
        from dataclasses import replace
        ctx = replace(ctx, session_id=session_id)

        try:
            await engine.evaluate(ctx)
            passed += 1
            print(f"  call {i}: ✓ allowed  (total passed: {passed})")
        except agentplane.PolicyBlocked as e:
            blocked_calls.append(i)
            print(f"  call {i}: ✗ BLOCKED  — {e.reason[:60]}")

    print(f"\n--- Summary ---")
    print(f"  Passed:  {passed}  (expected 5)")
    print(f"  Blocked: {len(blocked_calls)} at calls {blocked_calls}  (expected [6, 7, 8])")

    assert passed == 5, f"Expected 5 passed, got {passed}"
    assert len(blocked_calls) == 3, f"Expected 3 blocked, got {len(blocked_calls)}"
    print(f"\n✓ Rate limiting validated: 5 pass, 3 block.\n")


if __name__ == "__main__":
    asyncio.run(main())
