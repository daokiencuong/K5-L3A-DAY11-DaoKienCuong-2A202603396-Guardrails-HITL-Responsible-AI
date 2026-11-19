"""
Lab 11 — Optional enrichment: Human-in-the-Loop Design
  (Không chấm — tham khảo. Tóm tắt nộp do scripts/grade.py tự sinh,
   không viết report/*.md tay.)
  - Confidence Router
  - 3 HITL decision points
"""
from dataclasses import dataclass
import math


# ============================================================
# Optional enrichment: ConfidenceRouter (không chấm)
#
# Route agent responses based on confidence scores:
#   - HIGH (>= 0.9): Auto-send to user
#   - MEDIUM (0.7 - 0.9): Queue for human review
#   - LOW (< 0.7): Escalate to human immediately
#
# Special case: if the action is HIGH_RISK (e.g., money transfer,
# account deletion), ALWAYS escalate regardless of confidence.
#
# Implement the route() method.
# ============================================================

HIGH_RISK_ACTIONS = [
    "transfer_money",
    "close_account",
    "change_password",
    "delete_data",
    "update_personal_info",
]


@dataclass
class RoutingDecision:
    """Result of the confidence router."""
    action: str          # "auto_send", "queue_review", "escalate"
    confidence: float
    reason: str
    priority: str        # "low", "normal", "high"
    requires_human: bool


class ConfidenceRouter:
    """Route agent responses based on confidence and risk level.

    Thresholds:
        HIGH:   confidence >= 0.9 -> auto-send
        MEDIUM: 0.7 <= confidence < 0.9 -> queue for review
        LOW:    confidence < 0.7 -> escalate to human

    High-risk actions always escalate regardless of confidence.
    """

    HIGH_THRESHOLD = 0.9
    MEDIUM_THRESHOLD = 0.7

    def route(self, response: str, confidence: float,
              action_type: str = "general") -> RoutingDecision:
        """Route a response based on confidence score and action type.

        Args:
            response: The agent's response text
            confidence: Confidence score between 0.0 and 1.0
            action_type: Type of action (e.g., "general", "transfer_money")

        Returns:
            RoutingDecision with routing action and metadata
        """
        del response  # Routing uses the calibrated score and requested action.
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
            raise TypeError("confidence must be a numeric score from 0.0 to 1.0")
        score = float(confidence)
        if not math.isfinite(score) or not 0.0 <= score <= 1.0:
            raise ValueError("confidence must be finite and between 0.0 and 1.0")

        action = (action_type or "general").strip().casefold()
        if action in HIGH_RISK_ACTIONS:
            return RoutingDecision("escalate", score, f"High-risk action: {action}", "high", True)
        if score >= self.HIGH_THRESHOLD:
            return RoutingDecision("auto_send", score, "High confidence", "low", False)
        if score >= self.MEDIUM_THRESHOLD:
            return RoutingDecision("queue_review", score, "Medium confidence — needs review", "normal", True)
        return RoutingDecision("escalate", score, "Low confidence — escalating", "high", True)


# ============================================================
# Optional enrichment: 3 HITL decision points (không chấm)
# Không bắt buộc điền. Tóm tắt bài nộp: chạy scripts/grade.py
# (tự sinh lab_report.md) — không viết report tay.
#
# For each decision point, define:
# - trigger: What condition activates this HITL check?
# - hitl_model: Which model? (human-in-the-loop, human-on-the-loop,
#   human-as-tiebreaker)
# - context_needed: What info does the human reviewer need?
# - example: A concrete scenario
# - approval_path: What approve/reject/timeout decision is recorded?
# - audit_fields: Which correlation ID, intent and proposed action/diff are logged?
#
# Think about real banking scenarios where human judgment is critical.
# ============================================================

hitl_decision_points = [
    {
        "id": 1,
        "name": "High-risk money movement",
        "trigger": "Any transfer, withdrawal, or payee change with an irreversible financial side effect; always review regardless of model confidence.",
        "hitl_model": "human-in-the-loop",
        "context_needed": "Authenticated customer, recipient and destination, amount/currency, funding source, risk signals, exact proposed transaction, and idempotency key.",
        "example": "A request asks the assistant to transfer 50,000,000 VND to a newly added recipient.",
        "approval_path": "Hold the action pending review. Approve only the displayed transaction; reject or timeout cancels it. Any material edit requires new approval.",
        "audit_fields": "correlation_id, customer_id, intent, recipient, amount, currency, proposed_action_hash, risk_signals, reviewer_id, decision, timestamp, timeout, execution_id.",
    },
    {
        "id": 2,
        "name": "Account recovery and identity change",
        "trigger": "Password reset, account recovery, contact-detail change, or conflicting identity evidence.",
        "hitl_model": "human-in-the-loop",
        "context_needed": "Verified identity factors, recent account-change history, device/session signals, requested before/after values (masked), and policy result.",
        "example": "A caller requests a phone-number change and immediate password reset while failing one identity check.",
        "approval_path": "Do not apply changes before review. Approve only after independent verification; reject or timeout leaves existing account state intact and routes the customer to verified support.",
        "audit_fields": "correlation_id, customer_id, recovery_intent, masked_before_after, verification_results, reviewer_id, decision, reason_code, timestamp.",
    },
    {
        "id": 3,
        "name": "Disputed transaction and fraud escalation",
        "trigger": "Customer disputes a transaction, a fraud score crosses policy threshold, or evidence sources disagree.",
        "hitl_model": "human-on-the-loop with human-as-tiebreaker for conflicting evidence",
        "context_needed": "Transaction timeline, merchant and amount, customer statement, fraud indicators, evidence provenance, and permitted reversible actions.",
        "example": "A card transaction is flagged as suspicious but the device location matches the customer's recent travel notice.",
        "approval_path": "The assistant may collect facts and suggest a reversible card freeze; a trained reviewer decides dispute status and any irreversible reimbursement. Timeout preserves the safe hold and opens a case.",
        "audit_fields": "correlation_id, case_id, transaction_id, evidence_sources, provenance, model_confidence, proposed_action, reviewer_id, decision, rationale, timestamp.",
    },
]


# ============================================================
# Quick tests
# ============================================================

def test_confidence_router():
    """Test ConfidenceRouter with sample scenarios."""
    router = ConfidenceRouter()

    test_cases = [
        ("Balance inquiry", 0.95, "general"),
        ("Interest rate question", 0.82, "general"),
        ("Ambiguous request", 0.55, "general"),
        ("Transfer $50,000", 0.98, "transfer_money"),
        ("Close my account", 0.91, "close_account"),
    ]

    print("Testing ConfidenceRouter:")
    print("=" * 80)
    print(f"{'Scenario':<25} {'Conf':<6} {'Action Type':<18} {'Decision':<15} {'Priority':<10} {'Human?'}")
    print("-" * 80)

    for scenario, conf, action_type in test_cases:
        decision = router.route(scenario, conf, action_type)
        print(
            f"{scenario:<25} {conf:<6.2f} {action_type:<18} "
            f"{decision.action:<15} {decision.priority:<10} "
            f"{'Yes' if decision.requires_human else 'No'}"
        )

    print("=" * 80)


def test_hitl_points():
    """Display HITL decision points."""
    print("\nHITL Decision Points:")
    print("=" * 60)
    for point in hitl_decision_points:
        print(f"\n  Decision Point #{point['id']}: {point['name']}")
        print(f"    Trigger:  {point['trigger']}")
        print(f"    Model:    {point['hitl_model']}")
        print(f"    Context:  {point['context_needed']}")
        print(f"    Example:  {point['example']}")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_confidence_router()
    test_hitl_points()
