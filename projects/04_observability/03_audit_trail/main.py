"""
04_observability/03_audit_trail
==================================
Write 20 audit entries via agentplane AuditTrail, read back,
show filtering by status (allow/block/degrade).
"""
import asyncio
import json
import os
import tempfile
from agentplane import AuditTrail, PolicyContext


async def main() -> None:
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
        audit_path = f.name

    trail = AuditTrail(path=audit_path)

    print("=== Audit Trail Demo ===\n")
    print("Writing 20 audit entries...\n")

    specs = [
        ("search",       "allow",   "allowlist",  ""),
        ("search",       "allow",   "allowlist",  ""),
        ("search",       "allow",   "allowlist",  ""),
        ("drop_table",   "block",   "allowlist",  "tool 'drop_table' not in allowlist"),
        ("search",       "allow",   "allowlist",  ""),
        ("summarize",    "allow",   "allowlist",  ""),
        ("execute_code", "block",   "allowlist",  "tool 'execute_code' not in allowlist"),
        ("search",       "allow",   "allowlist",  ""),
        ("search",       "block",   "rate_limit", "rate limit exceeded: 5 calls per 60s"),
        ("read_file",    "allow",   "allowlist",  ""),
        ("search",       "degrade", "rate_limit", "rate throttle engaged"),
        ("search",       "allow",   "allowlist",  ""),
        ("write_file",   "block",   "allowlist",  "tool 'write_file' not in allowlist"),
        ("summarize",    "allow",   "allowlist",  ""),
        ("search",       "allow",   "allowlist",  ""),
        ("call_api",     "block",   "denylist",   "tool 'call_api' is denied"),
        ("search",       "allow",   "allowlist",  ""),
        ("read_file",    "allow",   "allowlist",  ""),
        ("delete_db",    "block",   "denylist",   "tool 'delete_db' is denied"),
        ("search",       "allow",   "allowlist",  ""),
    ]

    for tool, status, rule, reason in specs:
        ctx = PolicyContext.new(
            agent_id="search-agent",
            tenant_id="acme",
            hookpoint="before_tool_call",
            tool_name=tool,
        )
        await trail.record(
            policy_id="acme.search-policy",
            rule=rule,
            ctx=ctx,
            status=status,
            reason=reason,
        )

    await asyncio.sleep(0.1)

    with open(audit_path, encoding="utf-8") as f:
        entries = [json.loads(line) for line in f if line.strip()]

    print(f"✓ Wrote {len(entries)} entries\n")

    by_status: dict[str, int] = {}
    for e in entries:
        s = e.get("policy.status", "unknown")
        by_status[s] = by_status.get(s, 0) + 1

    print("--- Status Breakdown ---")
    for s, count in sorted(by_status.items()):
        bar = "█" * count
        print(f"  {s:10}: {count:2d} {bar}")

    print("\n--- Blocked Entries ---")
    for e in entries:
        if e.get("policy.status") == "block":
            print(f"  tool={e.get('tool_name'):15} rule={e.get('policy.rule'):12} reason={e.get('policy.reason','')[:45]}")

    print(f"\n--- Degraded Entries ---")
    for e in entries:
        if e.get("policy.status") == "degrade":
            print(f"  tool={e.get('tool_name'):15} reason={e.get('policy.reason','')[:50]}")

    print(f"\nTotal: {len(entries)}  Allow: {by_status.get('allow',0)}  Block: {by_status.get('block',0)}  Degrade: {by_status.get('degrade',0)}")

    os.unlink(audit_path)
    print(f"\n✓ Audit trail demonstrated.\n")


if __name__ == "__main__":
    asyncio.run(main())
