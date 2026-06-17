"""
11_agentmesh/04_hitl_approval
================================
Human-in-the-loop via agentmesh request/reply pattern.

Flow:
  1. billing-agent needs to approve a large transfer
  2. Publishes human.approval.requested with request_id
  3. Human reviewer receives event, deliberates, publishes response on reply topic
  4. billing-agent receives decision and proceeds or aborts
  5. One transfer times out — shows fallback behaviour

Three scenarios:
  - Approved:  human approves in time
  - Rejected:  human rejects in time
  - Timeout:   human doesn't respond — fallback kicks in

pip install agentmesh-bus && python main.py
"""
import asyncio
from agentmesh import AgentMesh, AgentEvent


class MockHumanReviewer:
    def __init__(self, mesh: AgentMesh) -> None:
        self.mesh = mesh
        self.reviews: list[dict] = []

    async def start(self) -> None:
        @self.mesh.subscribe("human.approval.requested")
        async def review(e: AgentEvent) -> None:
            action = e.data["action"]
            amount = e.data["amount"]
            request_id = e.data["_request_id"]
            auto_decision = e.data.get("_auto_decision")

            if auto_decision is None:
                return  # timeout scenario — don't respond

            await asyncio.sleep(0.05)  # human review time
            decision = auto_decision
            self.reviews.append({
                "action": action, "amount": amount, "approved": decision,
            })
            print(f"  [HUMAN] {'✓ APPROVED' if decision else '✗ REJECTED'} — {action} ${amount:,.2f}")

            await self.mesh.publish(f"_reply.{request_id}",
                data={"approved": decision, "approver": "alice@acme.com",
                      "reason": "within policy" if decision else "exceeds daily limit"},
                publisher_id="alice",
                publisher_type="human",
                session_id=e.session_id, run_id=e.run_id,
            )


async def request_approval(mesh: AgentMesh, action: str, amount: float,
                           auto_decision: bool | None, timeout: float = 2.0) -> dict:
    """Agent requests human approval. Returns decision dict."""
    response = await mesh.request(
        "human.approval.requested",
        data={"action": action, "amount": amount, "_auto_decision": auto_decision},
        publisher_id="billing-agent",
        session_id="sess-001", run_id=f"r-{action[:8]}",
        timeout_s=timeout,
        fallback=None,
    )
    if response is None:
        return {"approved": False, "reason": "timeout — auto-denied", "approver": "system"}
    return response.data


async def main() -> None:
    mesh = AgentMesh()
    await mesh.start()

    reviewer = MockHumanReviewer(mesh)
    await reviewer.start()

    print("=== HUMAN-IN-THE-LOOP APPROVAL ===\n")
    print("Three scenarios: approve, reject, timeout\n")

    transfers = [
        ("wire_transfer",  50_000.0, True,  2.0, "normal approval"),
        ("bulk_payment",  120_000.0, False, 2.0, "rejected by reviewer"),
        ("urgent_payment",  8_500.0, None,  0.3, "timeout — human too slow"),
    ]

    results = []
    for action, amount, auto_decision, timeout, desc in transfers:
        print(f"Request: {action} ${amount:,.2f} ({desc})")
        decision = await request_approval(mesh, action, amount, auto_decision, timeout)
        approved = decision.get("approved", False)
        reason = decision.get("reason", "")
        approver = decision.get("approver", "")
        icon = "✓" if approved else "✗"
        print(f"  {icon} Decision: approved={approved} | {reason} | by={approver}\n")
        results.append({"action": action, "approved": approved})

    print(f"{'='*55}")
    approved_count = sum(1 for r in results if r["approved"])
    print(f"Approved: {approved_count}/{len(results)}")
    print(f"Human reviews completed: {len(reviewer.reviews)}")
    print(f"\n✓ HITL pattern working — approve, reject, timeout all handled")
    await mesh.close()


if __name__ == "__main__":
    asyncio.run(main())
