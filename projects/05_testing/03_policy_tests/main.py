"""
05_testing/03_policy_tests
============================
PolicyTest with MockPolicyEngine covering allowed, blocked, and degraded paths.
"""
import asyncio
from agenteval import EvalSuite, PolicyTest
from agenteval.fixtures import MockPolicyEngine


async def main() -> None:
    suite = EvalSuite("policy-tests")

    # Test 1: allowed path — MockPolicyEngine(allow_all=True) returns ctx
    suite.add(PolicyTest(
        name="search_allowed",
        policy_id="acme.search-policy",
        inputs={"agent_id": "search-agent", "tenant_id": "acme", "tool_name": "search"},
        expect_allowed=True,
        expect_blocked=False,
    ))

    # Test 2: allowed path — different tool
    suite.add(PolicyTest(
        name="summarize_allowed",
        policy_id="acme.search-policy",
        inputs={"agent_id": "search-agent", "tenant_id": "acme", "tool_name": "summarize"},
        expect_allowed=True,
        expect_blocked=False,
    ))

    # Test 3: blocked path — MockPolicyEngine(allow_all=False) raises Exception with "PolicyBlocked"
    suite.add(PolicyTest(
        name="drop_table_blocked",
        policy_id="acme.search-policy",
        inputs={"agent_id": "search-agent", "tenant_id": "acme", "tool_name": "drop_table"},
        expect_blocked=True,
    ))

    # Test 4: blocked path — execute_code
    suite.add(PolicyTest(
        name="execute_code_blocked",
        policy_id="acme.search-policy",
        inputs={"agent_id": "search-agent", "tenant_id": "acme", "tool_name": "execute_code"},
        expect_blocked=True,
    ))

    # Test 5: degraded path
    suite.add(PolicyTest(
        name="high_volume_degraded",
        policy_id="acme.search-policy",
        inputs={"agent_id": "search-agent", "tenant_id": "acme", "tool_name": "search"},
        expect_degraded=True,
    ))

    # Run tests 1-2 with allow_all engine
    allow_engine = MockPolicyEngine(allow_all=True)
    block_engine = MockPolicyEngine(allow_all=False, block_reason="PolicyBlocked: tool not in allowlist")
    degrade_engine = MockPolicyEngine(allow_all=False, block_reason="PolicyDegraded: rate throttle")

    allow_suite = EvalSuite("allow-tests")
    allow_suite.add(suite._tests[0])
    allow_suite.add(suite._tests[1])

    block_suite = EvalSuite("block-tests")
    block_suite.add(suite._tests[2])
    block_suite.add(suite._tests[3])

    degrade_suite = EvalSuite("degrade-tests")
    degrade_suite.add(suite._tests[4])

    print("=== Policy Tests ===\n")

    r1 = await allow_suite.run(engine=allow_engine)
    r2 = await block_suite.run(engine=block_engine)
    r3 = await degrade_suite.run(engine=degrade_engine)

    print("Allow engine results:")
    r1.print()
    print("\nBlock engine results:")
    r2.print()
    print("\nDegrade engine results:")
    r3.print()

    total = r1.passed + r2.passed + r3.passed
    all_tests = r1.total + r2.total + r3.total
    print(f"\nOverall: {total}/{all_tests} passed")
    assert total == all_tests, f"Expected all {all_tests} tests to pass"
    print("All policy tests passed.\n")


if __name__ == "__main__":
    asyncio.run(main())
