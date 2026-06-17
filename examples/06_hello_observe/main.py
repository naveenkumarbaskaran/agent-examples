"""Hello Observe — simplest agentobserve-py example."""
# pip install agentobserve-py
from agentobserve import ObserveDashboard, Collector

def main() -> None:
    # Works with no running agents — shows empty state gracefully
    collector = Collector(
        agentplane_audit="~/.agentplane/audit.jsonl",
        agenthooks_audit="~/.agenthooks/audit.jsonl",
    )
    dash = ObserveDashboard(collector=collector)
    snap = dash.snapshot()

    print(f"Agents seen:      {snap.agent_count}")
    print(f"Active:           {snap.active_count}")
    print(f"Degraded:         {snap.degraded_count}")
    print(f"Policy evals:     {snap.total_evals}")
    print(f"Block rate:       {snap.block_rate:.1%}")
    print(f"Hook executions:  {snap.total_hook_executions}")

    dash.print_snapshot()

if __name__ == "__main__":
    main()
