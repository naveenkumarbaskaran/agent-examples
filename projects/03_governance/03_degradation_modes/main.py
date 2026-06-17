"""
03_governance/03_degradation_modes — All DegradationMode variants with recovery.
Run: pip install agentplane-py && python main.py
"""
import asyncio
import agentplane
from agentplane import PolicyEngine, Policy, Selector, PolicyContext, AllowlistRule
from agentplane.degradation.modes import DegradationMode


async def main() -> None:
    engine = PolicyEngine()
    engine.add_policy(Policy(
        id="base.policy",
        selector=Selector(agents=["*"]),
        blocking=[AllowlistRule(tools=["search", "read_file"])],
    ))

    ctx = PolicyContext.new(agent_id="agent-1", tenant_id="acme",
                            hookpoint="before_tool_call", tool_name="search")

    async def test_call(label: str, expect_blocked: bool = False) -> None:
        try:
            await engine.evaluate(ctx)
            icon = "?" if expect_blocked else "✓"
            print(f"  {icon} {label:40} → allowed")
        except agentplane.PolicyBlocked as e:
            icon = "✓" if expect_blocked else "✗"
            print(f"  {icon} {label:40} → blocked ({e.reason[:50]})")
        except agentplane.PolicyDegraded as e:
            icon = "✓" if expect_blocked else "✗"
            print(f"  ⚠ {label:40} → degraded mode={e.mode}")

    print("=== DEGRADATION MODES ===\n")

    modes = [
        (DegradationMode.READ_ONLY,       "30s", "Only reads allowed, writes blocked"),
        (DegradationMode.NO_EXTERNAL,     "30s", "No external API calls"),
        (DegradationMode.RATE_THROTTLE,   "30s", "Slowed down, not blocked"),
        (DegradationMode.SAFE_TOOLS_ONLY, "30s", "Allowlist shrinks to safe set"),
        (DegradationMode.FULL_BLOCK,      "30s", "Nothing passes"),
    ]

    for mode, recover_after, desc in modes:
        print(f"  Mode: {mode.value} — {desc}")

        # Baseline: not degraded
        engine.recover("agent-1")
        await test_call(f"  Before degradation", expect_blocked=False)

        # Degrade
        engine.degrade("agent-1", mode, reason=f"Test {mode.value}", recover_after=recover_after)
        print(f"    is_degraded: {engine.is_degraded('agent-1')}")

        if mode == DegradationMode.FULL_BLOCK:
            await test_call(f"  While degraded ({mode.value})", expect_blocked=True)
        else:
            await test_call(f"  While degraded ({mode.value})", expect_blocked=False)

        # Recover
        engine.recover("agent-1")
        print(f"    recovered: {not engine.is_degraded('agent-1')}")
        await test_call(f"  After recovery", expect_blocked=False)
        print()

    print("✓ All degradation modes demonstrated")


if __name__ == "__main__":
    asyncio.run(main())
