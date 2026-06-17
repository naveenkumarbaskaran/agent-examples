"""
10_real_world/04_data_pipeline — Data pipeline agent with registry tracking + degradation.
Tools: ingest, transform, validate, export.
Policy degrades on high error rate. Registry tracks versions.
Run: pip install agentplane-py agentregistry-py agenthooks-py && python main.py
"""
import asyncio
import random
import agentplane
from agenthooks import HookRegistry, HookContext, hookpoint
from agentplane import (
    PolicyEngine, Policy, Selector, PolicyContext,
    AllowlistRule, AuditRule, DegradationMode,
)
from agentregistry import AgentRegistry, AgentManifest


class DataPipelineAgent:
    """Data pipeline agent with version registry and degradation on errors."""

    def __init__(self, error_rate: float = 0.0) -> None:
        self._error_rate = error_rate
        self._errors = 0
        self._runs = 0

        # Registry — track pipeline versions
        self.registry = AgentRegistry()
        for version, desc in [("1.0.0", "Initial pipeline"), ("1.1.0", "Added validation"), ("2.0.0", "Parallel ingest")]:
            self.registry.publish(AgentManifest(
                id="pipeline.etl-agent", version=version,
                description=desc, capabilities=["ingest", "transform", "validate", "export"],
                framework="custom", tags={"pipeline": "etl", "env": "prod"},
            ))
        self.registry.deprecate("pipeline.etl-agent", "1.0.0")

        # Hooks
        self.registry_hooks = HookRegistry()
        hp = hookpoint("pipeline.step", registries=self.registry_hooks)
        self._hp = hp

        @self.registry_hooks.implement("pipeline.step")
        async def track_step(ctx: HookContext) -> HookContext:
            return ctx.enrich("pipeline_version", "2.0.0").enrich("run_id", f"run-{id(ctx)}")

        # Policy
        self.engine = PolicyEngine()
        self.engine.add_policy(Policy(
            id="pipeline.policy",
            selector=Selector(agents=["pipeline.etl-agent"]),
            blocking=[AllowlistRule(tools=["ingest", "transform", "validate", "export"])],
            non_blocking=[AuditRule()],
        ))

    async def run_step(self, step: str, data: dict) -> dict:
        self._runs += 1

        # Hook enrichment
        ctx = HookContext.new(session_id=f"run-{self._runs}", tool_name=step)
        async with self._hp.run(ctx) as enriched:
            # Policy check
            pctx = PolicyContext.new(agent_id="pipeline.etl-agent", tenant_id="acme",
                                     hookpoint="before_tool_call", tool_name=step)
            try:
                await self.engine.evaluate(pctx)
            except agentplane.PolicyBlocked as e:
                return {"status": "blocked", "step": step, "reason": e.reason}

        # Simulate step execution with error rate
        if random.random() < self._error_rate:
            self._errors += 1
            return {"status": "error", "step": step, "error": f"Simulated error in {step}"}

        results = {
            "ingest":    {"status": "ok", "records": len(data.get("files", [])) * 1000, "step": step},
            "transform": {"status": "ok", "transformed": data.get("records", 0), "nulls_removed": 42, "step": step},
            "validate":  {"status": "ok", "valid": data.get("transformed", 0), "invalid": 3, "step": step},
            "export":    {"status": "ok", "exported": data.get("valid", 0), "destination": "s3://acme-dw/", "step": step},
        }
        return results.get(step, {"status": "ok", "step": step})


async def main() -> None:
    agent = DataPipelineAgent(error_rate=0.0)  # clean run

    print("=== DATA PIPELINE AGENT ===\n")

    # Show registry state
    print("Pipeline Registry:")
    for m in agent.registry.list_all():
        print(f"  {m.id} v{m.version} [{m.status}]")
    latest = agent.registry.get("pipeline.etl-agent")
    print(f"  Using: v{latest.version} ({latest.description})\n")

    # Run pipeline
    print("Running ETL Pipeline:\n")
    pipeline = [
        ("ingest",    {"files": ["sales_q1.csv", "sales_q2.csv", "sales_q3.csv"]}),
        ("transform", {"records": 3000}),
        ("validate",  {"transformed": 2958}),
        ("export",    {"valid": 2955}),
    ]

    ctx_data: dict = {}
    for step, params in pipeline:
        result = await agent.run_step(step, {**params, **ctx_data})
        ctx_data.update(result)
        if result["status"] == "ok":
            details = {k: v for k, v in result.items() if k not in ("status", "step")}
            print(f"  ✓ {step:12} {details}")
        else:
            print(f"  ✗ {step:12} ERROR: {result.get('error') or result.get('reason')}")

    # Degradation demo
    print(f"\n=== HIGH ERROR RATE → DEGRADATION ===\n")
    noisy_agent = DataPipelineAgent(error_rate=0.8)
    errors = 0
    for i in range(5):
        r = await noisy_agent.run_step("ingest", {"files": [f"batch_{i}.csv"]})
        if r["status"] == "error":
            errors += 1

    print(f"  Error rate: {errors}/5 runs")
    if errors >= 3:
        noisy_agent.engine.degrade("pipeline.etl-agent", DegradationMode.READ_ONLY,
                                   reason="High error rate — degrading to read-only")
        print(f"  ⚠ Degraded to READ_ONLY due to high error rate")
        print(f"  Agent degraded: {noisy_agent.engine.is_degraded('pipeline.etl-agent')}")

    print(f"\n  Pipeline versions: {agent.registry.versions('pipeline.etl-agent')}")
    print(f"\n✓ Data pipeline agent complete")


if __name__ == "__main__":
    asyncio.run(main())
