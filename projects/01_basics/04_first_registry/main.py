"""
01_basics/04_first_registry — AgentRegistry: publish, search, version, deprecate.
Run: pip install agentregistry-py && python main.py
"""
from agentregistry import AgentRegistry, AgentManifest, SearchFilter, search


def main() -> None:
    registry = AgentRegistry()

    # Publish 3 agents
    agents = [
        AgentManifest(
            id="acme.search-agent", version="1.0.0",
            description="Searches documents and knowledge bases",
            capabilities=["search", "summarize", "read_file"],
            framework="langgraph",
            tags={"domain": "search", "env": "prod", "tier": "standard"},
        ),
        AgentManifest(
            id="acme.billing-agent", version="2.1.0",
            description="Handles all billing operations for enterprise tenants",
            capabilities=["charge_card", "refund", "get_balance", "generate_invoice"],
            framework="openai",
            tags={"domain": "finance", "env": "prod", "tier": "premium"},
            policies=["acme.billing.v2"],
        ),
        AgentManifest(
            id="acme.support-agent", version="1.3.0",
            description="Customer support and ticket management",
            capabilities=["search", "create_ticket", "escalate", "send_email"],
            framework="crewai",
            tags={"domain": "support", "env": "prod", "tier": "standard"},
        ),
    ]
    for a in agents:
        registry.publish(a)
        print(f"✓ published {a.id} v{a.version}")

    # Get latest
    print(f"\n=== GET LATEST ===")
    billing = registry.get("acme.billing-agent")
    print(f"  {billing.id} v{billing.version} — {billing.description}")
    print(f"  capabilities: {billing.capabilities}")
    print(f"  policies: {billing.policies}")

    # Search by capability
    print(f"\n=== SEARCH ===")
    searchers = registry.search(capability="search")
    print(f"  agents with 'search' capability: {[a.id for a in searchers]}")

    finance = registry.search(tags={"domain": "finance"})
    print(f"  agents in finance domain: {[a.id for a in finance]}")

    langgraph_agents = registry.search(framework="langgraph")
    print(f"  langgraph agents: {[a.id for a in langgraph_agents]}")

    # Publish v2 of search-agent
    print(f"\n=== VERSION LIFECYCLE ===")
    registry.publish(AgentManifest(
        id="acme.search-agent", version="2.0.0",
        description="Search agent with vector support",
        capabilities=["search", "summarize", "read_file", "vector_search"],
        framework="langgraph",
        tags={"domain": "search", "env": "prod", "tier": "premium"},
    ))
    print(f"  published acme.search-agent v2.0.0")
    print(f"  versions: {registry.versions('acme.search-agent')}")
    latest = registry.get("acme.search-agent")
    print(f"  latest: v{latest.version}")
    v1 = registry.get("acme.search-agent", version="1.0.0")
    print(f"  v1.0.0 still accessible: {v1.id} v{v1.version}")

    # Deprecate old version
    deprecated = registry.deprecate("acme.search-agent", "1.0.0")
    print(f"  deprecated v1.0.0: status={deprecated.status}")

    print(f"\n=== REGISTRY SUMMARY ===")
    print(f"  total agents: {registry.count()}")
    active = registry.list_all()
    for a in active:
        print(f"  • {a.id} v{a.version} [{a.status}] — {', '.join(a.capabilities[:3])}")


if __name__ == "__main__":
    main()
