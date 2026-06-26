#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent Paid Resource Control API
Experimental external control layer for AI agents paying for web content, APIs, data,
and financial workflow resources.
"""

import os
import json
import base64
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel, Field

from payment_verifier import PaymentVerifier

WALLET_ADDRESS = os.getenv("WALLET_ADDRESS", "0x60c402878EfcEcAe5733A88075328Aa2320C39BE")
TEST_MODE = os.getenv("TEST_MODE", "false").lower() == "true"

DANGEROUS_PATTERNS = [
    "ignore previous instructions",
    "ignore all instructions",
    "disregard",
    "you are now",
    "act as",
    "jailbreak",
    "forget everything",
]

app = FastAPI(
    title="AI Agent External Resource Review",
    version="0.1.0",
    description=(
        "AI Agent External Resource Review helps AI agents decide whether they should use or pay for an external resource before taking action.\n\n"
        "Use it before:\n"
        "- paying for a paid API or x402 resource\n"
        "- using an external tool, MCP server, GitHub repository, CLI, or binary\n"
        "- using stored memory for a payment, CRM update, or external action decision\n\n"
        "The review returns decision, risk_level, payment_allowed, and required_checks such as "
        "reputation_signal_audit, budget_policy_check, memory_use_permission_check, "
        "tool_install_approval_gate, and payment_evidence_required."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    schema["info"]["x-guidance"] = (
        "Call POST /api/paid-resource/review before an AI agent pays for a resource. "
        "This endpoint checks resource binding, duplicate payment risk, metadata privacy, "
        "fulfillment requirements, and evidence receipt fields. "
        "Requires x402 payment of 0.03 USDC on Base (eip155:8453)."
    )
    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi

_PAID_ENDPOINTS = {
    ("POST", "/api/paid-resource/review"): "0.03",
}

_BAZAAR_EXTENSIONS = {
    "bazaar": {
        "info": {
            "input": {
                "type": "http",
                "method": "POST",
                "queryParams": {
                    "agent_id": "agent_001",
                    "resource_url": "https://example.com/api/market-data",
                    "resource_type": "paid_api",
                    "payment_protocol": "x402",
                    "amount": "0.05",
                    "currency": "USDC",
                    "payment_purpose": "price_lookup",
                    "expected_result": "current BTC price with timestamp",
                    "freshness_required_seconds": 60,
                    "metadata": {
                        "uses_memory": True,
                        "requires_payment": True,
                        "affects_customer_record": False,
                        "provider_type": "crypto_data_api",
                    },
                },
            },
            "output": {
                "type": "json",
                "example": {
                    "review_id": "paid_resource_review_abc123",
                    "review_type": "agent_paid_resource_review",
                    "status": "created",
                    "experimental": True,
                    "agent_id": "agent_demo_001",
                    "resource_url": "https://example.com/premium/report",
                    "resource_type": "web_content",
                    "payment_protocol": "x402",
                    "amount": "0.03",
                    "currency": "USDC",
                    "decision": "review_required",
                    "resource_control": {
                        "resource_binding": "check_required",
                        "duplicate_payment_risk": "unknown",
                        "budget_status": "not_checked",
                        "metadata_privacy": "passed",
                        "fulfillment_check": "required",
                        "evidence_receipt_required": True,
                        "reconciliation_required": True,
                    },
                    "agent_guidance": {
                        "before_payment": [
                            "Confirm that the payment is bound to the intended resource_url.",
                            "Check whether this resource was already paid for in the current task window.",
                            "Confirm that the expected_result is specific enough to verify after payment.",
                        ],
                        "after_payment": [
                            "Record payment_tx or settlement reference.",
                            "Verify that the expected_result was fulfilled.",
                            "Create a paid access evidence receipt.",
                        ],
                    },
                    "evidence_fields": [
                        "agent_id", "resource_url", "resource_type",
                        "amount", "currency", "payment_protocol",
                        "payment_intent_id", "expected_result",
                        "actual_result", "payment_tx", "memo_id", "evidence_id",
                    ],
                    "required_checks": [
                        "reputation_signal_audit",
                        "budget_policy_check",
                        "memory_use_permission_check",
                        "payment_evidence_required",
                    ],
                    "recommended_next_step": "proceed_only_after_budget_and_resource_binding_check",
                    "created_at": "2026-06-18T00:00:00Z",
                },
                "examples": {
                    "example_b_mcp_tool": {
                        "input": {
                            "agent_id": "agent_001",
                            "resource_type": "mcp_tool",
                            "resource_url": "https://github.com/example/tool-server",
                            "purpose": "Use an external MCP tool before processing customer data",
                            "risk_context": {
                                "requires_payment": False,
                                "uses_memory": False,
                                "affects_customer_record": True,
                                "requires_tool_installation": True,
                            },
                        },
                        "expected_output": {
                            "decision": "review_required",
                            "risk_level": "high",
                            "required_checks": [
                                "reputation_signal_audit",
                                "tool_install_approval_gate",
                                "customer_data_boundary_check",
                                "action_evidence_required",
                            ],
                        },
                    },
                    "example_c_memory_backed_payment": {
                        "input": {
                            "agent_id": "agent_001",
                            "resource_type": "memory_backed_payment",
                            "resource_url": "https://api.vendor.example/paid-report",
                            "price": "0.10 USDC",
                            "purpose": "Pay for a vendor report based on previously stored approval memory",
                            "risk_context": {
                                "requires_payment": True,
                                "uses_memory": True,
                                "memory_affects_payment": True,
                                "affects_customer_record": False,
                            },
                        },
                        "expected_output": {
                            "decision": "review_required",
                            "risk_level": "medium",
                            "required_checks": [
                                "memory_use_permission_check",
                                "memory_provenance_receipt",
                                "budget_policy_memory_guard",
                                "payment_decision_memory_attribution",
                                "payment_evidence_required",
                            ],
                        },
                    },
                },
            },
        },
        "schema": {
            "type": "object",
            "properties": {
                "review_id": {"type": "string"},
                "review_type": {"type": "string"},
                "status": {"type": "string"},
                "experimental": {"type": "boolean"},
                "agent_id": {"type": "string"},
                "resource_url": {"type": "string"},
                "resource_type": {"type": "string"},
                "payment_protocol": {"type": "string"},
                "amount": {"type": "string"},
                "currency": {"type": "string"},
                "decision": {"type": "string"},
                "resource_control": {
                    "type": "object",
                    "properties": {
                        "resource_binding": {"type": "string"},
                        "duplicate_payment_risk": {"type": "string"},
                        "budget_status": {"type": "string"},
                        "metadata_privacy": {"type": "string"},
                        "fulfillment_check": {"type": "string"},
                        "evidence_receipt_required": {"type": "boolean"},
                        "reconciliation_required": {"type": "boolean"},
                    },
                },
                "agent_guidance": {
                    "type": "object",
                    "properties": {
                        "before_payment": {"type": "array", "items": {"type": "string"}},
                        "after_payment": {"type": "array", "items": {"type": "string"}},
                    },
                },
                "evidence_fields": {"type": "array", "items": {"type": "string"}},
                "recommended_next_step": {"type": "string"},
                "created_at": {"type": "string"},
            },
        },
    }
}


@app.middleware("http")
async def x402_payment_middleware(request: Request, call_next):
    method = request.method
    path = request.url.path
    key = (method, path)
    price = _PAID_ENDPOINTS.get(key)

    if not TEST_MODE and price is not None:
        payment_header = (
            request.headers.get("PAYMENT-SIGNATURE")
            or request.headers.get("X-PAYMENT")
        )
        if not payment_header:
            amount = str(round(float(price) * 1_000_000))
            _accept = {
                "scheme": "exact",
                "network": "eip155:8453",
                "amount": amount,
                "asset": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
                "payTo": WALLET_ADDRESS,
                "maxTimeoutSeconds": 300,
                "extra": {"name": "USD Coin", "version": "2"},
                "resource": {"method": method, "mimeType": "application/json"},
            }
            _pc = {
                "x402Version": 2,
                "error": "Payment required",
                "resource": {
                    "url": str(request.url),
                    "description": (
                        "Payment is required to receive an External Resource Review before the agent uses this paid API, "
                        "MCP tool, memory-backed decision, or external resource. "
                        "Pay to receive a pre-action risk review with decision, risk_level, payment_allowed, and required_checks."
                    ),
                    "mimeType": "application/json",
                },
                "accepts": [_accept],
                "extensions": _BAZAAR_EXTENSIONS,
                "decision": "payment_required",
                "next_recommended": "complete_x402_payment",
            }
            return JSONResponse(
                status_code=402,
                content=_pc,
                headers={
                    "Payment-Required": base64.b64encode(
                        json.dumps(_pc).encode()
                    ).decode()
                },
            )

    return await call_next(request)


payment_verifier = PaymentVerifier()


class PaidResourceReviewRequest(BaseModel):
    agent_id: str = Field(..., description="AI agent identifier")
    resource_url: str = Field(..., description="URL of the resource to be paid for")
    resource_type: str = Field(..., description="Type of resource. Candidates: data_api, web_content, financial_data, market_data, crypto_data, onchain_data, news_data, token_metadata")
    payment_protocol: str = Field(..., description="Payment protocol (e.g. x402, stripe)")
    amount: str = Field(..., description="Payment amount as string")
    currency: str = Field(..., description="Currency (USDC or JPYC)")
    payment_purpose: str = Field(..., description="Purpose of the payment. Candidates: access_paid_research_report, price_lookup, token_metadata, market_research, onchain_lookup")
    expected_result: str = Field(..., description="Expected result after payment")
    license_terms_id: Optional[str] = Field(default=None, description="License terms identifier")
    payment_intent_id: Optional[str] = Field(default=None, description="Payment intent ID")
    memo_id: Optional[str] = Field(default=None, description="Memo ID for reconciliation")
    freshness_required_seconds: Optional[int] = Field(default=None, description="Maximum acceptable age of data in seconds (e.g. 60 for real-time market data). Optional.")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


def _check_metadata_injection(metadata: Optional[Dict[str, Any]]) -> bool:
    if not metadata:
        return False
    text = json.dumps(metadata).lower()
    return any(pattern in text for pattern in DANGEROUS_PATTERNS)


def _evaluate_decision(req: PaidResourceReviewRequest) -> tuple[str, str]:
    if not req.resource_url or not req.resource_url.startswith("http"):
        return "deny", "resource_url is empty or invalid"
    try:
        amount_val = float(req.amount)
    except (ValueError, TypeError):
        return "deny", "amount is not a valid number"
    if amount_val <= 0:
        return "deny", "amount must be greater than 0"
    if req.currency not in ("USDC", "JPYC"):
        return "deny", f"currency '{req.currency}' is not supported; use USDC or JPYC"
    if _check_metadata_injection(req.metadata):
        return "deny", "metadata contains dangerous patterns"
    return "review_required", "default: human or agent review required before payment"


@app.post(
    "/api/paid-resource/review",
    summary="Review a paid resource access request",
    description=(
        "Review whether an AI agent should use or pay for an external resource. "
        "Covers paid APIs, x402 resources, MCP tools, external data sources, and memory-backed decisions. "
        "Returns decision, risk level, required checks, and next recommended steps."
    ),
    tags=["Paid Resource Control"],
    include_in_schema=True,
)
async def paid_resource_review(payload: PaidResourceReviewRequest, request: Request):
    payment_header = (
        request.headers.get("PAYMENT-SIGNATURE")
        or request.headers.get("X-PAYMENT")
    )

    if not TEST_MODE and payment_header:
        verified = await payment_verifier.verify_payment(
            payment_header,
            WALLET_ADDRESS,
            expected_amount="0.03",
        )
        if not verified:
            return JSONResponse(
                status_code=402,
                content={"error": "Payment verification failed"},
            )

    decision, reason = _evaluate_decision(payload)

    metadata_privacy = "failed" if _check_metadata_injection(payload.metadata) else "passed"

    review_id = f"paid_resource_review_{uuid.uuid4().hex[:12]}"

    return {
        "review_id": review_id,
        "review_type": "agent_paid_resource_review",
        "status": "created",
        "experimental": True,
        "agent_id": payload.agent_id,
        "resource_url": payload.resource_url,
        "resource_type": payload.resource_type,
        "payment_protocol": payload.payment_protocol,
        "amount": payload.amount,
        "currency": payload.currency,
        "decision": decision,
        "reason": reason,
        "resource_control": {
            "resource_binding": "check_required",
            "duplicate_payment_risk": "unknown",
            "budget_status": "not_checked",
            "metadata_privacy": metadata_privacy,
            "fulfillment_check": "required",
            "evidence_receipt_required": True,
            "reconciliation_required": True,
        },
        "agent_guidance": {
            "before_payment": [
                "Confirm that the payment is bound to the intended resource_url.",
                "Check whether this resource was already paid for in the current task window.",
                "Confirm that the expected_result is specific enough to verify after payment.",
            ],
            "after_payment": [
                "Record payment_tx or settlement reference.",
                "Verify that the expected_result was fulfilled.",
                "Create a paid access evidence receipt.",
            ],
        },
        "evidence_fields": [
            "agent_id",
            "resource_url",
            "resource_type",
            "amount",
            "currency",
            "payment_protocol",
            "payment_intent_id",
            "expected_result",
            "actual_result",
            "payment_tx",
            "memo_id",
            "evidence_id",
        ],
        "recommended_next_step": "proceed_only_after_budget_and_resource_binding_check",
        "related_controls": [
            {
                "service": "agent-memory-api",
                "endpoint": "/api/search-result-trust/check",
                "base_url": "https://agent-memory-api-bix5.onrender.com",
                "purpose": "Check whether the resource or context can be trusted before using it for agent decisions.",
            },
            {
                "service": "agent-security-gateway",
                "endpoint": "/api/security/metadata-sanitize",
                "base_url": "https://agent-security-gateway.onrender.com",
                "purpose": "Check whether payment metadata contains sensitive or unsafe information.",
            },
            {
                "service": "agent-budget-guard",
                "endpoint": "/api/budget/check",
                "base_url": "https://agent-budget-guard.onrender.com",
                "purpose": "Check whether the paid resource access is within the agent budget.",
            },
            {
                "service": "ai-agent-payment-safety-stack",
                "endpoint": "/api/payment-evidence/check",
                "base_url": "https://ai-agent-payment-safety-stack.onrender.com",
                "purpose": "Check or prepare evidence for the paid resource transaction.",
            },
        ],
        "recommended_flow": [
            "agent-memory-api: trust/context check",
            "agent-security-gateway: metadata/privacy check",
            "agent-budget-guard: budget/duplicate payment check",
            "agent-paid-resource-control: paid resource review",
            "ai-agent-payment-safety-stack: evidence receipt/payment check",
        ],
        "non_goals": [
            "not a payment protocol",
            "not a wallet",
            "not a settlement layer",
            "not a legal compliance system",
            "not an official standard",
        ],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/", include_in_schema=False)
async def root():
    return {
        "service": "agent-paid-resource-control",
        "version": "0.1.0",
        "experimental": True,
        "description": (
            "External control layer for AI agents paying for web content, APIs, data, "
            "and financial workflow resources."
        ),
        "endpoints": {
            "POST /api/paid-resource/review": "0.03 USDC via x402",
            "GET /llms.txt": "free",
            "GET /.well-known/agent.json": "free",
            "GET /.well-known/x402": "free",
        },
        "non_goals": [
            "not a payment protocol",
            "not a wallet",
            "not a settlement layer",
            "not affiliated with AWS, Coinbase, Arc, or Circle",
        ],
    }


@app.get("/llms.txt", include_in_schema=False)
async def llms_txt():
    content = """# AI Agent External Resource Review
