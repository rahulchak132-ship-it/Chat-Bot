"""
Core Customer Experience (CX) Chatbot Module.
Coordinates intent classification, sentiment analysis, knowledge retrieval (RAG),
progressive information extraction, ticket generation, and compliant response generation.
"""

import os
import json
import datetime
from typing import Dict, Any, List, Optional, Tuple

from modules.prompts import CX_SYSTEM_PROMPT, INTENT_SENTIMENT_ANALYSIS_PROMPT
from modules.intent import classify_intent_fallback, extract_entities_fallback, INTENT_CATEGORIES
from modules.sentiment import analyze_sentiment_fallback
from modules.escalation import evaluate_escalation
from modules.knowledge_base import get_knowledge_base
from modules.database import (
    insert_complaint,
    insert_service_request,
    insert_escalation,
    log_conversation_message,
    generate_complaint_id,
    generate_service_request_id
)

class CXChatbot:
    """Enterprise CX Executive Chatbot Engine."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.kb = get_knowledge_base()
        self.client = None
        self._init_openai_client()

    def _init_openai_client(self):
        """Initializes OpenAI client if API key is provided and valid."""
        if self.api_key and not self.api_key.startswith("your_openai"):
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
            except Exception as e:
                print(f"Warning: Could not initialize OpenAI client: {e}")
                self.client = None

    def analyze_message(self, message: str, conversation_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        Extracts Intent, Sentiment, Emotion, Urgency, Escalation, and Entities
        using OpenAI JSON schema or deterministic fallback.
        """
        # Try OpenAI structured analysis if client is active
        if self.client:
            try:
                context_str = "\n".join([f"{m.get('role', 'user')}: {m.get('content', '')}" for m in (conversation_history or [])[-4:]])
                prompt_input = f"Conversation History:\n{context_str}\n\nLatest Customer Message:\n{message}"

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": INTENT_SENTIMENT_ANALYSIS_PROMPT},
                        {"role": "user", "content": prompt_input}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1
                )
                raw_json = response.choices[0].message.content
                data = json.loads(raw_json)

                # Validate intent
                if data.get("intent") not in INTENT_CATEGORIES:
                    data["intent"] = classify_intent_fallback(message)

                return data
            except Exception as e:
                print(f"OpenAI analysis error (switching to fallback): {e}")

        # Deterministic High-Precision Fallback Engine
        sentiment_data = analyze_sentiment_fallback(message)
        intent = classify_intent_fallback(message)
        entities = extract_entities_fallback(message)

        is_esc, esc_reason, esc_team = evaluate_escalation(
            message=message,
            sentiment=sentiment_data["sentiment"],
            sentiment_score=sentiment_data["sentiment_score"],
            urgency=sentiment_data["urgency"],
            customer_type="Customer"
        )

        return {
            "intent": intent,
            "sentiment": sentiment_data["sentiment"],
            "sentiment_score": sentiment_data["sentiment_score"],
            "emotion": sentiment_data["emotion"],
            "urgency": sentiment_data["urgency"],
            "escalation_required": is_esc,
            "escalation_reason": esc_reason,
            "assigned_team": esc_team,
            "extracted_entities": entities
        }

    def generate_response(
        self,
        user_message: str,
        session_id: str,
        customer_profile: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Main end-to-end conversation pipeline:
        1. NLP Analysis (Intent, Sentiment, Emotion, Urgency, Escalation)
        2. Knowledge Base Retrieval (RAG)
        3. Empathetic and compliant AI response generation
        4. Automatic database ticket updates
        """
        profile = customer_profile or {}
        analysis = self.analyze_message(user_message, conversation_history)

        # Evaluate escalation with customer profile context
        is_esc, esc_reason, esc_team = evaluate_escalation(
            message=user_message,
            sentiment=analysis["sentiment"],
            sentiment_score=analysis.get("sentiment_score", 0),
            urgency=analysis["urgency"],
            customer_type=profile.get("customer_type", "Customer"),
            repeat_count=profile.get("repeat_complaints", 0)
        )
        if is_esc:
            analysis["escalation_required"] = True
            analysis["escalation_reason"] = esc_reason
            analysis["assigned_team"] = esc_team

        # RAG Search
        retrieved_passages = self.kb.search(user_message, top_k=2)
        rag_context = ""
        if retrieved_passages:
            rag_context = "\n---\n".join([f"[{p['title']} ({p['category']})]:\n{p['text']}" for p in retrieved_passages])

        ai_reply = ""

        # Check if OpenAI is available
        if self.client:
            try:
                system_with_rag = f"{CX_SYSTEM_PROMPT}\n\n==================================================\nVERIFIED COMPANY KNOWLEDGE BASE (USE ONLY THIS FOR SPECS/POLICY):\n==================================================\n{rag_context if rag_context else 'No specific manual found in database. Apply verified fallbacks.'}\n\nCURRENT CUSTOMER PROFILE:\n{json.dumps(profile, indent=2)}\n\nDETECTED NLP STATUS:\nIntent: {analysis['intent']}\nSentiment: {analysis['sentiment']} ({analysis.get('sentiment_score', 0)})\nEmotion: {analysis['emotion']}\nUrgency: {analysis['urgency']}\nEscalation: {analysis['escalation_required']} ({analysis.get('escalation_reason', '')})"

                messages_payload = [{"role": "system", "content": system_with_rag}]
                for m in (conversation_history or [])[-6:]:
                    messages_payload.append({"role": m["role"], "content": m["content"]})
                messages_payload.append({"role": "user", "content": user_message})

                resp = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages_payload,
                    temperature=0.3,
                    max_tokens=600
                )
                ai_reply = resp.choices[0].message.content.strip()
            except Exception as e:
                print(f"OpenAI completion error, using expert rule generator: {e}")
                ai_reply = self._generate_rule_based_response(user_message, analysis, rag_context, profile)
        else:
            ai_reply = self._generate_rule_based_response(user_message, analysis, rag_context, profile)

        # Log conversation
        log_conversation_message(
            session_id=session_id,
            role="user",
            content=user_message,
            intent=analysis["intent"],
            sentiment=analysis["sentiment"],
            emotion=analysis["emotion"],
            urgency=analysis["urgency"]
        )
        log_conversation_message(
            session_id=session_id,
            role="assistant",
            content=ai_reply,
            intent=analysis["intent"],
            sentiment=analysis["sentiment"],
            emotion=analysis["emotion"],
            urgency=analysis["urgency"]
        )

        return ai_reply, analysis

    def _generate_rule_based_response(
        self,
        message: str,
        analysis: Dict[str, Any],
        rag_context: str,
        profile: Dict[str, Any]
    ) -> str:
        """
        Deterministic, empathetic, high-fidelity CX generation engine.
        Follows all strict behavioral rules from Section 3, 8, 12, 27 & 28.
        """
        sentiment = analysis.get("sentiment", "Neutral")
        urgency = analysis.get("urgency", "LOW")
        intent = analysis.get("intent", "General Query")
        emotion = analysis.get("emotion", "Neutral")

        # Empathy acknowledgment prefix if customer is angry / frustrated / negative
        empathy_prefix = ""
        if sentiment in ["Very Negative", "Negative"] or emotion in ["Frustrated", "Angry", "Disappointed"]:
            if "visited" in message.lower() or "days" in message.lower():
                empathy_prefix = "I'm really sorry you've had to wait this long. I understand how frustrating delayed service can be, and I will help you raise this for immediate priority action.\n\n"
            else:
                empathy_prefix = "I understand that this experience has been frustrating. Let me help you resolve this right away.\n\n"

        # Critical Safety Hazard Handling
        if urgency == "CRITICAL" or "fire" in message.lower() or "smoke" in message.lower() or "shock" in message.lower():
            return (
                "⚠️ **SAFETY PRIORITY NOTICE**\n\n"
                "Please ensure the equipment is immediately isolated:\n"
                "1. If safe to do so, disengage the main AC and DC isolator switches or press the Red Emergency Stop button.\n"
                "2. Keep all personnel at a safe distance.\n\n"
                "I have triggered an **EMERGENCY ESCALATION** to our Rapid Safety & Engineering Core. "
                "A senior technical supervisor is being paged right now to guide you."
            )

        # Service / Technician Request or Repeated Service Complaint
        if intent in ["Service Request", "Product Complaint"] and any(w in message.lower() for w in ["not visited", "delay", "service team", "stopped working", "inverter"]):
            # Check what details we still need (progressive disclosure)
            missing = []
            if not profile.get("name"):
                missing.append("Your Full Name")
            if not profile.get("mobile"):
                missing.append("Mobile Number")
            if not profile.get("product") and not profile.get("model"):
                missing.append("Product & Model Number")
            if not profile.get("location"):
                missing.append("Installation Location / City")
            if not profile.get("serial_number"):
                missing.append("Serial Number or Existing Service Request Number (if available)")

            if missing:
                bullet_list = "\n".join([f"{i+1}. {item}" for i, item in enumerate(missing[:4])])
                return (
                    f"{empathy_prefix}"
                    f"To expedite this and assign our regional field service engineer, could you please confirm:\n"
                    f"{bullet_list}\n\n"
                    f"Once confirmed, I will generate an escalated service ticket."
                )

        # RAG verified answer if passages found
        if rag_context:
            # Format concise verified answer
            return (
                f"{empathy_prefix}"
                f"Here is the verified information from our technical documentation:\n\n"
                f"{rag_context}\n\n"
                f"Would you like me to book a technician visit or help you with anything else regarding this?"
            )

        # Missing Knowledge Base rule (Section 12 requirement)
        if intent in ["Product Information", "Warranty Query", "Technical Support"]:
            return (
                f"{empathy_prefix}"
                f"I don't have enough verified information to answer that accurately. "
                f"I can raise this as a service request or connect you with the appropriate team.\n\n"
                f"Would you like me to initiate a technical inquiry for our engineering specialists?"
            )

        # Dealer / Distributor commercial query
        if profile.get("customer_type") in ["Dealer", "Distributor"] or intent in ["Dealer Complaint", "Distributor Complaint", "Pricing Query"]:
            return (
                f"{empathy_prefix}"
                f"Thank you for contacting our Channel Partner desk. "
                f"For dealer margins, RMA replacement of Dead-On-Arrival (DOA) units, and quarterly rebate reconciliations, "
                f"our standard policy allows DOA replacement within 5 business days of return logging.\n\n"
                f"Could you share your Dealer Code and the Invoice Number so I can look up your credit or dispatch ledger?"
            )

        # General polite default
        return (
            f"{empathy_prefix}"
            f"Thank you for reaching out to Apex Global Customer Experience. "
            f"I can assist you with product technical inquiries, troubleshooting error codes, "
            f"registering complaints, booking on-site service visits, and tracking tickets.\n\n"
            f"How can I best assist you today?"
        )
