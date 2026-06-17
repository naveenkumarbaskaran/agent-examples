"""
04_observability/01_snapshot
==============================
Write mock agentplane audit JSONL entries, read with Collector,
take a Snapshot, and print all stats.
"""
import json
import os
import tempfile
import time
from agentobserve import ObserveDashboard, Collector


def main() -> None:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False, encoding="utf-8") as f:
        audit_path = f.name
        rows = [
            {"ts": time.time(), "agent_id": "search-agent",  "tenant_id": "acme",    "policy.id": "acme.search",     "policy.rule": "allowlist",  "policy.status": "allow",   "policy.reason": ""},
            {"ts": time.time(), "agent_id": "search-agent",  "tenant_id": "acme",    "policy.id": "acme.search",     "policy.rule": "allowlist",  "policy.status": "allow",   "policy.reason": ""},
            {"ts": time.time(), "agent_id": "search-agent",  "tenant_id": "acme",    "policy.id": "acme.search",     "policy.rule": "rate_limit", "policy.status": "block",   "policy.reason": "rate exceeded"},
            {"ts": time.time(), "agent_id": "billing-agent", "tenant_id": "siemens", "policy.id": "siemens.billing", "policy.rule": "allowlist",  "policy.status": "allow",   "policy.reason": ""},
            {"ts": time.time(), "agent_id": "billing-agent", "tenant_id": "siemens", "policy.id": "siemens.billing", "policy.rule": "allowlist",  "policy.status": "allow",   "policy.reason": ""},
            {"ts": time.time(), "agent_id": "billing-agent", "tenant_id": "siemens", "policy.id": "siemens.billing", "policy.rule": "denylist",   "policy.status": "block",   "policy.reason": "denied tool"},
            {"ts": time.time(), "agent_id": "report-agent",  "tenant_id": "acme",    "policy.id": "acme.search",     "policy.rule": "rate_limit", "policy.status": "degrade", "policy.reason": "throttle"},
        ]
        for row in rows:
            f.write(json.dumps(row) + "\n")

    try:
        collector = Collector(agentplane_audit=audit_path)
        agents   = collector.collect_agents()
        policies = collector.collect_policies()

        print("=== Observability Snapshot ===\n")
        print(f"Agents ({len(agents)}):")
        for a in agents:
            print(f"  {a.agent_id:20} tenant={str(a.tenant_id):10} status={a.status:10} evals={a.eval_count} blocks={a.block_count}")

        print(f"\nPolicies ({len(policies)}):")
        for p in policies:
            print(f"  {p.policy_id:28} evals={p.total_evals} blocks={p.blocks} degrades={p.degrades}")

        dash = ObserveDashboard(collector=collector)
        snap = dash.snapshot()

        print(f"\n--- Snapshot Summary ---")
        print(f"  agent_count:  {snap.agent_count}")
        print(f"  active_count: {snap.active_count}")
        print(f"  total_evals:  {snap.total_evals}")
        print(f"  total_blocks: {snap.total_blocks}")
        print(f"  block_rate:   {snap.block_rate:.1%}")

        print(f"\n--- Dashboard Output ---")
        dash.print_snapshot()

    finally:
        os.unlink(audit_path)


if __name__ == "__main__":
    main()