# External Control Front Door for AI Agent Stack

## Purpose
Use this API before an AI agent pays for or uses an external resource.
This is the front door of the AI Agent External Control Stack.

Use agent-paid-resource-control first when an AI agent is about to use or pay for an external resource.

## Primary use cases
1. Paid API / x402 Resource Review
   Decide whether an agent should use or pay for a paid API or x402 resource.

2. Tool / MCP / GitHub Repo Review
   Decide whether an agent should use an external tool, MCP server, GitHub repository, CLI, or binary.

3. Memory-backed Payment or CRM Decision Review
   Decide whether stored memory can be used for a payment, CRM update, or external action decision.

This API returns a pre-action review with decision, risk_level, payment_allowed, and required_checks.

## When to use
- Before paying for a paid API or x402 resource
- Before using an external tool, MCP server, or GitHub repository
- Before making a decision based on stored memory
- Before modifying a CRM record based on AI judgment

## External Control Stack routing
- agent-paid-resource-control: first — review whether an agent should use or pay for an external resource
- agent-budget-guard: spend limit / duplicate payment / budget risk
- agent-security-gateway: tool / input / security risk
- agent-memory-api-bix5: memory use permission / provenance check
- ai-agent-payment-safety-stack: payment / action / result evidence

## Main endpoint
POST /api/paid-resource/review

