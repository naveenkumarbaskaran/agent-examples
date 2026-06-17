# 05_first_eval

End-to-end agent evaluation with agenteval-core. Creates an EvalSuite with GoldenTest (output + latency), AdversarialTest (injection/jailbreak), and RegressionTest (baseline) against a MockAgent. Asserts pass rate >= 70%.

Run: `python main.py`
