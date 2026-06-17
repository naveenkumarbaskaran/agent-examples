# agent-examples

35 real working projects covering the full agent infrastructure stack — from hello world to production deployments.

No API keys required. All examples use mock agents and run locally with `python main.py`.

## Stack

| Package | Install | Purpose |
|---|---|---|
| `agenthooks-py` | `pip install agenthooks-py` | Hookpoints and extensibility |
| `agentplane-py` | `pip install agentplane-py` | Runtime policy control |
| `agentguard-lib` | `pip install agentguard-lib` | Safety guardrails |
| `agentregistry-py` | `pip install agentregistry-py` | Agent discovery and versioning |
| `agenteval-core` | `pip install agenteval-core` | Agent testing |
| `agentobserve-py` | `pip install agentobserve-py` | Observability dashboard |

---

## Quick Examples

Six single-file quickstarts. Copy, install one package, run.

| File | Package | What it shows |
|---|---|---|
| `examples/01_hello_hooks/main.py` | agenthooks-py | Register a hook, enrich context |
| `examples/02_hello_policy/main.py` | agentplane-py | Create a policy, allow/block |
| `examples/03_hello_guard/main.py` | agentguard-lib | Input/output/tool safety |
| `examples/04_hello_registry/main.py` | agentregistry-py | Publish, search, version agents |
| `examples/05_hello_eval/main.py` | agenteval-core | EvalSuite with golden + adversarial tests |
| `examples/06_hello_observe/main.py` | agentobserve-py | Dashboard snapshot |

```bash
pip install agenthooks-py
python examples/01_hello_hooks/main.py
```

---

## Projects

Each project is self-contained: `main.py` + `requirements.txt` + `README.md`.

```bash
cd projects/01_basics/01_first_hook
pip install -r requirements.txt
python main.py
```

### 01 Basics

| Project | Package(s) | Description |
|---|---|---|
| `01_first_hook` | agenthooks-py | Hook lifecycle, enrichment, blocking |
| `02_first_policy` | agentplane-py | Policy creation, selectors, evaluation |
| `03_first_guard` | agentguard-lib | All guard types: injection, PII, tool |
| `04_first_registry` | agentregistry-py | Publish, search, version, deprecate |
| `05_first_eval` | agenteval-core | EvalSuite: golden, adversarial, regression |

### 02 Safety

| Project | Package(s) | Description |
|---|---|---|
| `01_injection_defense` | agentguard-lib | 6 injection patterns, each blocked |
| `02_pii_redaction` | agentguard-lib | SSN, email, API key, password redaction |
| `03_jailbreak_protection` | agentguard-lib | DAN, developer mode, pretend attacks |
| `04_tool_governance` | agentguard-lib | Allowlist + denylist + combined guard |

### 03 Governance

| Project | Package(s) | Description |
|---|---|---|
| `01_policy_versioning` | agentplane-py | Publish v1/v2/v3, diff, rollback |
| `02_escalation_chain` | agentplane-py | Alert → Degrade → Block escalation |
| `03_degradation_modes` | agentplane-py | All 6 degradation modes + recovery |
| `04_conflict_resolution` | agentplane-py | Most-restrictive vs priority override |

### 04 Observability

| Project | Package(s) | Description |
|---|---|---|
| `01_snapshot` | agentobserve-py | Read audit files, snapshot stats |
| `02_live_dashboard` | agentobserve-py + agentplane-py | Real engine → dashboard |
| `03_audit_trail` | agentplane-py | Write 20 entries, read back, filter |
| `04_metrics` | agentplane-py | Cost tracking + metrics per tenant |

### 05 Testing

| Project | Package(s) | Description |
|---|---|---|
| `01_golden_tests` | agenteval-core | 5 golden tests: output, latency, tool calls |
| `02_adversarial_tests` | agenteval-core | 5 injection patterns, all blocked |
| `03_policy_tests` | agenteval-core + agentplane-py | Allow/block/degrade paths |
| `04_regression_tests` | agenteval-core | Baseline match, mismatch, capture |
| `05_full_suite` | agenteval-core + agentguard-lib + agentplane-py | 12 tests across all types |

### 06 Multi-Tenant

| Project | Package(s) | Description |
|---|---|---|
| `01_tenant_isolation` | agentplane-py | 3 tenants, isolated tool allowlists |
| `02_per_tenant_policies` | agentplane-py | Different rate limits + budgets per tier |
| `03_tenant_lockout` | agentplane-py | PlugBoard: lock tenant, restore, verify |

### 07 Production

| Project | Package(s) | Description |
|---|---|---|
| `01_hooks_plus_policy` | agenthooks-py + agentplane-py | Hook enrichment → policy enforcement |
| `02_full_stack` | agenthooks-py + agentplane-py + agentguard-lib | Guard → Hooks → Policy pipeline |
| `03_production_agent` | all | Complete agent with all layers + eval |

### 08 Wire AI Patterns

| Project | Package(s) | Description |
|---|---|---|
| `01_workforce` | agentplane-py + agentregistry-py | 3-agent workforce with governance |
| `02_hitl_gate` | agentplane-py | HITL escalation with mock reviewer |
| `03_budget_control` | agentplane-py | Cost + token budget exhaustion |
| `04_audit_chain` | agentplane-py | Full session audit trail |

### 09 Advanced

| Project | Package(s) | Description |
|---|---|---|
| `01_plug_unplug` | agentplane-py | 5 agents, unplug 2, restore 1 |
| `02_cost_budgets` | agentplane-py | $0.03/day limit, blocked at exhaustion |
| `03_rate_limiting` | agentplane-py | 5/min limit, 8 calls, 3 blocked |
| `04_api_governance` | agentplane-py | Path + method allowlist/denylist |

### 10 Real World

| Project | Package(s) | Description |
|---|---|---|
| `01_billing_agent` | agentplane-py + agentguard-lib + agenthooks-py | Enterprise billing with full governance |
| `02_sql_agent` | agentplane-py + agentguard-lib | SQL injection defense + read-only enforcement |
| `03_customer_support` | agentplane-py + agentguard-lib + agenthooks-py | PII redaction + session rate limiting |
| `04_data_pipeline` | agentplane-py + agentregistry-py + agenthooks-py | ETL pipeline with registry + degradation |
| `05_multi_agent` | all libraries | 3-agent orchestration: registry + governance + eval |

---

## Run All Examples

```bash
# Install all packages
pip install agenthooks-py agentplane-py agentguard-lib agentregistry-py agenteval-core agentobserve-py

# Run quick examples
for f in examples/*/main.py; do echo "=== $f ==="; python "$f"; echo; done

# Run a project
cd projects/10_real_world/05_multi_agent
pip install -r requirements.txt
python main.py
```

---

Apache 2.0 · Built on the [agent infrastructure stack](https://github.com/naveenkumarbaskaran)
