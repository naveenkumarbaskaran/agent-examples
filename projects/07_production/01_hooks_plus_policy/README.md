# 01_hooks_plus_policy

agenthooks and agentplane wired into a single before_tool_call pipeline. Hook 1 enriches context (region, request_id). Hook 2 enforces agentplane policy. Shows the full lifecycle for allowed and blocked calls.

Run: `python main.py`
