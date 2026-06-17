"""
07_production/01_hooks_plus_policy — agenthooks + agentplane wired together.
Run: pip install agenthooks-py agentplane-py && python main.py
"""
import asyncio
import agentplane
from agenthooks import HookRegistry, HookContext, hookpoint, inject
from agentplane import PolicyEngine, Policy, Selector, PolicyContext, AllowlistRule, AuditRule


async def main() -> None:
    # ── Setup agenthooks ──────────────────────────────────────────────────────
    registry = HookRegistry()
    hp = hookpoint("before_tool_call", registries=[registry])

    @registry.implement("before_tool_call", order=1)
    async def enrich_with_tenant(ctx: HookContext) -> HookContext:
        return ctx.enrich("region", "eu-west-1").enrich("version", "2.1.0")

    @registry.implement("before_tool_call", order=2)
    async def log_call(ctx: HookContext) -> HookContext:
        print(f"  [hook] session={ctx.session_id} tool={ctx.tool_name} tenant={ctx.tenant_id}")
        return ctx

    # ── Setup agentplane ──────────────────────────────────────────────────────
    engine = PolicyEngine()
    engine.add_policy(Policy(
        id="acme.combined",
        selector=Selector(tenants=["acme"]),
        blocking=[AllowlistRule(tools=["search", "summarize", "charge_card"])],
        non_blocking=[AuditRule()],
    ))

    # ── Combined pipeline ─────────────────────────────────────────────────────
    async def agent_call(session_id: str, tenant_id: str, tool: str) -> dict:
        # Step 1: Run hooks (enrich context)
        hook_ctx = HookContext.new(session_id=session_id, tenant_id=tenant_id, tool_name=tool)
        async with hp.run(hook_ctx) as enriched:
            # Step 2: Run policy (enforce rules using enriched context)
            policy_ctx = PolicyContext.new(
                agent_id=session_id,
                tenant_id=enriched.tenant_id,
                hookpoint="before_tool_call",
                tool_name=enriched.tool_name,
                metadata=enriched.metadata,
            )
            await engine.evaluate(policy_ctx)
            return {"tool": tool, "region": enriched.metadata.get("region"), "status": "ok"}

    print("=== HOOKS + POLICY PIPELINE ===\n")
    calls = [
        ("s1", "acme", "search"),
        ("s1", "acme", "charge_card"),
        ("s1", "acme", "drop_table"),  # should be blocked
        ("s2", "acme", "summarize"),
    ]

    for session_id, tenant_id, tool in calls:
        print(f"\nCall: tool={tool!r} tenant={tenant_id!r}")
        try:
            result = await agent_call(session_id, tenant_id, tool)
            print(f"  ✓ success: region={result['region']} status={result['status']}")
        except agentplane.PolicyBlocked as e:
            print(f"  ✗ blocked by policy: {e.reason[:60]}")

    print("\n✓ Hooks enriched context, policy enforced rules")


if __name__ == "__main__":
    asyncio.run(main())
