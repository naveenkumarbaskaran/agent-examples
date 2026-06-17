"""
09_advanced/01_plug_unplug — PlugBoard: 5 agents, unplug 2, restore 1, test all.
Run: pip install agentplane-py && python main.py
"""
import asyncio
import agentplane
from agentplane import PolicyEngine, Policy, Selector, PolicyContext, AllowlistRule, PlugBoard


async def main() -> None:
    board = PlugBoard()
    engine = PolicyEngine(plug_board=board)
    engine.add_policy(Policy(
        id="base", selector=Selector(agents=["*"]),
        blocking=[AllowlistRule(tools=["search", "report"])],
    ))

    # Register 5 agents across 2 tenants
    agents = [
        ("billing-1",  "acme"),
        ("billing-2",  "acme"),
        ("search-1",   "acme"),
        ("analytics-1","siemens"),
        ("report-1",   "siemens"),
    ]
    for aid, tid in agents:
        board.register(aid, tenant_id=tid)

    async def status(aid: str) -> str:
        ctx = PolicyContext.new(agent_id=aid, tenant_id="acme",
                                hookpoint="before_tool_call", tool_name="search")
        try:
            await engine.evaluate(ctx)
            return "✓ plugged"
        except agentplane.PolicyBlocked as e:
            return f"✗ blocked ({e.reason[:30]})"

    print("=== PLUG / UNPLUG ===\n")

    print("Initial state (all plugged):")
    for aid, _ in agents:
        print(f"  {aid:15} {await status(aid)}")

    print(f"\nUnplugging billing-1 (budget exhausted) and billing-2 (security review)...")
    board.unplug("billing-1", reason="daily cost budget exhausted", by="cost-monitor")
    board.unplug("billing-2", reason="unusual activity — security review", by="security-team")

    print(f"\nAfter unplug (billing-1, billing-2):")
    for aid, _ in agents:
        s = await status(aid)
        print(f"  {aid:15} {s}")

    print(f"\nRestoring billing-1 after budget reset...")
    board.plug("billing-1")

    print(f"\nAfter restore (billing-1):")
    for aid, _ in agents:
        s = await status(aid)
        print(f"  {aid:15} {s}")

    print(f"\n=== SUMMARY ===")
    unplugged = board.list_unplugged()
    print(f"  Still unplugged: {[s.agent_id for s in unplugged]}")
    for slot in unplugged:
        print(f"    {slot.agent_id}: {slot.unplugged_reason}")

    print(f"\n✓ Plug/Unplug control demonstrated")


if __name__ == "__main__":
    asyncio.run(main())
