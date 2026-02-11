from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

from .repository import ReplayRepository
from .schema import ApiCallRecord, new_id, utc_now

VALID_TRANSITIONS = {
    "requires_payment_method": "requires_confirmation",
    "requires_confirmation": "processing",
    "processing": "succeeded",
}


@dataclass(slots=True)
class GatewayResponse:
    status_code: int
    body: dict[str, Any]
    headers: dict[str, str]


class GatewaySimulator:
    def __init__(self, repo: ReplayRepository, seed: int = 0) -> None:
        self.repo = repo
        self.prng = random.Random(seed)
        self.customers: dict[str, dict[str, Any]] = {}
        self.payment_intents: dict[str, dict[str, Any]] = {}
        self.refunds: dict[str, dict[str, Any]] = {}

    def _server_timing(self) -> str:
        db_ms = 1 + int(self.prng.random() * 3)
        app_ms = 2 + int(self.prng.random() * 6)
        return f"db;dur={db_ms},app;dur={app_ms}"

    def _headers(self, correlation_id: str) -> dict[str, str]:
        return {
            "Server-Timing": self._server_timing(),
            "X-Correlation-Id": correlation_id,
        }

    def _log_call(
        self,
        run_id: str,
        method: str,
        path: str,
        request_payload: dict[str, Any],
        response_payload: dict[str, Any],
        status_code: int,
        correlation_id: str,
        idempotency_key: str | None,
        cache_hit: bool,
    ) -> None:
        now = utc_now()
        self.repo.save_api_call(
            ApiCallRecord(
                id=new_id("api"),
                run_id=run_id,
                service="gateway",
                method=method,
                path=path,
                request_json=request_payload,
                response_json=response_payload,
                status_code=status_code,
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                started_at=now,
                ended_at=now,
                latency_ms=3 + int(self.prng.random() * 4),
                cache_hit=1 if cache_hit else 0,
            )
        )

    def create_customer(self, run_id: str, email: str, correlation_id: str) -> GatewayResponse:
        customer_id = new_id("cus")
        body = {"id": customer_id, "object": "customer", "email": email}
        self.customers[customer_id] = body
        self._log_call(
            run_id,
            "POST",
            "/v1/customers",
            {"email": email},
            body,
            200,
            correlation_id,
            None,
            False,
        )
        return GatewayResponse(status_code=200, body=body, headers=self._headers(correlation_id))

    def create_payment_intent(
        self,
        run_id: str,
        amount: int,
        currency: str,
        correlation_id: str,
        idempotency_key: str | None,
    ) -> GatewayResponse:
        request_payload = {"amount": amount, "currency": currency}
        if idempotency_key:
            cached = self.repo.idempotency_lookup(
                "POST",
                "/v1/payment_intents",
                idempotency_key,
                request_payload,
            )
            if cached is not None:
                self._log_call(
                    run_id,
                    "POST",
                    "/v1/payment_intents",
                    request_payload,
                    cached,
                    200,
                    correlation_id,
                    idempotency_key,
                    True,
                )
                return GatewayResponse(
                    status_code=200, body=cached, headers=self._headers(correlation_id)
                )

        intent_id = new_id("pi")
        body = {
            "id": intent_id,
            "object": "payment_intent",
            "amount": amount,
            "currency": currency,
            "status": "requires_payment_method",
        }
        self.payment_intents[intent_id] = body
        if idempotency_key:
            self.repo.idempotency_store(
                "POST",
                "/v1/payment_intents",
                idempotency_key,
                request_payload,
                body,
            )
        self._log_call(
            run_id,
            "POST",
            "/v1/payment_intents",
            request_payload,
            body,
            200,
            correlation_id,
            idempotency_key,
            False,
        )
        return GatewayResponse(status_code=200, body=body, headers=self._headers(correlation_id))

    def confirm_payment_intent(
        self,
        run_id: str,
        intent_id: str,
        correlation_id: str,
        idempotency_key: str | None,
    ) -> GatewayResponse:
        if intent_id not in self.payment_intents:
            return GatewayResponse(
                status_code=404,
                body={"error": "intent_not_found"},
                headers=self._headers(correlation_id),
            )

        intent = self.payment_intents[intent_id]
        current = intent["status"]
        next_state = VALID_TRANSITIONS.get(current)
        if next_state is None:
            next_state = current
        intent["status"] = next_state

        response = {"id": intent_id, "status": next_state, "object": "payment_intent"}
        self._log_call(
            run_id,
            "POST",
            f"/v1/payment_intents/{intent_id}/confirm",
            {"intent_id": intent_id},
            response,
            200,
            correlation_id,
            idempotency_key,
            False,
        )
        return GatewayResponse(
            status_code=200, body=response, headers=self._headers(correlation_id)
        )

    def create_refund(
        self, run_id: str, payment_intent_id: str, correlation_id: str
    ) -> GatewayResponse:
        refund_id = new_id("re")
        body = {
            "id": refund_id,
            "object": "refund",
            "payment_intent": payment_intent_id,
            "status": "succeeded",
        }
        self.refunds[refund_id] = body
        self._log_call(
            run_id,
            "POST",
            "/v1/refunds",
            {"payment_intent": payment_intent_id},
            body,
            200,
            correlation_id,
            None,
            False,
        )
        return GatewayResponse(status_code=200, body=body, headers=self._headers(correlation_id))

    def deterministic_failure(self, probability: float) -> bool:
        return self.prng.random() < probability
