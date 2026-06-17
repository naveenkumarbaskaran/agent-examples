"""Hello Hooks — simplest agenthooks example."""
# pip install agenthooks-py
import asyncio
from agenthooks import HookRegistry, HookContext, hookpoint

async def main() -> None:
    registry = HookRegistry()
    hp = hookpoint("before_call", registries=[registry])

    @registry.implement("before_call")
    async def log_call(ctx: HookContext) -> HookContext:
        print(f"[hook] session={ctx.session_id} tool={ctx.tool_name}")
        return ctx.enrich("logged", True)

    ctx = HookContext.new(session_id="s1", tool_name="search")
    async with hp.run(ctx) as out:
        print(f"[agent] logged={out.metadata.get('logged')}")

if __name__ == "__main__":
    asyncio.run(main())
