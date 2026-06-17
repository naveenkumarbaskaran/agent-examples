"""
08_wire_ai/01_workforce — Multi-agent workforce: orchestrator + 3 specialist agents.
Uses agentplane + agentregistry to govern and discover agents.
Run: pip install agentplane-py agentregistry-py && python main.py
"""
import asyncio
import agentplane
from agentplane import (
    PolicyEngine, Policy, Selector, PolicyContext,
    AllowlistRule, RateRule, AuditRule, CostBudgetRule,
)
from agentregistry import AgentRegistry, AgentManifest


class WorkforceAgent:
    def __init__(self, agent_id: str, role: str, tools: list[str], mock_outputs: dict) -> None:
        self.agent_id = agent_id
        self.role = role
        self.tools = tools
        self._outputs = mock_outputs

    async def run(self, task: str, tool: str) -> dict:
        output = self._outputs.get(tool, f"{self.role} completed: {task[:30]}")
        return {"agent": self.agent_id, "role": self.role, "output": output, "status": "ok"}


async def main() -> None:
    # ── Register agents in the registry ──────────────────────────────────────
    registry = AgentRegistry()
    for manifest in [
        AgentManifest(id="workforce.retriever", version="1.0.0",
                      description="Retrieves relevant documents and data",
                      capabilities=["search", "read_file", "vector_search"],
                      framework="custom", tags={"role": "retriever"}),
        AgentManifest(id="workforce.analyzer", version="1.0.0",
                      description="Analyzes data and generates insights",
                      capabilities=["analyze", "summarize", "calculate"],
                      framework="custom", tags={"role": "analyzer"}),
        AgentManifest(id="workforce.writer",   version="1.0.0",
                      description="Generates reports and documents",
                      capabilities=["write_report", "format", "export"],
                      framework="custom", tags={"role": "writer"}),
    ]:
        registry.publish(manifest)

    # ── Governance policies per role ──────────────────────────────────────────
    engine = PolicyEngine()
    engine.add_policy(Policy(
        id="workforce.retriever.policy",
        selector=Selector(agents=["workforce.retriever"]),
        blocking=[AllowlistRule(tools=["search", "read_file", "vector_search"]),
                  RateRule(limit=50, window="1h"), CostBudgetRule(max_usd=2.0, window="1d")],
        non_blocking=[AuditRule()], priority=100,
    ))
    engine.add_policy(Policy(
        id="workforce.analyzer.policy",
        selector=Selector(agents=["workforce.analyzer"]),
        blocking=[AllowlistRule(tools=["analyze", "summarize", "calculate"]),
                  RateRule(limit=20, window="1h")],
        non_blocking=[AuditRule()], priority=100,
    ))
    engine.add_policy(Policy(
        id="workforce.writer.policy",
        selector=Selector(agents=["workforce.writer"]),
        blocking=[AllowlistRule(tools=["write_report", "format", "export"])],
        non_blocking=[AuditRule()], priority=100,
    ))

    # ── Spawn agents ──────────────────────────────────────────────────────────
    agents = {
        "workforce.retriever": WorkforceAgent(
            "workforce.retriever", "Retriever", ["search", "read_file"],
            {"search": "Found 15 relevant documents about Q1 revenue"}),
        "workforce.analyzer": WorkforceAgent(
            "workforce.analyzer", "Analyzer", ["analyze", "summarize"],
            {"analyze": "Analysis: revenue up 12%, churn down 3%, NPS improved to 72"}),
        "workforce.writer": WorkforceAgent(
            "workforce.writer", "Writer", ["write_report"],
            {"write_report": "Report generated: Q1_2026_Executive_Summary.pdf"}),
    }

    async def run_with_governance(agent_id: str, tool: str, task: str) -> dict:
        ctx = PolicyContext.new(agent_id=agent_id, tenant_id="acme",
                                hookpoint="before_tool_call", tool_name=tool,
                                cost_usd=0.005, token_count=200)
        try:
            await engine.evaluate(ctx)
            return await agents[agent_id].run(task, tool)
        except agentplane.PolicyBlocked as e:
            return {"status": "blocked", "agent": agent_id, "reason": e.reason}

    # ── Orchestrate the workforce ─────────────────────────────────────────────
    print("=== MULTI-AGENT WORKFORCE ===")
    print("Task: Generate Q1 2026 Executive Summary\n")

    steps = [
        ("workforce.retriever", "search",       "Find Q1 2026 revenue data"),
        ("workforce.retriever", "read_file",     "Load financial models"),
        ("workforce.analyzer",  "analyze",       "Analyze revenue trends"),
        ("workforce.analyzer",  "summarize",     "Summarize key insights"),
        ("workforce.writer",    "write_report",  "Write executive summary"),
    ]

    results = []
    for agent_id, tool, task in steps:
        result = await run_with_governance(agent_id, tool, task)
        results.append(result)
        icon = "✓" if result["status"] == "ok" else "✗"
        role = agents[agent_id].role if result["status"] == "ok" else agent_id
        output = result.get("output", result.get("reason", ""))[:60]
        print(f"  {icon} [{role:10}] {tool:15} → {output}")

    # Show registry
    print(f"\n=== REGISTERED AGENTS ===")
    for m in registry.list_all():
        print(f"  {m.id:30} capabilities={m.capabilities[:2]}")

    successful = sum(1 for r in results if r["status"] == "ok")
    print(f"\n  Workflow: {successful}/{len(steps)} steps completed successfully")
    print("✓ Workforce orchestration complete")


if __name__ == "__main__":
    asyncio.run(main())
