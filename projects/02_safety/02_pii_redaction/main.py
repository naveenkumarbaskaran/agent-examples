"""
02_safety/02_pii_redaction — Output guard redacts SSN, email, phone, API keys.
Run: pip install agentguard-lib && python main.py
"""
from agentguard import Guard, Rules


def main() -> None:
    guard = Guard(rules=[
        Rules.no_pii_leakage(),
        Rules.no_credentials(),
    ])

    outputs = [
        ("Clean output",     "Q1 2026 revenue was $4.2M, margin improved 3pp."),
        ("SSN present",      "Customer John Doe, SSN: 123-45-6789, DOB: 1980-01-15."),
        ("Email present",    "Contact support at john.doe@acme.com for follow-up."),
        ("API key present",  "Authentication token: Bearer sk-abc123xyz456secret789"),
        ("Password present", "DB password is s3cr3tP@ssw0rd, rotation every 90 days."),
        ("Mixed PII",        "User bob@company.com (SSN: 987-65-4321) called re: account."),
    ]

    print("=== PII REDACTION IN AGENT OUTPUT ===\n")
    for label, text in outputs:
        r = guard.check_output(text)
        print(f"  [{label}]")
        print(f"    Input:  {text[:70]}")
        if r.filtered:
            print(f"    Output: {(r.text or text)[:70]}")
            print(f"    Filters applied: {r.filters_applied}")
        elif not r.passed:
            print(f"    Status: BLOCKED — {r.reason}")
        else:
            print(f"    Status: CLEAN — passed through unchanged")
        print()


if __name__ == "__main__":
    main()
