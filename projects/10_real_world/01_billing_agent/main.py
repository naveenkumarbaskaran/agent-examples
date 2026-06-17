"""
10_real_world/01_billing_agent — Enterprise billing agent with full governance.
Tools: charge_card, refund, get_balance, generate_invoice.
Policy: cost budget, rate limit, tool allowlist, audit.
Run: pip install agentplane-py agentguard-lib agenthooks-py && python main.py
"""
import asyncio
import agentplane
from agenthooks import HookRegistry, HookContext, hookpoint
from agentplane import (
    PolicyEngine, Policy, Selector, PolicyContext,
    AllowlistRule, RateRule, CostBudgetRule, RedactRule,
    AuditRule, CostTrackingRule, AlertRule,
)
from agentguard import Guard, Rules


class BillingAgent:
    """Enterprise billing agent with 3-layer governance."""

    TOOLS = {
        "charge_card":      lambda p: {"status": "ok", "txn_id": f"TXN-{id(p)}", "amount": p.get("amount", 0)},
        "refund":           lambda p: {"status": "ok", "ref_id": f"REF-{id(p)}", "amount": p.get("amount", 0)},
        "get_balance":      lambda p: {"status": "ok", "balance": 42_500.00, "currency": "USD"},
        "generate_invoice": lambda p: {"status": "ok", "invoice_id": "INV-2026-0042", "total": p.get("amount", 0)},
        "delete_account":   lambda p: {"status": "error", "message": "not allowed"},
    }

    def __init__(self) -> None:
        self.guard = Guard(rules=[
            Rules.no_prompt_injection(), Rules.no_jailbreak(),
            Rules.tool_allowlist(list(self.TOOLS.keys())[:-1]),  # exclude delete
        ])
        self.registry = HookRegistry()
        hp = hookpoint("billing.call", registries=self.registry)
        self._hp = hp

        @self.registry.implement("billing.call")
        async def audit_log(ctx: HookContext) -> HookContext:
            return ctx.enrich("audited", True).enrich("service", "billing-v2")

        self.engine = PolicyEngine()
        self.cost_tracker = CostTrackingRule(track_per="tenant")
        self.engine.add_policy(Policy(
            id="billing.policy.v2",
            selector=Selector(agents=["billing-agent"], tenants=["acme", "siemens"]),
            blocking=[
                AllowlistRule(tools=list(self.TOOLS.keys())[:-1]),
                RateRule(limit=10, window="1h", per="tenant"),
                CostBudgetRule(max_usd=0.50, window="1d"),
                RedactRule(fields=["card_number", "cvv", "ssn"]),
            ],
            non_blocking=[AuditRule(), self.cost_tracker,
                          AlertRule(channel="log", on="breach")],
            priority=100,
        ))

    async def execute(self, tenant: str, tool: str, params: dict) -> dict:
        # Layer 1: Guard
        g = self.guard.check_tool(tool)
        if not g.passed:
            return {"status": "blocked", "layer": "guard", "reason": g.reason}

        # Layer 2: Hook
        ctx = HookContext.new(session_id=f"{tenant}-session", tenant_id=tenant, tool_name=tool)
        async with self._hp.run(ctx) as enriched:
            # Layer 3: Policy
            pctx = PolicyContext.new(
                agent_id="billing-agent", tenant_id=tenant,
                hookpoint="before_tool_call", tool_name=tool,
                cost_usd=0.002, token_count=50,
                tool_inputs={**params},
            )
            try:
                await self.engine.evaluate(pctx)
            except agentplane.PolicyBlocked as e:
                return {"status": "blocked", "layer": "policy", "reason": e.reason}

        # Execute
        fn = self.TOOLS.get(tool)
        return fn(params) if fn else {"status": "error", "message": "unknown tool"}


async def main() -> None:
    agent = BillingAgent()

    operations = [
        ("acme",    "charge_card",      {"amount": 299.99, "card_number": "4111111111111111"}),
        ("acme",    "get_balance",      {}),
        ("acme",    "generate_invoice", {"amount": 1250.00, "client": "ACME Corp"}),
        ("siemens", "charge_card",      {"amount": 5000.00}),
        ("siemens", "refund",           {"amount": 250.00, "txn_id": "TXN-123"}),
        ("acme",    "delete_account",   {"account": "ACME-001"}),  # blocked by guard
        ("acme",    "charge_card",      {"amount": 99.99}),
        ("acme",    "charge_card",      {"amount": 49.99}),
        ("acme",    "charge_card",      {"amount": 29.99}),
        ("acme",    "charge_card",      {"amount": 19.99}),
    ]

    print("=== BILLING AGENT — ENTERPRISE GOVERNANCE ===\n")
    print(f"{'Tenant':10} {'Tool':18} {'Amount':10} {'Result'}")
    print(f"{'-'*65}")

    for tenant, tool, params in operations:
        result = await agent.execute(tenant, tool, params)
        amount = f"${params.get('amount', '—')}" if "amount" in params else "—"
        if result["status"] == "ok":
            txn = result.get("txn_id") or result.get("invoice_id") or f"${result.get('balance',''):.2f}"
            print(f"  ✓ {tenant:10} {tool:18} {amount:10} {txn}")
        else:
            print(f"  ✗ {tenant:10} {tool:18} {amount:10} [{result['layer']}] {result['reason'][:40]}")
        await asyncio.sleep(0.01)

    print(f"\n=== COST SUMMARY ===")
    for tenant in ["acme", "siemens"]:
        total = agent.cost_tracker.get_total(tenant)
        print(f"  {tenant}: ${total:.4f} spent today")

    print(f"\n✓ Billing agent governance complete")


if __name__ == "__main__":
    asyncio.run(main())
