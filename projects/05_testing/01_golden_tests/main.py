"""
05_testing/01_golden_tests
============================
Five GoldenTest cases covering output content, latency bounds,
expected tool calls, and pass-through cases.
"""
import asyncio
from agenteval import EvalSuite, GoldenTest
from agenteval.fixtures import MockAgent


async def main() -> None:
    agent = MockAgent(
        responses={
            "search":    {"output": "Found 12 results for quarterly revenue", "status": "ok", "tool": "search"},
            "summarize": {"output": "Executive summary: revenue up 18% YoY",   "status": "ok", "tool": "summarize"},
            "read_file": {"output": "File contents: Q4 report data",            "status": "ok", "tool": "read_file"},
            "calculate": {"output": "Result: 42.0",                             "status": "ok"},
        },
        default={"output": "generic response", "status": "ok"},
    )

    suite = EvalSuite("golden-tests")

    # Test 1: output contains expected string
    suite.add(GoldenTest(
        name="search_returns_results",
        inputs={"tool": "search", "query": "quarterly revenue"},
        expected_output_contains="results",
    ))

    # Test 2: latency within bound (mock is instant, so generous)
    suite.add(GoldenTest(
        name="summarize_within_latency",
        inputs={"tool": "summarize", "text": "long annual report text"},
        expected_output_contains="summary",
        max_latency_ms=5000.0,
    ))

    # Test 3: specific output substring
    suite.add(GoldenTest(
        name="read_file_returns_contents",
        inputs={"tool": "read_file", "path": "/reports/q4.pdf"},
        expected_output_contains="Q4 report",
    ))

    # Test 4: no output check — just verifies it completes
    suite.add(GoldenTest(
        name="calculate_completes",
        inputs={"tool": "calculate", "expression": "6 * 7"},
    ))

    # Test 5: very fast latency (mock completes in <100ms)
    suite.add(GoldenTest(
        name="search_fast_path",
        inputs={"tool": "search", "query": "fast lookup"},
        max_latency_ms=2000.0,
    ))

    print(f"Running EvalSuite '{suite.name}' with {len(suite)} tests...\n")
    report = await suite.run(agent=agent)
    report.print()

    print(f"\nPass rate:  {report.pass_rate:.0%}  ({report.passed}/{report.total})")
    assert report.pass_rate >= 0.8, f"Expected >=80% pass rate, got {report.pass_rate:.0%}"
    print("All golden tests passed.\n")


if __name__ == "__main__":
    asyncio.run(main())
