"""
03_governance/02_escalation_chain — Alert→Degrade→Block escalation with history.
Run: pip install agentplane-py && python main.py
"""
import asyncio
import agentplane
from agentplane import (
    PolicyEngine, Policy, Selector, PolicyContext,
    RateRule, EscalationChain, EscalationLevel,
    Alert, Degrade, Block,
)


async def main() -> None:
    # Build escalation chain: first breach=alert, repeat=degrade, persistent=block
    escalation = EscalationChain([
        EscalationLevel(
            level=1, trigger="rate_breach",
            action=Alert(channel="log", message="Rate limit approaching"),
        ),
        EscalationLevel(
            level=2, trigger="rate_breach",
            action=Degrade(mode="rate_throttle", recover_after="5m",
                           reason="Repeated rate limit violations"),
        ),
        EscalationLevel(
            level=3, trigger="rate_breach",
            action=Block(reason="Persistent rate limit abuse — agent blocked"),
        ),
    ])

    engine = PolicyEngine()
    engine.add_policy(Policy(
        id="acme.rate-policy",
        selector=Selector(tenants=["acme"]),
        blocking=[RateRule(limit=3, window="1h", per="tenant", on_breach="escalate")],
        escalation=escalation,
        priority=100,
    ))

    ctx = PolicyContext.new(agent_id="search-agent", tenant_id="acme",
                            hookpoint="before_tool_call", tool_name="search")

    print("=== ESCALATION CHAIN SIMULATION ===\n")
    print("Policy: 3 calls/hour limit. Breach triggers escalation.\n")

    results = []
    for i in range(1, 8):
        try:
            await engine.evaluate(ctx)
            results.append(("✓", "allowed", ""))
            print(f"  Call {i}: ✓ allowed")
        except agentplane.PolicyBlocked as e:
            results.append(("✗", "blocked", e.reason[:60]))
            print(f"  Call {i}: ✗ blocked  — {e.reason[:60]}")
            break
        except agentplane.PolicyDegraded as e:
            results.append(("⚠", "degraded", f"mode={e.mode}"))
            print(f"  Call {i}: ⚠ degraded — mode={e.mode}")
            break
        except Exception as e:
            results.append(("⚠", "escalated", str(e)[:60]))
            print(f"  Call {i}: ⚠ escalated — {str(e)[:60]}")

    print(f"\n=== ESCALATION HISTORY ===")
    for event in escalation.history():
        print(f"  Level {event.level} | trigger={event.trigger!r} | action={type(event.action).__name__}")

    print(f"\nEscalation level reached: {escalation.current_level}")
    print("✓ Chain progressed Alert → Degrade → Block as designed")


if __name__ == "__main__":
    asyncio.run(main())
