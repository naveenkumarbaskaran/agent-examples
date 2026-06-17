# 05_full_stack_events

The complete stack wired together via agentmesh:
- agentmesh: event bus connecting all agents
- agentplane: policy governs what agents can publish
- agentguard: safety on user inputs before they enter the mesh
- agenthooks: enriches events before delivery
- agentregistry: agents discover each other by capability
- agenteval: post-run eval suite validates the event flow

## Install & Run
```bash
pip install agentmesh-bus agentplane-py agentguard-lib agenthooks-py agentregistry-py agenteval-core
python main.py
```
