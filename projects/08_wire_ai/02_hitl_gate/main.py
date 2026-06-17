"""
08_wire_ai/02_hitl_gate — Human-in-the-loop via EscalationChain with HITL action.
Simulates approval flow with mock reviewer.
Run: pip install agentplane-py && python main.py
"""
import asyncio
import agentplane
from agentplane import (
    PolicyEngine, Policy, Selector, PolicyContext,
    RateRule, EscalationChain, EscalationLevel,
    Alert, Degrade, Block,
)


class MockHITLReviewer:
    """Simulates a human reviewer who approves or rejects escalated actions."""

    def __init__(self, auto_approve: bool = True) -> None:
        self._auto_approve = auto_approve
        self.reviews: list[dict] = []

    async def review(self, agent_id: str, action: str, context: str) -> bool:
        review = {"agent": agent_id, "action": action, "context": context, "approved": self._auto_approve}
        self.reviews.append(review)
        decision = "APPROVED" if self._auto_approve else "REJECTED"
        print(f"  [HITL] Reviewer: {decision} — {context[:50]}")
        await asyncio.sleep(0.01)  # Simulate review time
        return self._auto_approve


async def main() -> None:
    reviewer = MockHITLReviewer(auto_approve=True)

    # HITL gate: high-cost/high-risk actions require human approval
    async def hitl_gate(ctx: PolicyContext, action_desc: str) -> bool:
        print(f"\n  ⚠  HITL Gate triggered for {ctx.agent_id}")
        print(f"     Action: {action_desc}")
        approved = await reviewer.review(ctx.agent_id, action_desc, f"tenant={ctx.tenant_id}")
        return approved

    engine = PolicyEngine()

    # Low threshold to trigger escalation quickly for demo
    escalation = EscalationChain([
        EscalationLevel(level=1, trigger="high_cost",
                        action=Alert(channel="log", message="High-cost operation detected")),
        EscalationLevel(level=2, trigger="high_cost",
                        action=Degrade(mode="human_loop", recover_after="5m")),
        EscalationLevel(level=3, trigger="high_cost",
                        action=Block(reason="Requires human approval — escalated to reviewer")),
    ])

    engine.add_policy(Policy(
        id="acme.hitl-policy",
        selector=Selector(tenants=["acme"]),
        blocking=[RateRule(limit=2, window="1h", per="tenant", on_breach="escalate")],
        escalation=escalation,
    ))

    print("=== HITL GATE SIMULATION ===\n")
    print("Policy: 2 calls/hour. On breach: Alert → Degrade → Block (HITL)\n")

    high_risk_operations = [
        ("billing-agent", "charge_card",  "$50,000 enterprise renewal"),
        ("billing-agent", "charge_card",  "$12,500 professional services"),
        ("billing-agent", "wire_transfer", "$250,000 vendor payment"),    # triggers escalation
        ("billing-agent", "refund",        "$5,000 dispute resolution"),
    ]

    for agent_id, tool, description in high_risk_operations:
        ctx = PolicyContext.new(
            agent_id=agent_id, tenant_id="acme",
            hookpoint="before_tool_call", tool_name=tool,
            cost_usd=50.0, token_count=100,
        )
        print(f"Operation: {description}")
        try:
            await engine.evaluate(ctx)
            print(f"  ✓ {tool} — proceeded normally")
        except agentplane.PolicyBlocked as e:
            # Trigger HITL review
            approved = await hitl_gate(ctx, description)
            if approved:
                print(f"  ✓ {tool} — proceeded after HITL approval")
            else:
                print(f"  ✗ {tool} — rejected by HITL reviewer")
        except agentplane.PolicyDegraded as e:
            print(f"  ⚠ {tool} — degraded (mode={e.mode}), awaiting HITL")
        except Exception as e:
            print(f"  ⚠ {tool} — escalated: {str(e)[:60]}")
        print()

    print(f"HITL Reviews performed: {len(reviewer.reviews)}")
    for r in reviewer.reviews:
        print(f"  {'✓' if r['approved'] else '✗'} {r['agent']} — {r['action']}")

    print(f"\n✓ HITL gate working — escalations reviewed and decided")


if __name__ == "__main__":
    asyncio.run(main())
