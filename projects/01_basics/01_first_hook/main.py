"""
01_basics/01_first_hook
=======================
Your first agenthooks hook. Shows how to register a hook implementation,
enrich context with metadata, and run it through a hookpoint.
"""
import asyncio
from agenthooks import HookRegistry, HookContext, hookpoint, inject, AuditRule


async def main() -> None:
    registry = HookRegistry(default_timeout_ms=1000)
    hp_before = hookpoint("before_tool_call", registries=[registry])
    hp_after  = hookpoint("after_tool_call",  registries=[registry])

    # Hook 1: inject tenant metadata before every tool call
    @registry.implement("before_tool_call", order=1)
    async def inject_tenant(ctx: HookContext) -> HookContext:
        return ctx.enrich("tenant_enriched", True).enrich("region", "eu-west")

    # Hook 2: validate tool is in allowlist
    @registry.implement("before_tool_call", order=2)
    async def validate_tool(ctx: HookContext) -> HookContext:
        allowed = {"search", "summarize", "read_file"}
        if ctx.tool_name not in allowed:
            ctx.block(f"tool '{ctx.tool_name}' not in allowlist")
        return ctx

    # Hook 3: log after tool call
    @registry.implement("after_tool_call", order=1)
    async def log_result(ctx: HookContext) -> HookContext:
        print(f"[after] tool={ctx.tool_name} result_keys={list((ctx.tool_result or {}).keys())}")
        return ctx

    print("=== Allowed tool call ===")
    ctx = HookContext.new(session_id="s1", tenant_id="acme", tool_name="search")
    async with hp_before.run(ctx) as enriched:
        # Simulate tool execution
        result_ctx = enriched.replace("tool_result", {"results": ["doc1", "doc2"]})
        async with hp_after.run(result_ctx) as final:
            print(f"  region={final.metadata.get('region')}")
            print(f"  enriched={final.metadata.get('tenant_enriched')}")

    print("\n=== Blocked tool call ===")
    ctx2 = HookContext.new(session_id="s1", tenant_id="acme", tool_name="drop_table")
    try:
        async with hp_before.run(ctx2) as _:
            pass
    except Exception as e:
        print(f"  blocked: {e}")


if __name__ == "__main__":
    asyncio.run(main())
