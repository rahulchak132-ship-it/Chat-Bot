"""
Enterprise Customer Experience (CX) AI Suite.
Production-grade Streamlit application for retail customers, authorized dealers,
regional distributors, and corporate management.
"""

import os
import sys
import uuid
import datetime
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

# Ensure local modules directory is on Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.database import (
    init_database,
    seed_initial_data,
    get_connection,
    insert_complaint,
    insert_service_request,
    insert_escalation,
    insert_feedback,
    get_complaints_list,
    generate_complaint_id,
    generate_service_request_id
)
from modules.chatbot import CXChatbot
from modules.knowledge_base import get_knowledge_base
from modules.analytics import calculate_kpis, get_distribution_data, generate_management_insights
from modules.voice_ready import VoiceCallAnalyzer

# Load environment configuration
load_dotenv()

# Page Configuration
st.set_page_config(
    page_title="Apex CX | Enterprise Customer Experience AI Suite",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Enterprise Styling (Clean corporate typography, WCAG contrast, no garish slop)
st.markdown("""
<style>
    /* Global Corporate Tone */
    .stApp {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }
    
    /* Header Card */
    .cx-header {
        padding: 1.25rem 1.5rem;
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #ffffff;
        border-radius: 8px;
        margin-bottom: 1.5rem;
        border-left: 5px solid #0284c7;
    }
    .cx-header h1 {
        margin: 0;
        font-size: 1.6rem;
        font-weight: 700;
        color: #f8fafc;
        letter-spacing: -0.02em;
    }
    .cx-header p {
        margin: 0.35rem 0 0 0;
        font-size: 0.9rem;
        color: #94a3b8;
    }

    /* KPI Cards */
    .kpi-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
        gap: 1rem;
        margin-bottom: 1.5rem;
    }
    .kpi-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .kpi-label {
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748b;
        margin-bottom: 0.25rem;
    }
    .kpi-value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #0f172a;
        line-height: 1.2;
    }
    .kpi-sub {
        font-size: 0.75rem;
        color: #10b981;
        margin-top: 0.25rem;
        font-weight: 500;
    }

    /* Insight Banner */
    .insight-box {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-left: 4px solid #0284c7;
        padding: 1rem 1.25rem;
        border-radius: 6px;
        margin-bottom: 1rem;
        font-size: 0.9rem;
        color: #1e293b;
    }

    /* Status Indicators */
    .status-badge {
        display: inline-block;
        padding: 0.2rem 0.5rem;
        font-size: 0.75rem;
        font-weight: 600;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Database and Seed Data on first load
if "db_initialized" not in st.session_state:
    init_database()
    seed_initial_data()
    st.session_state.db_initialized = True

# Session State Setup
if "session_id" not in st.session_state:
    st.session_state.session_id = f"SESS-{uuid.uuid4().hex[:8].upper()}"

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Welcome to Apex Global Customer Experience. How can we help you today with our solar inverters, commercial heat pumps, EV fast chargers, or industrial pumping systems?",
            "intent": "General Query",
            "sentiment": "Positive",
            "emotion": "Helpful",
            "urgency": "LOW"
        }
    ]

if "customer_profile" not in st.session_state:
    st.session_state.customer_profile = {
        "name": "Rajesh Sharma",
        "mobile": "+91 98201 12345",
        "email": "rajesh.sharma@example.com",
        "customer_type": "Customer",  # Customer, Dealer, Distributor, Business Partner
        "dealer": "Apex Electro Services",
        "distributor": "Zenith Power Distro",
        "product": "Solar Hybrid Inverter",
        "model": "Apex-Solar-5KVA",
        "serial_number": "SN-SOLAR-88219",
        "location": "Mumbai, Maharashtra",
        "state": "Maharashtra",
        "repeat_complaints": 1
    }

if "last_analysis" not in st.session_state:
    st.session_state.last_analysis = {
        "intent": "General Query",
        "sentiment": "Neutral",
        "sentiment_score": 0,
        "emotion": "Neutral",
        "urgency": "LOW",
        "escalation_required": False,
        "escalation_reason": "",
        "assigned_team": "Level-1 Support"
    }

if "feedback_submitted" not in st.session_state:
    st.session_state.feedback_submitted = False

# Initialize Chatbot Engine
@st.cache_resource
def get_bot():
    return CXChatbot()

bot = get_bot()

# ==============================================================================
# SIDEBAR NAVIGATION & CUSTOMER PROFILE
# ==============================================================================
with st.sidebar:
    # Logo
    logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
    if os.path.exists(logo_path):
        st.image(logo_path, width=180)
    else:
        st.markdown("### ⚡ **APEX GLOBAL CX**")

    st.markdown("**Enterprise CX Suite**")
    st.caption("Dealers · Distributors · Customers · Partners")
    st.markdown("---")

    # Mode Selector
    mode = st.radio(
        "Application Mode",
        ["💬 Customer Chat", "📊 Management Analytics", "📚 Knowledge Base & Docs", "🎙️ Call / Voice Analysis"],
        index=0
    )

    st.markdown("---")

    # Active Customer Details (Section 14)
    with st.expander("👤 Customer Details & Profile", expanded=True):
        st.session_state.customer_profile["name"] = st.text_input("Name", st.session_state.customer_profile["name"])
        st.session_state.customer_profile["customer_type"] = st.selectbox(
            "Account Type",
            ["Customer", "Dealer", "Distributor", "Business Partner"],
            index=["Customer", "Dealer", "Distributor", "Business Partner"].index(st.session_state.customer_profile.get("customer_type", "Customer"))
        )
        st.session_state.customer_profile["mobile"] = st.text_input("Mobile", st.session_state.customer_profile["mobile"])
        st.session_state.customer_profile["product"] = st.selectbox(
            "Product Line",
            ["Solar Hybrid Inverter", "Commercial Heat Pump", "EV Fast Charger", "Industrial Water Pump", "All Apex Lineups"],
            index=0
        )
        st.session_state.customer_profile["model"] = st.text_input("Model", st.session_state.customer_profile["model"])
        st.session_state.customer_profile["serial_number"] = st.text_input("Serial Number", st.session_state.customer_profile["serial_number"])
        st.session_state.customer_profile["location"] = st.text_input("Location", st.session_state.customer_profile["location"])

    # Current NLP Analysis Card (Section 14)
    with st.expander("🔍 Live AI Analysis (Internal)", expanded=True):
        ana = st.session_state.last_analysis
        st.markdown(f"**Intent:** `{ana.get('intent', 'General Query')}`")
        
        # Sentiment Coloration
        s = ana.get("sentiment", "Neutral")
        score = ana.get("sentiment_score", 0)
        s_color = "🟢" if "Positive" in s else ("🔴" if "Negative" in s else "🟡")
        st.markdown(f"**Sentiment:** {s_color} {s} ({score})")
        st.markdown(f"**Emotion:** `{ana.get('emotion', 'Neutral')}`")
        
        # Urgency
        u = ana.get("urgency", "LOW")
        u_color = "🔴" if u in ["CRITICAL", "HIGH"] else "🟢"
        st.markdown(f"**Urgency:** {u_color} `{u}`")

        # Escalation
        if ana.get("escalation_required"):
            st.error(f"⚠️ **Escalation Required: YES**\n\n*{ana.get('escalation_reason')}*")
        else:
            st.success("✅ **Escalation Required: NO**")

    # Sidebar Quick Action Buttons (Section 14)
    st.markdown("---")
    st.markdown("### Action Controls")
    col_sb1, col_sb2 = st.columns(2)
    with col_sb1:
        if st.button("🔄 New Chat", use_container_width=True):
            st.session_state.messages = [
                {
                    "role": "assistant",
                    "content": "Hello! How may I assist you with Apex Global products or services today?",
                    "intent": "General Query",
                    "sentiment": "Neutral",
                    "emotion": "Helpful",
                    "urgency": "LOW"
                }
            ]
            st.session_state.session_id = f"SESS-{uuid.uuid4().hex[:8].upper()}"
            st.session_state.feedback_submitted = False
            st.rerun()

    with col_sb2:
        if st.button("🧹 Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

    if st.button("🚨 Force Escalate Ticket", use_container_width=True):
        esc_id = insert_escalation({
            "ticket_type": "complaint",
            "reference_id": st.session_state.session_id,
            "customer_name": st.session_state.customer_profile["name"],
            "reason": "Manual escalation triggered from Customer Experience Console",
            "urgency": "HIGH"
        })
        st.warning(f"Ticket escalated to Senior Management! Escalation Ref: #{esc_id}")

# ==============================================================================
# MODE 1: CUSTOMER CHAT
# ==============================================================================
if mode == "💬 Customer Chat":
    # Top Banner (Section 14)
    st.markdown("""
    <div class="cx-header">
        <h1>Customer Experience Assistant</h1>
        <p>How can we help you today? · Verified Support for Retail, Dealers & Channel Partners</p>
    </div>
    """, unsafe_allow_html=True)

    # Quick Action Buttons Row (Section 15)
    st.markdown("##### Quick Actions")
    qa_cols = st.columns(8)
    quick_prompts = [
        ("ℹ️ Product Info", "Could you provide technical specifications and warranty details for the Solar Hybrid Inverter?"),
        ("⚠️ Register Complaint", "I want to register an urgent product complaint regarding equipment malfunctioning."),
        ("🛠️ Book a Service", "I would like to book a technician visit for preventive maintenance."),
        ("📜 Warranty Terms", "What is the warranty policy and replacement terms for our units?"),
        ("🔍 Track Complaint", "Can you help me check the current status of my open complaint?"),
        ("🚚 Track Service", "Please track my service request visit schedule."),
        ("📞 Talk to Support", "Please connect me with our regional technical support manager."),
        ("⭐ Give Feedback", "I want to share feedback regarding my recent service experience.")
    ]

    selected_quick_prompt = None
    for i, (label, prompt_text) in enumerate(quick_prompts):
        with qa_cols[i]:
            if st.button(label, key=f"qa_{i}", use_container_width=True):
                selected_quick_prompt = prompt_text

    st.markdown("---")

    # Chat History Container
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.messages:
            role = msg["role"]
            with st.chat_message(role):
                st.markdown(msg["content"])
                if role == "assistant" and "intent" in msg and msg.get("intent") != "General Query":
                    st.caption(f"Intent: {msg['intent']} · Sentiment: {msg.get('sentiment', 'Neutral')} · Urgency: {msg.get('urgency', 'LOW')}")

    # Process Input from user or quick action
    user_input = st.chat_input("Type your question, issue, or complaint here...")
    if selected_quick_prompt:
        user_input = selected_quick_prompt

    if user_input:
        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })

        # Generate response using CX Chatbot
        with st.spinner("Analyzing inquiry and retrieving technical policies..."):
            reply, analysis = bot.generate_response(
                user_message=user_input,
                session_id=st.session_state.session_id,
                customer_profile=st.session_state.customer_profile,
                conversation_history=st.session_state.messages[:-1]
            )

        st.session_state.last_analysis = analysis
        st.session_state.messages.append({
            "role": "assistant",
            "content": reply,
            "intent": analysis.get("intent", "General Query"),
            "sentiment": analysis.get("sentiment", "Neutral"),
            "emotion": analysis.get("emotion", "Neutral"),
            "urgency": analysis.get("urgency", "LOW")
        })

        # Auto-create complaint or service request if high urgency or complaint intent detected
        if analysis.get("intent") in ["Product Complaint", "Product Defect", "Installation Issue", "Emergency / High Priority"] and not st.session_state.get("complaint_created"):
            cid = insert_complaint({
                "customer_name": st.session_state.customer_profile["name"],
                "mobile": st.session_state.customer_profile["mobile"],
                "email": st.session_state.customer_profile["email"],
                "customer_type": st.session_state.customer_profile["customer_type"],
                "product": st.session_state.customer_profile["product"],
                "model": st.session_state.customer_profile["model"],
                "serial_number": st.session_state.customer_profile["serial_number"],
                "dealer": st.session_state.customer_profile["dealer"],
                "distributor": st.session_state.customer_profile["distributor"],
                "location": st.session_state.customer_profile["location"],
                "state": st.session_state.customer_profile.get("state", "Maharashtra"),
                "complaint_category": analysis["intent"],
                "complaint_description": user_input,
                "intent": analysis["intent"],
                "sentiment": analysis["sentiment"],
                "emotion": analysis["emotion"],
                "urgency": analysis["urgency"],
                "status": "Escalated" if analysis.get("escalation_required") else "Open"
            })
            st.session_state.complaint_created = cid
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"📋 **Complaint Registered Successfully**\n\nTicket ID: **{cid}**\nStatus: **{'Escalated to Executive Desk' if analysis.get('escalation_required') else 'Open - Assigned to Technical Support'}**\nPriority: **{analysis['urgency']}**\nSMS update dispatched to {st.session_state.customer_profile['mobile']}.",
                "intent": "Product Complaint"
            })

        st.rerun()

    # Feedback System (Section 16)
    if len(st.session_state.messages) >= 3 and not st.session_state.feedback_submitted:
        st.markdown("---")
        fb_col1, fb_col2 = st.columns([1, 2])
        with fb_col1:
            st.markdown("##### Was this resolution helpful?")
            col_y, col_n = st.columns(2)
            with col_y:
                if st.button("👍 Yes", key="fb_yes", use_container_width=True):
                    insert_feedback({
                        "session_id": st.session_state.session_id,
                        "is_helpful": 1,
                        "rating": 5,
                        "feedback_text": "Customer marked Yes"
                    })
                    st.session_state.feedback_submitted = True
                    st.success("Thank you for your valuable feedback! CSAT updated.")
                    st.rerun()
            with col_n:
                if st.button("👎 No", key="fb_no", use_container_width=True):
                    insert_feedback({
                        "session_id": st.session_state.session_id,
                        "is_helpful": 0,
                        "rating": 2,
                        "feedback_text": "Customer marked No"
                    })
                    st.session_state.feedback_submitted = True
                    st.warning("We apologize for the inconvenience. A supervisor has been alerted to review this interaction.")
                    st.rerun()

# ==============================================================================
# MODE 2: MANAGEMENT ANALYTICS DASHBOARD
# ==============================================================================
elif mode == "📊 Management Analytics":
    st.markdown("""
    <div class="cx-header">
        <h1>Executive CX Management Dashboard</h1>
        <p>Operational KPIs · Sentiment Trends · SLA Breach Analytics · Grounded AI Insights</p>
    </div>
    """, unsafe_allow_html=True)

    # Compute Live Metrics
    kpis = calculate_kpis()
    dists = get_distribution_data()

    # KPI Scorecard (Section 17)
    kpi_cols = st.columns(6)
    with kpi_cols[0]:
        st.metric("Total Conversations", f"{kpis['total_conversations']:,}")
    with kpi_cols[1]:
        st.metric("Active Complaints", f"{kpis['open_complaints']}", delta=f"{kpis['total_complaints']} Total", delta_color="inverse")
    with kpi_cols[2]:
        st.metric("Escalated Cases", f"{kpis['escalated_complaints']}", delta="High Priority", delta_color="inverse")
    with kpi_cols[3]:
        st.metric("Customer CSAT", f"{kpis['csat_score']}%", delta="+2.1% MoM")
    with kpi_cols[4]:
        st.metric("Avg Sentiment Score", f"{kpis['avg_sentiment_score']}", delta="Scale -100 to +100")
    with kpi_cols[5]:
        st.metric("SLA Breach %", f"{kpis['sla_breach_pct']}%", delta="Target < 10%", delta_color="inverse")

    st.markdown("---")

    # Section 19: AI-Generated Management Insights (Data-Grounded)
    st.subheader("💡 Executive Intelligence & AI Observations")
    insights = generate_management_insights(kpis, dists)
    for insight in insights:
        st.markdown(f'<div class="insight-box">{insight}</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Analytics Tabs (Section 18)
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Distributions & Trends", "📋 Complaints Ledger", "🛠️ Service Requests", "🚨 Escalations Queue"])

    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("##### Product-Wise Complaint Distribution")
            if dists["product_dist"]:
                df_prod = pd.DataFrame(dists["product_dist"])
                st.bar_chart(df_prod.set_index("product"))

        with c2:
            st.markdown("##### Customer Intent Breakdown")
            if dists["intent_dist"]:
                df_intent = pd.DataFrame(dists["intent_dist"])
                st.bar_chart(df_intent.set_index("intent"))

        c3, c4 = st.columns(2)
        with c3:
            st.markdown("##### Regional State-Wise Distribution")
            if dists["state_dist"]:
                df_state = pd.DataFrame(dists["state_dist"])
                st.bar_chart(df_state.set_index("state"))

        with c4:
            st.markdown("##### Urgency Severity Split")
            if dists["urgency_dist"]:
                df_urg = pd.DataFrame(dists["urgency_dist"])
                st.bar_chart(df_urg.set_index("urgency"))

    with tab2:
        st.markdown("##### Master Complaints Database (SQLite)")
        # Filters (Section 26)
        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1:
            f_status = st.selectbox("Filter Status", ["All", "Open", "In Progress", "Resolved", "Escalated", "Closed"])
        with f_col2:
            f_urgency = st.selectbox("Filter Urgency", ["All", "LOW", "MEDIUM", "HIGH", "CRITICAL"])
        with f_col3:
            f_product = st.selectbox("Filter Product", ["All", "Solar Hybrid Inverter", "Commercial Heat Pump", "EV Fast Charger", "Industrial Water Pump"])

        complaints_data = get_complaints_list(filters={"status": f_status, "urgency": f_urgency, "product": f_product})
        if complaints_data:
            df_c = pd.DataFrame(complaints_data)
            display_cols = ["complaint_id", "date", "customer_name", "customer_type", "product", "model", "complaint_category", "sentiment", "urgency", "status", "assigned_team"]
            st.dataframe(df_c[[c for c in display_cols if c in df_c.columns]], use_container_width=True)
        else:
            st.info("No complaints found matching the selected filters.")

    with tab3:
        st.markdown("##### Service Requests & Field Engineer Allocations")
        conn = get_connection()
        srs = pd.read_sql_query("SELECT * FROM service_requests ORDER BY id DESC", conn)
        conn.close()
        st.dataframe(srs, use_container_width=True)

    with tab4:
        st.markdown("##### Priority Escalations & Critical Safety Alerts")
        conn = get_connection()
        escs = pd.read_sql_query("SELECT * FROM escalations ORDER BY id DESC", conn)
        conn.close()
        st.dataframe(escs, use_container_width=True)

# ==============================================================================
# MODE 3: KNOWLEDGE BASE & DOCUMENT INGESTION
# ==============================================================================
elif mode == "📚 Knowledge Base & Docs":
    st.markdown("""
    <div class="cx-header">
        <h1>Technical Knowledge Base & RAG Ingestion</h1>
        <p>Upload Product Manuals, Warranty Policies, FAQs (PDF, DOCX, TXT, CSV, XLSX)</p>
    </div>
    """, unsafe_allow_html=True)

    kb = get_knowledge_base()

    col_up, col_list = st.columns([1, 1])

    with col_up:
        st.subheader("📤 Document Upload")
        uploaded_files = st.file_uploader(
            "Upload company documents to extend AI knowledge base",
            type=["pdf", "docx", "txt", "csv", "xlsx"],
            accept_multiple_files=True
        )

        if uploaded_files:
            upload_dir = os.path.join(os.path.dirname(__file__), "uploads")
            os.makedirs(upload_dir, exist_ok=True)
            for f in uploaded_files:
                save_path = os.path.join(upload_dir, f.name)
                with open(save_path, "wb") as out:
                    out.write(f.getbuffer())
                doc_id = kb.parse_uploaded_file(save_path, f.name)
                if doc_id:
                    st.success(f"Successfully parsed and indexed: {f.name} (Ref: {doc_id})")
                else:
                    st.warning(f"File uploaded to {save_path}. Text extracted for indexing.")

        st.markdown("---")
        st.markdown("##### Test RAG Knowledge Retrieval")
        search_query = st.text_input("Enter search query to test RAG similarity matching:", "Error E04 in solar inverter")
        if search_query:
            results = kb.search(search_query, top_k=3)
            for r in results:
                st.markdown(f"**[{r['title']} - {r['category']}]** (Chunk: `{r['chunk_id']}`)")
                st.caption(r['text'])
                st.markdown("---")

    with col_list:
        st.subheader("📚 Verified Technical Knowledge Documents")
        for doc in kb.documents:
            with st.expander(f"📄 {doc['title']} ({doc['category']})"):
                st.markdown(f"**Document ID:** `{doc['doc_id']}`")
                st.write(doc['content'])

# ==============================================================================
# MODE 4: VOICE / CALL RECORDING ANALYSIS
# ==============================================================================
elif mode == "🎙️ Call / Voice Analysis":
    st.markdown("""
    <div class="cx-header">
        <h1>Voice & Audio Call Analysis Center (Ready)</h1>
        <p>Speech-to-Text Transcription · Speaker Diarization · Agent Empathy & Call Quality Auditing</p>
    </div>
    """, unsafe_allow_html=True)

    analyzer = VoiceCallAnalyzer()

    col_aud, col_rep = st.columns([1, 2])

    with col_aud:
        st.subheader("Audio File Ingestion")
        audio_file = st.file_uploader("Upload call recording (MP3, WAV, M4A)", type=["mp3", "wav", "m4a"])
        demo_btn = st.button("Load Representative Audio Analysis (Thane Solar E04 Case)", use_container_width=True)

    with col_rep:
        if audio_file or demo_btn:
            fname = audio_file.name if audio_file else "call_recording_thane_inverter_e04.wav"
            report = analyzer.analyze_audio_file(fname)

            st.subheader(f"Call Audit Report: `{report.call_id}`")
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            with m_col1:
                st.metric("Call Duration", f"{report.duration_seconds}s")
            with m_col2:
                st.metric("Agent Empathy Score", f"{report.agent_empathy_score}%")
            with m_col3:
                st.metric("Call Quality Score", f"{report.call_quality_score}%")
            with m_col4:
                st.metric("Sentiment Score", f"{report.sentiment_score}/100")

            st.markdown(f"**Call Summary:** {report.call_summary}")
            st.markdown(f"**Caller Phone:** `{report.caller_phone}` · **Agent:** `{report.agent_id}` · **Format:** `{report.audio_format}`")

            st.markdown("##### 📝 Speaker-Diarized Transcript")
            for ut in report.transcript:
                badge = "👤 Customer" if ut.speaker == "Customer" else "🎧 Agent"
                st.markdown(f"**[{ut.start_sec if hasattr(ut, 'start_sec') else ut.start_time_sec:.1f}s - {ut.end_sec if hasattr(ut, 'end_sec') else ut.end_time_sec:.1f}s] {badge}:** {ut.text}")

            st.markdown("##### 📌 Generated Action Items")
            for item in report.action_items:
                st.markdown(f"- {item}")
        else:
            st.info("Upload an audio recording or click 'Load Representative Audio Analysis' to inspect call audit metrics.")
