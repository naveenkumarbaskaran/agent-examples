"""
11_agentmesh/02_multi_agent_events
====================================
Four agents connected via events:
  shop-agent       → order.created
  inventory-agent  → inventory.reserved  (caused_by: order.created)
  billing-agent    → payment.charged     (caused_by: inventory.reserved)
  notify-agent     → notification.sent   (caused_by: payment.charged)

Each event carries caused_by_event_id, forming a full causality chain.
At the end we reconstruct the chain from the event store.

pip install agentmesh-bus && python main.py
"""
import asyncio
import tempfile
from agentmesh import AgentMesh, AgentEvent


async def main() -> None:
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
        store_path = f.name

    mesh = AgentMesh(store_path=store_path)
    await mesh.start()

    chain: list[tuple[str, str, str | None]] = []  # (event_type, agent, caused_by)

    @mesh.subscribe("order.created")
    async def inventory_agent(e: AgentEvent) -> None:
        chain.append((e.event_type, "inventory-agent", e.caused_by_event_id))
        print(f"  [inventory]  ← {e.event_type} | reserving stock for {e.data['order_id']}")
        await mesh.publish("inventory.reserved",
            data={**e.data, "warehouse": "EU-WEST-1", "reserved_qty": e.data["qty"]},
            publisher_id="inventory-agent",
            session_id=e.session_id, run_id=e.run_id,
            tenant_id=e.tenant_id,
            caused_by_event_id=e.event_id,   # ← link to parent
        )

    @mesh.subscribe("inventory.reserved")
    async def billing_agent(e: AgentEvent) -> None:
        chain.append((e.event_type, "billing-agent", e.caused_by_event_id))
        print(f"  [billing]    ← {e.event_type} | charging ${e.data['amount']:.2f}")
        await mesh.publish("payment.charged",
            data={**e.data, "txn_id": "TXN-2026-001", "status": "ok"},
            publisher_id="billing-agent",
            session_id=e.session_id, run_id=e.run_id,
            tenant_id=e.tenant_id,
            caused_by_event_id=e.event_id,
        )

    @mesh.subscribe("payment.charged")
    async def notify_agent(e: AgentEvent) -> None:
        chain.append((e.event_type, "notify-agent", e.caused_by_event_id))
        print(f"  [notify]     ← {e.event_type} | emailing customer")
        await mesh.publish("notification.sent",
            data={**e.data, "channel": "email", "template": "order_confirmed"},
            publisher_id="notify-agent",
            session_id=e.session_id, run_id=e.run_id,
            tenant_id=e.tenant_id,
            caused_by_event_id=e.event_id,
        )

    @mesh.subscribe("notification.sent")
    async def audit_agent(e: AgentEvent) -> None:
        chain.append((e.event_type, "audit-agent", e.caused_by_event_id))
        print(f"  [audit]      ← {e.event_type} | workflow complete ✓")

    print("=== MULTI-AGENT EVENT WORKFLOW ===\n")
    print("Trigger: shop-agent publishes order.created\n")

    root_event = await mesh.publish("order.created",
        data={"order_id": "ORD-2026-001", "amount": 299.99, "qty": 2, "sku": "PROD-42"},
        publisher_id="shop-agent",
        session_id="sess-001", run_id="run-001",
        tenant_id="acme",
    )

    await asyncio.sleep(0.3)

    print(f"\n{'='*55}")
    print(f"Workflow steps completed: {len(chain)}")
    print(f"\nCausality chain (reconstructed from event IDs):")
    print(f"  order.created (root: {root_event.event_id[:8]}...)")
    for event_type, agent, caused_by in chain:
        print(f"    └─ {event_type:30} [{agent}]")

    # Replay the full workflow from store
    print(f"\nReplay from persistent store:")
    topics = ["order.created", "inventory.reserved", "payment.charged",
              "notification.sent"]
    for topic in topics:
        events = [e async for e in mesh.replay(topic)]
        if events:
            e = events[0]
            chain_note = f"← caused by {e.caused_by_event_id[:8]}..." if e.caused_by_event_id else "← root"
            print(f"  {topic:35} {chain_note}")

    await mesh.close()


if __name__ == "__main__":
    asyncio.run(main())
