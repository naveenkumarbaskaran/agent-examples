"""Hello Policy — simplest agentplane example."""
# pip install agentplane-py
import asyncio
import agentplane
from agentplane import PolicyEngine, Policy, Selector, PolicyContext, AllowlistRule, AuditRule

async def main() -> None:
    engine = PolicyEngine()
    engine.add_policy(Policy(
        id="demo.basic",
        selector=Selector(agents=["*"]),
        blocking=[AllowlistRule(tools=["search", "summarize"])],
        non_blocking=[AuditRule()],
    ))

    ctx = PolicyContext.new(agent_id="my-agent", hookpoint="before_tool_call", tool_name="search")
    await engine.evaluate(ctx)
    print("✓ search — allowed")

    try:
        ctx2 = PolicyContext.new(agent_id="my-agent", hookpoint="before_tool_call", tool_name="drop_table")
        await engine.evaluate(ctx2)
    except agentplane.PolicyBlocked as e:
        print(f"✗ drop_table — blocked: {e.reason}")

if __name__ == "__main__":
    asyncio.run(main())
