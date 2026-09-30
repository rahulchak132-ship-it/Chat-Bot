"""
Escalation Engine Module for Enterprise Customer Experience (CX) Suite.
Evaluates incoming tickets and conversations for automated management escalation triggers.
"""

from typing import Dict, Any, Tuple

def evaluate_escalation(
    message: str,
    sentiment: str,
    sentiment_score: int,
    urgency: str,
    customer_type: str = "Customer",
    repeat_count: int = 0,
    hours_open: float = 0.0
) -> Tuple[bool, str, str]:
    """
    Evaluates whether an automated escalation must be raised.
    Returns: (is_escalation_required, reason, assigned_executive_team)
    """
    text_lower = message.lower()

    # Rule 1: Critical Urgency (Safety, Fire, Electrical Hazard, Physical Harm)
    if urgency == "CRITICAL" or any(w in text_lower for w in ["fire", "smoke", "spark", "shock", "hazard", "explosion", "injury"]):
        return (
            True,
            "CRITICAL safety hazard / hardware fire or electrical risk reported. Immediate executive containment required.",
            "Safety & Engineering Core Taskforce"
        )

    # Rule 2: Legal Threat / Regulatory Complaint
    if any(w in text_lower for w in ["legal action", "lawyer", "advocate", "consumer court", "police", "fir", "sue you"]):
        return (
            True,
            "Customer has raised formal legal action / consumer dispute notice.",
            "Legal & Corporate Compliance Directorate"
        )

    # Rule 3: Customer explicitly demands Manager / Leadership
    if any(w in text_lower for w in ["speak to your manager", "escalate to manager", "call your supervisor", "talk to head"]):
        return (
            True,
            "Customer explicitly requested senior supervisory intervention.",
            "Customer Operations Team Lead"
        )

    # Rule 4: Dealer / Distributor Significant Business Impact
    if customer_type in ["Dealer", "Distributor", "Business Partner"]:
        if any(w in text_lower for w in ["loss of business", "cancelling dealership", "stop selling", "credit hold", "dispute margin", "refuse stock"]):
            return (
                True,
                f"High-priority {customer_type} commercial dispute or revenue disruption detected.",
                "Channel Sales & Partner Relations VP"
            )

    # Rule 5: Repeated Unresolved Complaints
    if repeat_count >= 2 or any(w in text_lower for w in ["again and again", "third time", "fourth time", "unresolved for weeks", "repeated complaint"]):
        return (
            True,
            "Customer has reported repeated unresolved service failures on the same equipment.",
            "Quality Assurance & Regional Service Head"
        )

    # Rule 6: Prolonged SLA Breach (> 48 hours unresolved with negative sentiment)
    if hours_open > 48.0 or any(w in text_lower for w in ["10 days", "7 days", "over a week", "nobody visited", "still waiting"]):
        if sentiment in ["Negative", "Very Negative"]:
            return (
                True,
                "Service SLA breach exceeded standard 48-hour response threshold with high dissatisfaction.",
                "Field Operations Escalations Desk"
            )

    # Rule 7: Very Negative Sentiment with High Urgency
    if sentiment == "Very Negative" and (urgency in ["HIGH", "CRITICAL"] or sentiment_score <= -75):
        return (
            True,
            f"Sentiment score reached severe threshold ({sentiment_score}/100) with elevated urgency.",
            "Senior Customer Experience Manager"
        )

    return (False, "", "")
