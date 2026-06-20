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
    title="Agent Paid Resource Control",
    version="0.1.0",
    description=(
        "An experimental external control layer for AI agents that pay for web content, "
        "APIs, data, and financial workflow resources. "
        "Use POST /api/paid-resource/review before paying for a resource. "
        "Not a payment protocol, wallet, settlement layer, or official standard."
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
                "bodyType": "json",
                "body": {
                    "agent_id": "agent_001",
                    "resource_url": "https://example.com/api/data",
                    "resource_type": "data_api",
                    "payment_protocol": "x402",
                    "amount": "0.03",
                    "currency": "USDC",
                    "payment_purpose": "data_access",
                    "expected_result": "JSON response with market data",
                },
            },
            "output": {
                "type": "json",
                "example": {
                    "decision": "review_required",
                    "resource_control": {
                        "resource_binding": "check_required",
                        "duplicate_payment_risk": "unknown",
                    },
                },
            },
        },
        "schema": {
            "type": "object",
            "properties": {
                "decision": {"type": "string"},
                "resource_control": {"type": "object"},
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
                    "method": method,
                    "description": "Agent Paid Resource Review — 0.03 USDC",
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
    resource_type: str = Field(..., description="Type of resource (e.g. data_api, web_content, financial_data)")
    payment_protocol: str = Field(..., description="Payment protocol (e.g. x402, stripe)")
    amount: str = Field(..., description="Payment amount as string")
    currency: str = Field(..., description="Currency (USDC or JPYC)")
    payment_purpose: str = Field(..., description="Purpose of the payment")
    expected_result: str = Field(..., description="Expected result after payment")
    license_terms_id: Optional[str] = Field(default=None, description="License terms identifier")
    payment_intent_id: Optional[str] = Field(default=None, description="Payment intent ID")
    memo_id: Optional[str] = Field(default=None, description="Memo ID for reconciliation")
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
        "Review an AI agent's intent to pay for a resource. "
        "Returns decision (allow/deny/review_required), resource control fields, "
        "agent guidance, and evidence receipt fields."
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
        verified = await payment_verifier.verify_payment(payment_header, "/api/paid-resource/review")
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
    content = """# Agent Paid Resource Control

Agent Paid Resource Control is an experimental external control layer for AI agents
that pay for web content, APIs, data, and financial workflow resources.

Use this API before or after an agent pays for a resource to review:
- what resource is being paid for
- whether the payment should be bound to a specific URL/path/API
- whether duplicate payment risk exists
- whether metadata is privacy-safe
- what result should be fulfilled after payment
- what evidence fields should be recorded
- whether reconciliation is required

Main endpoint:
POST /api/paid-resource/review

This endpoint is paid via x402 (0.03 USDC on Base eip155:8453).

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
            "Experimental external control layer for AI agents paying for resources. "
            "Call /api/paid-resource/review before executing a payment."
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
