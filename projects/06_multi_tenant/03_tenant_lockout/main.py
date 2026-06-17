"""
06_multi_tenant/03_tenant_lockout — PlugBoard: lock out a tenant, restore access.
Run: pip install agentplane-py && python main.py
"""
import asyncio
import agentplane
from agentplane import (
    PolicyEngine, Policy, Selector, PolicyContext,
    AllowlistRule, PlugBoard,
)


async def main() -> None:
    board = PlugBoard()
    engine = PolicyEngine(plug_board=board)

    engine.add_policy(Policy(
        id="base.policy",
        selector=Selector(agents=["*"]),
        blocking=[AllowlistRule(tools=["search", "charge_card", "report"])],
    ))

    # Register agents
    agents = [
        ("billing-agent-1", "acme"),
        ("billing-agent-2", "acme"),
        ("search-agent-1",  "acme"),
        ("report-agent-1",  "siemens"),
        ("search-agent-2",  "siemens"),
    ]
    for agent_id, tenant_id in agents:
        board.register(agent_id, tenant_id=tenant_id)

    async def test_agent(agent_id: str, tool: str = "search") -> str:
        ctx = PolicyContext.new(agent_id=agent_id, tenant_id="acme",
                                hookpoint="before_tool_call", tool_name=tool)
        try:
            await engine.evaluate(ctx)
            return "allowed"
        except agentplane.PolicyBlocked as e:
            return f"blocked ({e.reason[:40]})"

    print("=== BEFORE LOCKOUT ===")
    for agent_id, _ in agents[:3]:
        result = await test_agent(agent_id)
        print(f"  {agent_id:25} → {result}")

    print(f"\n=== SECURITY INCIDENT: Locking out ACME tenant ===")
    unplugged = board.unplug_all("acme", reason="Security incident — unusual billing activity", by="security-team")
    print(f"  Unplugged {len(unplugged)} agents: {unplugged}")

    print(f"\n=== DURING LOCKOUT ===")
    for agent_id, tenant in agents:
        result = await test_agent(agent_id)
        icon = "✗" if "blocked" in result else "✓"
        print(f"  {icon} {agent_id:25} (tenant={tenant}) → {result[:55]}")

    print(f"\n  siemens agents unaffected: {not engine._plug_board.is_plugged('report-agent-1') is False}")

    print(f"\n=== RESTORE SINGLE AGENT ===")
    board.plug("billing-agent-1")
    result = await test_agent("billing-agent-1")
    print(f"  billing-agent-1 after plug: {result}")
    result2 = await test_agent("billing-agent-2")
    print(f"  billing-agent-2 still locked: {result2[:55]}")

    print(f"\n=== RESTORE ALL ACME AGENTS ===")
    for agent_id, tenant in agents:
        if tenant == "acme":
            board.plug(agent_id)
    for agent_id, tenant in agents[:3]:
        result = await test_agent(agent_id)
        print(f"  ✓ {agent_id:25} → {result}")

    print(f"\nUnplugged agents remaining: {[s.agent_id for s in board.list_unplugged()]}")
    print("✓ Tenant lockout and restore complete")


if __name__ == "__main__":
    asyncio.run(main())
