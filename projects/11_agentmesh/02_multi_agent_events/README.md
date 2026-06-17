# 02_multi_agent_events

Three agents connected by events. order.created → inventory.reserved → payment.charged → notification.sent.
Shows causality chain — each event carries caused_by_event_id linking to its parent.

## Install & Run
```bash
pip install agentmesh-bus
python main.py
```
