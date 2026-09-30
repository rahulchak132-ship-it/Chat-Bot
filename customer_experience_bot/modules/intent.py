"""
Intent Classification Module for Enterprise Customer Experience (CX) Suite.
Classifies messages into exactly 20 enterprise intent categories with dual-engine
execution: OpenAI JSON schema extraction with robust deterministic rule-based fallback.
"""

import re
from typing import Dict, Any, List

INTENT_CATEGORIES = [
    "Product Information",
    "Product Complaint",
    "Product Defect",
    "Technical Support",
    "Installation Issue",
    "Warranty Query",
    "Service Request",
    "Spare Parts",
    "Delivery Issue",
    "Order Status",
    "Dealer Complaint",
    "Distributor Complaint",
    "Pricing Query",
    "Payment Query",
    "Replacement Request",
    "Refund Request",
    "Feedback",
    "Suggestion",
    "General Query",
    "Emergency / High Priority"
]

# High-precision keyword & pattern rules for deterministic fallback
INTENT_PATTERNS = {
    "Emergency / High Priority": [
        r"\b(fire|smoke|spark|sparking|shock|electrocute|hazard|explosion|burst|blast|burning smell|danger|threat|police|court|legal action|advocate)\b",
        r"\b(emergency|urgent|life threat|burn)\b"
    ],
    "Product Defect": [
        r"\b(defect|defective|broken|cracked|leaking|short circuit|faulty component|display dead|pcb burnt|damaged on arrival)\b",
        r"\b(hardware failure|manufacturing defect|blown fuse)\b"
    ],
    "Installation Issue": [
        r"\b(installation|install|mounting|wiring|grid connect|commissioning|setup issue|brackets|inverter mounting|earthing)\b"
    ],
    "Technical Support": [
        r"\b(error code|fault code|e0[1-9]|f0[1-9]|app not connecting|firmware|wifi dongle|sync issue|cavitation|tripping|tripped)\b",
        r"\b(troubleshoot|how to configure|parameter|settings|manual reset)\b"
    ],
    "Service Request": [
        r"\b(service request|book a service|technician visit|schedule visit|service engineer|maintenance|amc|inspection|visit my location)\b",
        r"\b(book service|send technician|send engineer)\b"
    ],
    "Spare Parts": [
        r"\b(spare part|replacement board|spare|component|cable|filter|display panel|relay|igbt|capacitor|connector)\b"
    ],
    "Warranty Query": [
        r"\b(warranty|guarantee|extended warranty|coverage|warranty card|warranty terms|warranty policy|under warranty)\b"
    ],
    "Delivery Issue": [
        r"\b(delayed delivery|delivery delay|shipment delay|not arrived|dispatched|courier|transport damage|pallet damage|consignment)\b"
    ],
    "Order Status": [
        r"\b(order status|where is my order|tracking number|track order|awb|dispatch status|po status)\b"
    ],
    "Replacement Request": [
        r"\b(replace unit|replacement|swap|exchange unit|new piece|replace my)\b"
    ],
    "Refund Request": [
        r"\b(refund|money back|reimburse|credit note return|compensation)\b"
    ],
    "Dealer Complaint": [
        r"\b(dealer issue|dealer not responding|dealer refused|dealer cheated|authorized dealer problem|dealer complaint)\b"
    ],
    "Distributor Complaint": [
        r"\b(distributor delay|distributor stock|distributor margin|distributor credit|distributor complaint)\b"
    ],
    "Pricing Query": [
        r"\b(price|pricing|cost|quotation|discount|rate|dealer price|commercial proposal|quote)\b"
    ],
    "Payment Query": [
        r"\b(payment|invoice|billing|gst invoice|credit terms|outstanding|ledger|transaction failed)\b"
    ],
    "Feedback": [
        r"\b(feedback|experience was|rate your service|satisfied|dissatisfied|review|kudos|great service|poor service)\b"
    ],
    "Suggestion": [
        r"\b(suggest|recommendation|feature request|would be better if|improvement)\b"
    ],
    "Product Complaint": [
        r"\b(complaint|not working|stopped working|failed|useless|terrible product|worst|heating up|loud noise|vibrating|shut down)\b"
    ],
    "Product Information": [
        r"\b(specifications|datasheet|features|catalog|models available|capacity|efficiency|dimensions|weight|compatibility)\b"
    ]
}

def classify_intent_fallback(text: str) -> str:
    """Classifies user query intent using domain-specific heuristics and regex patterns."""
    text_lower = text.lower()
    
    # Priority order matching
    for intent, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return intent

    # Check for general question keywords
    if any(q in text_lower for q in ["what", "how", "when", "where", "can i", "is it", "tell me"]):
        return "Product Information"

    return "General Query"

def extract_entities_fallback(text: str) -> Dict[str, Any]:
    """Extracts phone numbers, models, and serial numbers using regex patterns."""
    entities = {
        "phone": None,
        "serial_number": None,
        "model": None,
        "ticket_ref": None
    }
    # Match Phone
    phone_match = re.search(r"(\+?\d{1,3}[-.\s]?)?(\d{10}|\d{5}[-.\s]?\d{5})", text)
    if phone_match:
        entities["phone"] = phone_match.group(0).strip()

    # Match Serial Number (e.g. SN-SOLAR-88219 or SN123456)
    sn_match = re.search(r"\b(SN[-_A-Z0-9]{5,20})\b", text, re.IGNORECASE)
    if sn_match:
        entities["serial_number"] = sn_match.group(1).upper()

    # Match Model (e.g. Apex-Solar-5KVA, Apex-HP-10KW)
    model_match = re.search(r"\b(Apex-[A-Za-z0-9\-]+|[0-9]+KVA|[0-9]+KW|[0-9]+HP)\b", text, re.IGNORECASE)
    if model_match:
        entities["model"] = model_match.group(1)

    # Match Ticket Ref (CX-YYYYMMDD-XXXX or SR-YYYYMMDD-XXXX)
    ticket_match = re.search(r"\b((CX|SR)-\d{8}-\d{4})\b", text, re.IGNORECASE)
    if ticket_match:
        entities["ticket_ref"] = ticket_match.group(1).upper()

    return entities
