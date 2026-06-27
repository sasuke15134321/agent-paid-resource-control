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
