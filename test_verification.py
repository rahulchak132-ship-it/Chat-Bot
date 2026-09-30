"""
Comprehensive Unit and Integration Verification Script.
Tests all modules in customer_experience_bot without external network dependencies.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "customer_experience_bot")))

from modules.database import (
    init_database,
    seed_initial_data,
    insert_complaint,
    insert_service_request,
    insert_escalation,
    insert_feedback,
    get_complaints_list
)
from modules.intent import classify_intent_fallback, INTENT_CATEGORIES
from modules.sentiment import analyze_sentiment_fallback
from modules.escalation import evaluate_escalation
from modules.knowledge_base import get_knowledge_base
from modules.analytics import calculate_kpis, get_distribution_data, generate_management_insights
from modules.chatbot import CXChatbot
from modules.voice_ready import VoiceCallAnalyzer

class TestCXSuite(unittest.TestCase):

    def setUp(self):
        self.db_path = "customer_experience_bot/data/test_cx.sqlite"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        init_database(self.db_path)
        seed_initial_data(self.db_path)

    def test_database_seeding(self):
        complaints = get_complaints_list(db_path=self.db_path)
        self.assertGreaterEqual(len(complaints), 10)
        self.assertTrue(any(c["urgency"] == "CRITICAL" for c in complaints))
        print("✓ Database seeding test passed")

    def test_intent_classification(self):
        # 1. Product info
        self.assertEqual(classify_intent_fallback("What are the technical specifications of the 5KVA solar inverter?"), "Product Information")
        # 2. Defect / Safety
        self.assertEqual(classify_intent_fallback("There is smoke and sparks coming out of the charging port!"), "Emergency / High Priority")
        # 3. Service request
        self.assertEqual(classify_intent_fallback("Please schedule a technician visit for annual maintenance."), "Service Request")
        print("✓ Intent classification test passed")

    def test_sentiment_and_urgency(self):
        # Sample from prompt: "My inverter stopped working and your service team hasn't visited for 5 days."
        sample = "My inverter stopped working and your service team hasn't visited for 5 days."
        res = analyze_sentiment_fallback(sample)
        self.assertIn(res["sentiment"], ["Negative", "Very Negative"])
        self.assertIn(res["emotion"], ["Frustrated", "Angry", "Disappointed"])
        self.assertIn(res["urgency"], ["HIGH", "CRITICAL"])
        print(f"✓ Sample sentiment test passed: {res}")

    def test_escalation_engine(self):
        # Safety critical
        is_esc, reason, team = evaluate_escalation(
            message="Smoke detected from the machine",
            sentiment="Very Negative",
            sentiment_score=-85,
            urgency="CRITICAL"
        )
        self.assertTrue(is_esc)
        self.assertIn("Safety", team)
        print("✓ Escalation engine test passed")

    def test_knowledge_base_rag(self):
        kb = get_knowledge_base()
        results = kb.search("Error E04 grid sync relay")
        self.assertGreater(len(results), 0)
        self.assertIn("Solar Inverter Error Codes", results[0]["title"])
        print("✓ Knowledge base RAG search test passed")

    def test_analytics_and_insights(self):
        kpis = calculate_kpis(self.db_path)
        self.assertGreater(kpis["total_complaints"], 0)
        self.assertGreater(kpis["csat_score"], 50)
        dists = get_distribution_data(self.db_path)
        insights = generate_management_insights(kpis, dists)
        self.assertGreater(len(insights), 2)
        print("✓ Analytics & insights generation test passed")

    def test_chatbot_sample_conversation(self):
        bot = CXChatbot()
        reply, analysis = bot.generate_response(
            user_message="My inverter stopped working and your service team hasn't visited for 5 days.",
            session_id="TEST-SESS-01",
            customer_profile={"name": "Rajesh Sharma", "mobile": "+91 98201 12345", "product": "Solar Hybrid Inverter"}
        )
        self.assertTrue(len(reply) > 20)
        self.assertIn(analysis["urgency"], ["HIGH", "CRITICAL"])
        print("✓ Chatbot end-to-end conversation test passed")

    def test_voice_architecture(self):
        analyzer = VoiceCallAnalyzer()
        rep = analyzer.analyze_audio_file("sample_test.wav")
        self.assertEqual(len(rep.transcript), 7)
        self.assertGreater(rep.call_quality_score, 80)
        print("✓ Voice architecture test passed")

if __name__ == "__main__":
    unittest.main()
