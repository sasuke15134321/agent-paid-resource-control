# Agent Procurement Gate

Move faster. Spend safer. Leave evidence.

Agent Procurement Gate helps AI agents use paid APIs, x402 resources, MCP tools, repos, models, and memory-backed actions without acting blindly.

It reviews planned external actions before they happen and returns:
- **allow**
- **deny**
- **review_required**
- **escalate**

It also returns the reason, matched rules, evidence, and next action.

---

## When to use this API

Call this endpoint **before** an AI agent executes a paid resource access:

1. Before calling a paid data API
2. Before accessing premium web content via x402
3. Before paying for financial workflow resources
4. When reconciliation or evidence receipts are required after payment

---

## Endpoint

### POST /api/paid-resource/review

**Pricing:** 0.03 USDC via x402 (Base eip155:8453)

**Request:**
```json
{
  "agent_id": "agent_001",
  "resource_url": "https://example.com/api/data",
  "resource_type": "data_api",
  "payment_protocol": "x402",
  "amount": "0.03",
  "currency": "USDC",
  "payment_purpose": "data_access",
  "expected_result": "JSON response with market data"
}
```

**Response fields:**
- `review_id` — unique review identifier
- `decision` — `allow` | `deny` | `review_required`
- `resource_control` — binding, duplicate risk, metadata privacy, fulfillment check
- `agent_guidance` — before/after payment guidance
- `evidence_fields` — fields to record for evidence receipt

---

## Decision logic

| Condition | Decision |
|-----------|----------|
| resource_url empty or invalid | deny |
| amount <= 0 | deny |
| currency not USDC or JPYC | deny |
| metadata contains dangerous patterns | deny |
| all other cases | review_required |

---

## Disclaimer

This is an independent experimental project. Not production-ready, not certified, not an official standard.
Not affiliated with AWS, Coinbase, Arc, Circle, Anthropic, or any payment network.

---

## Scale-Aware Agent Control

Agent Procurement Gate supports scale-aware review of AI agent actions.

Use the right scale for memory, tokens, audit, and throughput.

Review agent actions at the right scale:
- S0: tool_call
- S1: action
- S2: task
- S3: session
- S4: agent
- S5: workflow
- S6: market

At each scale, the gate helps check:
- Goal: is this action aligned with the original purpose?
- Evidence: what is the basis for this action?
- Action: what is being executed or attempted?
- Outcome: what is the result?
- Cost: are token, API cost, latency, and payment proportionate?
- Memory: what context or memory is being used?
- Throughput: does this action help or block overall progress?

---

## Agent Modulor

Agent Modulor is the internal design concept behind Scale-Aware Agent Control.

Just as architectural modulor systems define standard scale units based on human proportion, Agent Modulor defines standard review scales for AI agent judgment: S0 tool_call through S6 market.

The goal is not to audit everything at every scale. The goal is to move between scales when needed:

Scale down when:
- evidence is missing
- execution result is unclear
- failure cause needs to be isolated

Scale up when:
- a specialist agent is stopping too much
- human approval is occurring too often
- token or payment cost is not proportionate to outcome
- overall purpose is being lost

Throughput Anchor: safe actions should proceed. Risky actions should be stopped. Uncertain actions should be reviewed at the right scale.
