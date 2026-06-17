"""
11_agentmesh/01_hello_mesh
===========================
Simplest agentmesh example.
- Creates a mesh (in-process, zero deps)
- Subscribes with a wildcard pattern
- Publishes two events from different tenants
- Shows tenant isolation in action
- Prints stats

pip install agentmesh-bus && python main.py
"""
import asyncio
from agentmesh import AgentMesh, AgentEvent


async def main() -> None:
    mesh = AgentMesh()
    await mesh.start()

    received: list[str] = []

    # Wildcard — catches order.created AND order.updated
    @mesh.subscribe("order.*")
    async def handle_any_order(e: AgentEvent) -> None:
        received.append(e.event_type)
        print(f"  [subscriber] {e.event_type} | tenant={e.tenant_id} | {e.data}")

    # Tenant-namespaced — only ACME billing events
    @mesh.subscribe("acme:billing.*")
    async def handle_acme_billing(e: AgentEvent) -> None:
        print(f"  [acme-billing] {e.event_type} | amount=${e.data.get('amount', 0):.2f}")

    print("Publishing events...\n")

    # order.created — matches "order.*"
    await mesh.publish("order.created",
        data={"order_id": "ORD-001", "amount": 149.99, "items": 3},
        publisher_id="shop-agent",
        session_id="sess-001", run_id="run-001",
        tenant_id="acme",
    )

    # order.updated — also matches "order.*"
    await mesh.publish("order.updated",
        data={"order_id": "ORD-001", "status": "processing"},
        publisher_id="warehouse-agent",
        session_id="sess-001", run_id="run-002",
        tenant_id="acme",
    )

    # Tenant-namespaced billing event
    await mesh.publish("acme:billing.charged",
        data={"order_id": "ORD-001", "amount": 149.99, "method": "card"},
        publisher_id="billing-agent",
        session_id="sess-001", run_id="run-003",
        tenant_id="acme",
    )

    # Siemens event — NOT matched by "order.*" subscriber above
    # (would need "siemens:order.*" to catch it)
    await mesh.publish("siemens:order.created",
        data={"order_id": "ORD-DE-001"},
        publisher_id="siemens-shop",
        session_id="sess-002", run_id="run-001",
        tenant_id="siemens",
    )

    await asyncio.sleep(0.1)

    print(f"\n{'='*50}")
    print(f"Events received by 'order.*' subscriber: {len(received)}")
    print(f"Event types: {received}")
    print(f"\nStats: {mesh.stats()}")
    print("\n✓ Wildcard subscription and tenant isolation working")
    await mesh.close()


if __name__ == "__main__":
    asyncio.run(main())