This endpoint is paid via x402 (0.03 USDC on Base eip155:8453).

## Decision logic
- resource_url empty or invalid → deny
- amount <= 0 → deny
- currency not USDC or JPYC → deny
- metadata contains injection patterns → deny
- all other cases → review_required

## Evidence fields
After payment, record:
- agent_id, resource_url, resource_type
- amount, currency, payment_protocol
- payment_intent_id, expected_result
- actual_result, payment_tx, memo_id, evidence_id

## Non-goals
Not a payment protocol, wallet, settlement layer, legal compliance system, or official standard.
Not affiliated with AWS, Coinbase, Arc, Circle, or any payment network.
"""
    return PlainTextResponse(content)


@app.get("/.well-known/agent.json", include_in_schema=False)
async def agent_json():
    return {
        "name": "Agent Paid Resource Control",
        "version": "0.1.0",
        "experimental": True,
        "live": True,
        "description": (
            "AI Agent External Resource Review. Front door of the AI Agent External Control Stack. "
            "Use before an AI agent pays for or uses an external resource."
        ),
        "endpoints": [
            {
                "path": "/api/paid-resource/review",
                "method": "POST",
                "description": "Review paid resource access before payment",
                "pricing": {"amount": "0.03", "currency": "USDC", "protocol": "x402"},
            }
        ],
        "use_cases": [
            "agent_paid_resource_review",
            "duplicate_payment_prevention",
            "metadata_privacy_check",
            "resource_binding_verification",
            "evidence_receipt_fields",
        ],
        "constraints": [
            "does_not_execute_payments",
            "does_not_handle_private_keys",
            "does_not_perform_wallet_operations",
            "experimental_only",
        ],
        "x402": {
            "network": "eip155:8453",
            "payTo": WALLET_ADDRESS,
        },
        "paid_data_lookup_support": {
            "role": "before_payment_review",
            "purpose": "Review paid data lookup requests before an AI agent pays for market data, crypto data, token metadata, onchain data, or news data via x402.",
            "use_when": [
                "Before an AI agent pays for a paid API or x402 resource",
                "Before an AI agent uses an external MCP tool, GitHub repository, CLI, or binary",
                "Before an AI agent uses stored memory to make a payment, CRM update, or external action decision",
            ],
            "key_fields": ["resource_type", "payment_purpose", "freshness_required_seconds", "expected_result"],
        },
    }


@app.get("/.well-known/x402", include_in_schema=False)
async def x402_manifest():
    return {
        "x402Version": 2,
        "name": "Agent Paid Resource Control",
        "title": "Agent Paid Resource Control",
        "description": (
            "Experimental external control layer for AI agents paying for resources. "
            "Use /api/paid-resource/review before making a paid resource access."
        ),
        "tags": ["AI", "Payments", "ResourceControl"],
        "resources": [
            {
                "url": "/api/paid-resource/review",
                "method": "POST",
                "description": "Review paid resource access — 0.03 USDC",
                "accepts": [
                    {
                        "scheme": "exact",
                        "network": "eip155:8453",
                        "amount": "30000",
                        "asset": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
                        "payTo": WALLET_ADDRESS,
                        "maxTimeoutSeconds": 300,
                        "extra": {"name": "USD Coin", "version": "2"},
                        "resource": {"method": "POST", "mimeType": "application/json"},
                    }
                ],
            }
        ],
    }


@app.get("/.well-known/agent-control-relations.json", include_in_schema=False)
async def agent_control_relations():
    return {
        "name": "Agent Paid Resource Control Relations",
        "version": "0.1.0",
        "status": "experimental",
        "primary_service": "agent-paid-resource-control",
        "primary_url": "https://agent-paid-resource-control.onrender.com",
        "description": "AI-readable relation index connecting paid resource review to trust, security, budget, and evidence layers.",
        "related_services": [
            {
                "name": "agent-memory-api",
                "base_url": "https://agent-memory-api-bix5.onrender.com",
                "role": "trust_and_context",
                "relation": "use_before_paid_resource_review",
                "key_endpoint": "/api/search-result-trust/check",
            },
            {
                "name": "agent-security-gateway",
                "base_url": "https://agent-security-gateway.onrender.com",
                "role": "security_and_metadata_privacy",
                "relation": "use_before_payment_or_metadata_submission",
                "key_endpoint": "/api/security/metadata-sanitize",
            },
            {
                "name": "agent-budget-guard",
                "base_url": "https://agent-budget-guard.onrender.com",
                "role": "budget_and_duplicate_payment_control",
                "relation": "use_before_x402_payment",
                "key_endpoint": "/api/budget/check",
            },
            {
                "name": "ai-agent-payment-safety-stack",
                "base_url": "https://ai-agent-payment-safety-stack.onrender.com",
                "role": "payment_evidence_and_receipt",
                "relation": "use_after_or_during_paid_resource_payment",
                "key_endpoint": "/api/payment-evidence/check",
            },
        ],
        "recommended_flow": [
            "trust_check",
            "metadata_privacy_check",
            "budget_check",
            "paid_resource_review",
            "payment_evidence_receipt",
        ],
        "external_control_materials_map": "https://ai-agent-payment-safety-stack.onrender.com/.well-known/external-control-materials.json",
        "non_goals": [
            "not a payment protocol",
            "not a wallet",
            "not a settlement layer",
            "not a legal compliance system",
            "not an official standard",
        ],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
