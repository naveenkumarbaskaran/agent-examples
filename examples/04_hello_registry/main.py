"""Hello Registry — simplest agentregistry example."""
# pip install agentregistry-py
from agentregistry import AgentRegistry, AgentManifest

def main() -> None:
    registry = AgentRegistry()
    registry.publish(AgentManifest(
        id="acme.search-agent",
        version="1.0.0",
        description="Searches documents and summarizes results",
        capabilities=["search", "summarize", "read_file"],
        framework="custom",
        tags={"domain": "search", "env": "prod"},
    ))

    agent = registry.get("acme.search-agent")
    print(f"✓ found: {agent.id} v{agent.version}")
    print(f"  capabilities: {agent.capabilities}")

    results = registry.search(capability="search")
    print(f"  search by capability: {len(results)} found")

if __name__ == "__main__":
    main()
