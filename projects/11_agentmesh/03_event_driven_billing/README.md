# 03_event_driven_billing

Billing agent reacts to order events. agentplane policy governs which events the agent can
publish. AgentGuard blocks injection in order notes. Shows full governance on event publishing.

## Install & Run
```bash
pip install agentmesh-bus agentplane-py agentguard-lib
python main.py
```
