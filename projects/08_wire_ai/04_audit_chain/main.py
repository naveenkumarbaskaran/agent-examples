"""
08_wire_ai/04_audit_chain — AuditTrail records every agent action, read back + summary.
Run: pip install agentplane-py && python main.py
"""
import asyncio, json, pathlib, tempfile
from agentplane import PolicyContext, AuditTrail


async def main() -> None:
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
        path = f.name

    audit = AuditTrail(path=path)

    # Simulate a full agent session: orchestrator + 3 specialists
    session = [
        # (agent_id, tenant, policy_id, rule, tool, status, reason)
        ("orchestrator",   "acme", "acme.orchestrator", "allowlist",  "plan_workflow",  "allow",  ""),
        ("retriever-agent","acme", "acme.retriever",     "allowlist",  "search",         "allow",  ""),
        ("retriever-agent","acme", "acme.retriever",     "allowlist",  "read_file",      "allow",  ""),
        ("retriever-agent","acme", "acme.retriever",     "rate_limit", "search",         "allow",  ""),
        ("analyzer-agent", "acme", "acme.analyzer",      "allowlist",  "analyze",        "allow",  ""),
        ("analyzer-agent", "acme", "acme.analyzer",      "allowlist",  "summarize",      "allow",  ""),
        ("analyzer-agent", "acme", "acme.analyzer",      "cost_budget","analyze",        "block",  "cost exceeded $2.00"),
        ("writer-agent",   "acme", "acme.writer",        "allowlist",  "write_report",   "allow",  ""),
        ("writer-agent",   "acme", "acme.writer",        "allowlist",  "export",         "allow",  ""),
        ("orchestrator",   "acme", "acme.orchestrator",  "allowlist",  "delete_all",     "block",  "tool not in allowlist"),
    ]

    print("=== AUDIT CHAIN ===\n")
    print("Recording agent workflow...\n")

    for agent_id, tenant, policy_id, rule, tool, status, reason in session:
        ctx = PolicyContext.new(agent_id=agent_id, tenant_id=tenant,
                                hookpoint="before_tool_call", tool_name=tool)
        await audit.record(
            policy_id=policy_id, rule=rule, ctx=ctx,
            status=status, reason=reason, duration_ms=2.5,
        )
        icon = "✓" if status == "allow" else "✗"
        print(f"  {icon} [{agent_id:18}] {tool:15} → {status}")

    await asyncio.sleep(0.1)

    # Read back and analyse
    entries = [json.loads(l) for l in pathlib.Path(path).read_text().splitlines() if l.strip()]

    print(f"\n=== AUDIT ANALYSIS ({len(entries)} entries) ===\n")

    # Group by agent
    by_agent: dict[str, list] = {}
    for e in entries:
        a = e.get("agent_id", "?")
        by_agent.setdefault(a, []).append(e)

    for agent, evts in by_agent.items():
        allowed = sum(1 for e in evts if e.get("policy.status") == "allow")
        blocked  = sum(1 for e in evts if e.get("policy.status") == "block")
        print(f"  {agent:20} {len(evts):2d} actions  ✓{allowed} ✗{blocked}")

    print(f"\n  Blocked actions:")
    for e in entries:
        if e.get("policy.status") == "block":
            print(f"    [{e['agent_id']}] {e.get('tool_name')} — {e.get('policy.reason','')}")

    print(f"\n  Audit file: {path}")
    print(f"  Entries: {len(entries)}")
    pathlib.Path(path).unlink()
    print("\n✓ Audit chain complete — full trace of agent actions recorded")


if __name__ == "__main__":
    asyncio.run(main())
