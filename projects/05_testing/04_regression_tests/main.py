"""
05_testing/04_regression_tests
================================
RegressionTest: baseline comparison, mismatch detection, no-baseline capture.
"""
import asyncio
from agenteval import EvalSuite, RegressionTest
from agenteval.fixtures import MockAgent


async def main() -> None:
    agent = MockAgent(
        responses={
            "search":    {"output": "Found 12 results for quarterly revenue", "status": "ok", "count": 12},
            "summarize": {"output": "Summary: revenue up 18% YoY",            "status": "ok"},
            "calculate": {"output": "Result: 84",                              "status": "ok", "value": 84},
        },
        default={"output": "default response", "status": "ok"},
    )

    suite = EvalSuite("regression-tests")

    # Test 1: matches baseline exactly — PASSES
    suite.add(RegressionTest(
        name="search_output_stable",
        inputs={"tool": "search", "query": "quarterly revenue"},
        baseline={"output": "Found 12 results for quarterly revenue", "status": "ok"},
    ))

    # Test 2: baseline mismatch — FAILS (output changed)
    suite.add(RegressionTest(
        name="search_output_changed",
        inputs={"tool": "search", "query": "quarterly revenue"},
        baseline={"output": "Found 10 results"},  # wrong — will fail
    ))

    # Test 3: no baseline — PASSES with "no baseline — capturing"
    suite.add(RegressionTest(
        name="summarize_capture",
        inputs={"tool": "summarize", "text": "annual report"},
        baseline=None,
    ))

    # Test 4: partial baseline match — PASSES
    suite.add(RegressionTest(
        name="calculate_value_stable",
        inputs={"tool": "calculate", "expression": "42 * 2"},
        baseline={"status": "ok"},  # just check status
    ))

    # Test 5: no baseline capture again
    suite.add(RegressionTest(
        name="new_feature_capture",
        inputs={"tool": "search", "query": "new product launch"},
        baseline=None,
    ))

    print(f"Running EvalSuite '{suite.name}' with {len(suite)} tests...\n")
    report = await suite.run(agent=agent)
    report.print()

    print(f"\nPass rate:  {report.pass_rate:.0%}  ({report.passed}/{report.total})")
    # Test 2 is expected to fail (baseline mismatch)
    assert report.passed == 4, f"Expected 4 passed (1 intentional fail), got {report.passed}"
    print("Regression tests validated (1 intentional baseline mismatch detected).\n")


if __name__ == "__main__":
    asyncio.run(main())
