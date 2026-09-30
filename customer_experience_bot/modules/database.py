"""
Database Module for Enterprise Customer Experience (CX) Suite.
Manages SQLite persistence for customers, conversations, messages,
complaints, service requests, feedback, escalations, and analytics.
"""

import os
import sqlite3
import datetime
from typing import List, Dict, Any, Optional

DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "cx_database.sqlite")

def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Creates a thread-safe connection to the SQLite database."""
    target_path = db_path or os.getenv("DATABASE_PATH", DEFAULT_DB_PATH)
    # Ensure directory exists
    os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
    conn = sqlite3.connect(target_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_database(db_path: Optional[str] = None):
    """Initializes the database schema with all required enterprise tables."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # 1. Customers Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id TEXT UNIQUE,
        name TEXT NOT NULL,
        mobile TEXT,
        email TEXT,
        customer_type TEXT DEFAULT 'Customer', -- Customer, Dealer, Distributor, Business Partner
        dealer_name TEXT,
        distributor_name TEXT,
        location TEXT,
        state TEXT,
        sales_head TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 2. Conversations Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS conversations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT UNIQUE NOT NULL,
        customer_id TEXT,
        start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        intent_summary TEXT,
        sentiment_summary TEXT,
        status TEXT DEFAULT 'Active', -- Active, Escalated, Closed, Transferred
        FOREIGN KEY(customer_id) REFERENCES customers(customer_id)
    )
    """)

    # 3. Messages Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        role TEXT NOT NULL, -- user, assistant, system
        content TEXT NOT NULL,
        intent TEXT,
        sentiment TEXT,
        emotion TEXT,
        urgency TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(session_id) REFERENCES conversations(session_id)
    )
    """)

    # 4. Complaints Table (Structured as per Section 9)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS complaints (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        complaint_id TEXT UNIQUE NOT NULL, -- CX-YYYYMMDD-XXXX
        customer_name TEXT NOT NULL,
        mobile TEXT,
        email TEXT,
        customer_type TEXT DEFAULT 'Customer',
        product TEXT NOT NULL,
        model TEXT,
        serial_number TEXT,
        dealer TEXT,
        distributor TEXT,
        location TEXT,
        state TEXT,
        complaint_category TEXT NOT NULL,
        complaint_description TEXT NOT NULL,
        intent TEXT,
        sentiment TEXT,
        emotion TEXT,
        urgency TEXT DEFAULT 'MEDIUM',
        date TEXT NOT NULL,
        status TEXT DEFAULT 'Open', -- Open, Assigned, In Progress, Waiting for Customer, Resolved, Closed, Escalated
        assigned_team TEXT DEFAULT 'Level-1 Technical Support',
        resolution TEXT,
        closure_date TEXT
    )
    """)

    # 5. Service Requests Table (Section 10)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS service_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_id TEXT UNIQUE NOT NULL, -- SR-YYYYMMDD-XXXX
        customer_name TEXT NOT NULL,
        mobile TEXT,
        email TEXT,
        product TEXT NOT NULL,
        model TEXT,
        serial_number TEXT,
        issue TEXT NOT NULL,
        location TEXT,
        preferred_visit_date TEXT,
        contact_number TEXT,
        status TEXT DEFAULT 'Pending Visit', -- Pending Visit, Assigned Engineer, Technician Dispatched, Completed, Cancelled
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        resolved_at TIMESTAMP
    )
    """)

    # 6. Feedback Table (Section 16)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        complaint_id TEXT,
        is_helpful INTEGER, -- 1 for Yes, 0 for No
        rating INTEGER, -- 1 to 5
        csat_score REAL, -- 0 to 100
        feedback_text TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 7. Escalations Table (Section 11)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS escalations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_type TEXT NOT NULL, -- complaint, service_request, conversation
        reference_id TEXT NOT NULL,
        customer_name TEXT,
        reason TEXT NOT NULL,
        urgency TEXT DEFAULT 'HIGH',
        status TEXT DEFAULT 'Pending Management Review', -- Pending Management Review, Under Investigation, Action Taken, Resolved
        escalated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        resolved_at TIMESTAMP
    )
    """)

    # 8. Analytics Aggregation Cache
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS analytics_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_type TEXT NOT NULL,
        event_key TEXT,
        event_val REAL,
        metadata_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

def generate_complaint_id(db_path: Optional[str] = None) -> str:
    """Generates a sequential enterprise complaint ID in CX-YYYYMMDD-XXXX format."""
    today_str = datetime.datetime.now().strftime("%Y%m%d")
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM complaints WHERE date LIKE ?", (f"{datetime.datetime.now().strftime('%Y-%m-%d')}%",))
    count = cursor.fetchone()[0] + 1
    conn.close()
    return f"CX-{today_str}-{count:04d}"

def generate_service_request_id(db_path: Optional[str] = None) -> str:
    """Generates a sequential enterprise service request ID in SR-YYYYMMDD-XXXX format."""
    today_str = datetime.datetime.now().strftime("%Y%m%d")
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM service_requests WHERE created_at LIKE ?", (f"{datetime.datetime.now().strftime('%Y-%m-%d')}%",))
    count = cursor.fetchone()[0] + 1
    conn.close()
    return f"SR-{today_str}-{count:04d}"

def insert_complaint(record: Dict[str, Any], db_path: Optional[str] = None) -> str:
    """Inserts a new structured complaint and returns the Complaint ID."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    
    complaint_id = record.get("complaint_id") or generate_complaint_id(db_path)
    today = record.get("date") or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    INSERT INTO complaints (
        complaint_id, customer_name, mobile, email, customer_type,
        product, model, serial_number, dealer, distributor,
        location, state, complaint_category, complaint_description,
        intent, sentiment, emotion, urgency, date, status,
        assigned_team, resolution, closure_date
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        complaint_id,
        record.get("customer_name", "Valued Customer"),
        record.get("mobile", ""),
        record.get("email", ""),
        record.get("customer_type", "Customer"),
        record.get("product", "General Lineup"),
        record.get("model", ""),
        record.get("serial_number", ""),
        record.get("dealer", ""),
        record.get("distributor", ""),
        record.get("location", ""),
        record.get("state", ""),
        record.get("complaint_category", "General Service"),
        record.get("complaint_description", ""),
        record.get("intent", "Product Complaint"),
        record.get("sentiment", "Negative"),
        record.get("emotion", "Frustrated"),
        record.get("urgency", "MEDIUM"),
        today,
        record.get("status", "Open"),
        record.get("assigned_team", "Technical Support Team"),
        record.get("resolution", ""),
        record.get("closure_date", "")
    ))
    conn.commit()
    conn.close()
    return complaint_id

def insert_service_request(record: Dict[str, Any], db_path: Optional[str] = None) -> str:
    """Inserts a new service request and returns the Request ID."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    req_id = record.get("request_id") or generate_service_request_id(db_path)
    cursor.execute("""
    INSERT INTO service_requests (
        request_id, customer_name, mobile, email, product, model,
        serial_number, issue, location, preferred_visit_date,
        contact_number, status
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        req_id,
        record.get("customer_name", "Customer"),
        record.get("mobile", ""),
        record.get("email", ""),
        record.get("product", ""),
        record.get("model", ""),
        record.get("serial_number", ""),
        record.get("issue", ""),
        record.get("location", ""),
        record.get("preferred_visit_date", ""),
        record.get("contact_number") or record.get("mobile", ""),
        record.get("status", "Pending Visit")
    ))
    conn.commit()
    conn.close()
    return req_id

def insert_escalation(record: Dict[str, Any], db_path: Optional[str] = None) -> int:
    """Logs an automated or manual management escalation."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO escalations (
        ticket_type, reference_id, customer_name, reason, urgency, status
    ) VALUES (?, ?, ?, ?, ?, ?)
    """, (
        record.get("ticket_type", "complaint"),
        record.get("reference_id", "N/A"),
        record.get("customer_name", "Anonymous"),
        record.get("reason", "Triggered by CX Escalation Engine"),
        record.get("urgency", "HIGH"),
        record.get("status", "Pending Management Review")
    ))
    escalation_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return escalation_id

def insert_feedback(record: Dict[str, Any], db_path: Optional[str] = None):
    """Records customer feedback and calculates CSAT score."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    is_helpful = 1 if record.get("is_helpful") else 0
    rating = record.get("rating", 5 if is_helpful else 2)
    csat_score = (rating / 5.0) * 100.0

    cursor.execute("""
    INSERT INTO feedback (session_id, complaint_id, is_helpful, rating, csat_score, feedback_text)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        record.get("session_id", ""),
        record.get("complaint_id", ""),
        is_helpful,
        rating,
        csat_score,
        record.get("feedback_text", "")
    ))
    conn.commit()
    conn.close()

def log_conversation_message(session_id: str, role: str, content: str,
                             intent: str = "", sentiment: str = "",
                             emotion: str = "", urgency: str = "",
                             db_path: Optional[str] = None):
    """Logs a single message in the conversation history with its NLP tags."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    # Ensure conversation row exists
    cursor.execute("""
    INSERT INTO conversations (session_id, start_time, last_active, intent_summary, sentiment_summary)
    VALUES (?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ?, ?)
    ON CONFLICT(session_id) DO UPDATE SET
        last_active = CURRENT_TIMESTAMP,
        intent_summary = excluded.intent_summary,
        sentiment_summary = excluded.sentiment_summary
    """, (session_id, intent, sentiment))

    cursor.execute("""
    INSERT INTO messages (session_id, role, content, intent, sentiment, emotion, urgency)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (session_id, role, content, intent, sentiment, emotion, urgency))
    conn.commit()
    conn.close()

def get_complaints_list(filters: Optional[Dict[str, Any]] = None, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves complaints matching optional filter criteria."""
    conn = get_connection(db_path)
    cursor = conn.cursor()
    query = "SELECT * FROM complaints WHERE 1=1"
    params = []

    if filters:
        if filters.get("status") and filters["status"] != "All":
            query += " AND status = ?"
            params.append(filters["status"])
        if filters.get("urgency") and filters["urgency"] != "All":
            query += " AND urgency = ?"
            params.append(filters["urgency"])
        if filters.get("product") and filters["product"] != "All":
            query += " AND product = ?"
            params.append(filters["product"])
        if filters.get("state") and filters["state"] != "All":
            query += " AND state = ?"
            params.append(filters["state"])

    query += " ORDER BY id DESC"
    cursor.execute(query, params)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def seed_initial_data(db_path: Optional[str] = None):
    """
    Populates realistic historical complaints, service requests, feedback,
    and escalations so management analytics have immediate, high-fidelity data.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM complaints")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return  # Already seeded

    # Seed Historical Complaints
    sample_complaints = [
        ("CX-20260901-0001", "Rajesh Sharma", "+91 98201 12345", "rajesh.sharma@example.com", "Customer", "Solar Hybrid Inverter", "Apex-Solar-5KVA", "SN-SOLAR-88219", "Apex Electro Services", "Zenith Power Distro", "Mumbai", "Maharashtra", "Technical Support", "Inverter error code E04 during grid switchover.", "Technical Support", "Negative", "Frustrated", "HIGH", "2026-09-01 10:15:00", "Resolved", "Level-2 Field Support", "Firmware updated to v3.2.1 and capacitor replaced.", "2026-09-03"),
        ("CX-20260902-0002", "Sunita Patel", "+91 98765 43210", "sunita.patel@example.com", "Customer", "Commercial Heat Pump", "Apex-HP-10KW", "SN-HEAT-44102", "Surat Energy Hub", "Gujarat Power Grid", "Surat", "Gujarat", "Installation Issue", "Compressor vibration noise exceeding threshold in basement.", "Installation Issue", "Negative", "Anxious", "MEDIUM", "2026-09-02 11:30:00", "Resolved", "HVAC Installation Team", "Anti-vibration mount pads installed and realigned.", "2026-09-04"),
        ("CX-20260904-0003", "Metro Solar Enterprises", "+91 98101 99220", "metro.solar@dealers.apex.com", "Dealer", "Solar Hybrid Inverter", "Apex-Solar-5KVA", "DEAL-INV-001", "Self", "Delhi Distributors Ltd", "New Delhi", "Delhi", "Dealer Complaint", "Delayed replacement stock for 8 defective control boards.", "Spare Parts", "Very Negative", "Angry", "HIGH", "2026-09-04 14:20:00", "In Progress", "Supply Chain & Logistics", "Priority air dispatch scheduled from Pune warehouse.", ""),
        ("CX-20260906-0004", "Vikas Verma", "+91 94120 55432", "vikas.verma@example.com", "Customer", "EV Fast Charger", "Apex-EV-Fast-60", "SN-EVFC-99120", "Northern Power Store", "Delhi Distributors Ltd", "New Delhi", "Delhi", "Product Defect", "Smoke detected from connector port during 60kW DC charging.", "Emergency / High Priority", "Very Negative", "Angry", "CRITICAL", "2026-09-06 16:45:00", "Escalated", "Safety & Engineering Core", "Unit decommissioned immediately, replacement unit dispatched.", ""),
        ("CX-20260908-0005", "Pooja Hegde", "+91 97411 88990", "pooja.hegde@example.com", "Customer", "Solar Hybrid Inverter", "Apex-Solar-10KVA", "SN-SOLAR-77312", "Bangalore Solar Mart", "Karnataka Power Logistics", "Bengaluru", "Karnataka", "Service Request", "Routine annual AMC preventive maintenance check required.", "Service Request", "Positive", "Satisfied", "LOW", "2026-09-08 09:10:00", "Closed", "Field Service Bengaluru", "All string voltages calibrated, dust cleaning completed.", "2026-09-09"),
        ("CX-20260910-0006", "Anand Kulkarni", "+91 98220 33441", "anand.kulkarni@example.com", "Customer", "Industrial Water Pump", "Apex-Pump-7HP", "SN-PUMP-11234", "Pune Battery & Solar", "Western Grid Supply", "Pune", "Maharashtra", "Product Complaint", "Pump thermal cut-off tripping repeatedly within 15 minutes.", "Product Complaint", "Negative", "Frustrated", "HIGH", "2026-09-10 13:00:00", "Resolved", "Industrial Systems Team", "Thermal relay sensor replaced, motor rewinding inspected.", "2026-09-13"),
        ("CX-20260912-0007", "Deccan Green Tech", "+91 94401 22334", "deccan.tech@dealers.apex.com", "Dealer", "Commercial Heat Pump", "Apex-HP-15KW", "DEAL-INV-002", "Self", "Southern Apex Hub", "Hyderabad", "Telangana", "Distributor Complaint", "Invoicing mismatch in quarterly dealer incentive rebate.", "Pricing Query", "Negative", "Disappointed", "MEDIUM", "2026-09-12 15:40:00", "Resolved", "Dealer Accounts & Finance", "Credit note CN-2026-081 issued for INR 48,500.", "2026-09-14"),
        ("CX-20260915-0008", "Meera Nair", "+91 98470 66123", "meera.nair@example.com", "Customer", "Solar Hybrid Inverter", "Apex-Solar-3KVA", "SN-SOLAR-33901", "Kochi Green Solutions", "Southern Apex Hub", "Kochi", "Kerala", "Warranty Query", "Confirmation needed regarding 5-year extended warranty certificate.", "Warranty Query", "Neutral", "Neutral", "LOW", "2026-09-15 11:20:00", "Closed", "Customer Support Level-1", "Warranty certificate emailed and verified on portal.", "2026-09-15"),
        ("CX-20260917-0009", "Rohan Deshmukh", "+91 99203 44556", "rohan.deshmukh@example.com", "Customer", "Solar Hybrid Inverter", "Apex-Solar-5KVA", "SN-SOLAR-88240", "Apex Electro Services", "Zenith Power Distro", "Thane", "Maharashtra", "Delivery Issue", "Replacement battery pack delayed by 12 days, no update.", "Delivery Issue", "Very Negative", "Angry", "HIGH", "2026-09-17 17:30:00", "Escalated", "Logistics Operations Head", "Express courier assigned, delivery completed on 19th Sep.", "2026-09-19"),
        ("CX-20260920-0010", "Suresh Reddy", "+91 98480 77112", "suresh.reddy@example.com", "Customer", "Industrial Water Pump", "Apex-Pump-10HP", "SN-PUMP-99432", "Deccan Green Tech", "Southern Apex Hub", "Secunderabad", "Telangana", "Technical Support", "Impeller cavitation noise during low head pressure operations.", "Technical Support", "Negative", "Confused", "MEDIUM", "2026-09-20 10:00:00", "In Progress", "Field Service Hyderabad", "Throttling valve adjustment proposed, technician visiting.", ""),
        ("CX-20260922-0011", "Gujarat Energy Traders", "+91 98250 88771", "gujarat.energy@dealers.apex.com", "Dealer", "EV Fast Charger", "Apex-EV-Dual-120", "DEAL-INV-003", "Self", "Gujarat Power Grid", "Ahmedabad", "Gujarat", "Dealer Complaint", "Customer app sync failing on 4 newly commissioned charge points.", "Technical Support", "Negative", "Frustrated", "HIGH", "2026-09-22 14:15:00", "Resolved", "Software & IoT Team", "OCPP gateway endpoint restored and reconnected.", "2026-09-23"),
        ("CX-20260925-0012", "Harpreet Singh", "+91 98140 12890", "harpreet.singh@example.com", "Customer", "Solar Hybrid Inverter", "Apex-Solar-10KVA", "SN-SOLAR-66102", "Chandigarh Energy Point", "Punjab Power Corp", "Ludhiana", "Punjab", "Service Request", "Solar technician visit requested for net metering sync failure.", "Service Request", "Negative", "Frustrated", "HIGH", "2026-09-25 12:45:00", "Open", "Field Service North", "Service technician ticket #SR-20260925-0002 assigned.", ""),
        ("CX-20260927-0013", "Kavita Iyer", "+91 98410 99881", "kavita.iyer@example.com", "Customer", "EV Fast Charger", "Apex-EV-Fast-30", "SN-EVFC-55210", "Chennai Eco Power", "Southern Apex Hub", "Chennai", "Tamil Nadu", "Product Defect", "Screen touch panel frozen, unable to terminate charging.", "Product Defect", "Negative", "Anxious", "MEDIUM", "2026-09-27 16:10:00", "Open", "Field Service Chennai", "Display PCB replacement allocated under warranty.", ""),
        ("CX-20260928-0014", "Zenith Power Distro", "+91 98200 11000", "zenith.distro@distro.apex.com", "Distributor", "All Apex Lineups", "Full Range", "DIST-HQ-01", "None", "Self", "Mumbai", "Maharashtra", "Distributor Complaint", "Warehouse pallet packaging damage in container #MH-04-TR-918.", "Delivery Issue", "Negative", "Disappointed", "HIGH", "2026-09-28 11:00:00", "In Progress", "Warehouse Quality Audit", "Insurance claim surveyor scheduled for joint inspection.", ""),
        ("CX-20260929-0015", "Amitabh Sen (VP Ops)", "+91 98300 44111", "amitabh.sen@apexglobal.com", "Business Partner", "Solar Hybrid Inverter", "Apex-Solar-5KVA", "SN-AUDIT-09", "Apex Electro Services", "Zenith Power Distro", "Kolkata", "West Bengal", "Emergency / High Priority", "Spike in inverter relay latching failures reported in eastern territory.", "Product Defect", "Very Negative", "Urgent", "CRITICAL", "2026-09-29 09:30:00", "Escalated", "Executive Quality Taskforce", "Batch recall inspection order issued for capacitors dated Aug 2026.", "")
    ]

    cursor.executemany("""
    INSERT INTO complaints (
        complaint_id, customer_name, mobile, email, customer_type,
        product, model, serial_number, dealer, distributor,
        location, state, complaint_category, complaint_description,
        intent, sentiment, emotion, urgency, date, status,
        assigned_team, resolution, closure_date
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, sample_complaints)

    # Seed Service Requests
    sample_srs = [
        ("SR-20260901-0001", "Rajesh Sharma", "+91 98201 12345", "rajesh.sharma@example.com", "Solar Hybrid Inverter", "Apex-Solar-5KVA", "SN-SOLAR-88219", "Grid sync relay replacement and firmware flash", "Mumbai", "2026-09-02", "+91 98201 12345", "Completed", "2026-09-01 10:20:00", "2026-09-03 16:00:00"),
        ("SR-20260908-0002", "Pooja Hegde", "+91 97411 88990", "pooja.hegde@example.com", "Solar Hybrid Inverter", "Apex-Solar-10KVA", "SN-SOLAR-77312", "Preventive Maintenance and String Testing", "Bengaluru", "2026-09-09", "+91 97411 88990", "Completed", "2026-09-08 09:15:00", "2026-09-09 14:30:00"),
        ("SR-20260925-0003", "Harpreet Singh", "+91 98140 12890", "harpreet.singh@example.com", "Solar Hybrid Inverter", "Apex-Solar-10KVA", "SN-SOLAR-66102", "Net metering bi-directional inverter synchronization", "Ludhiana", "2026-09-28", "+91 98140 12890", "Technician Dispatched", "2026-09-25 12:50:00", None),
        ("SR-20260927-0004", "Kavita Iyer", "+91 98410 99881", "kavita.iyer@example.com", "EV Fast Charger", "Apex-EV-Fast-30", "SN-EVFC-55210", "Touchscreen digitizer panel swap under warranty", "Chennai", "2026-09-30", "+91 98410 99881", "Assigned Engineer", "2026-09-27 16:15:00", None),
        ("SR-20260929-0005", "Sunita Patel", "+91 98765 43210", "sunita.patel@example.com", "Commercial Heat Pump", "Apex-HP-10KW", "SN-HEAT-44102", "Refrigerant pressure top-up and seal check", "Surat", "2026-10-02", "+91 98765 43210", "Pending Visit", "2026-09-29 11:20:00", None)
    ]

    cursor.executemany("""
    INSERT INTO service_requests (
        request_id, customer_name, mobile, email, product, model,
        serial_number, issue, location, preferred_visit_date,
        contact_number, status, created_at, resolved_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, sample_srs)

    # Seed Feedback
    sample_feedback = [
        ("sess-101", "CX-20260901-0001", 1, 5, 100.0, "Engineer arrived on time and solved inverter error code fast.", "2026-09-03 17:00:00"),
        ("sess-102", "CX-20260902-0002", 1, 4, 80.0, "Vibration fixed promptly. App interface is very convenient.", "2026-09-04 18:30:00"),
        ("sess-103", "CX-20260908-0005", 1, 5, 100.0, "Excellent preventive maintenance support.", "2026-09-09 15:00:00"),
        ("sess-104", "CX-20260910-0006", 1, 4, 80.0, "Pump is working fine now after thermal relay change.", "2026-09-13 18:00:00"),
        ("sess-105", "CX-20260912-0007", 1, 4, 80.0, "Finance team credit note resolved our dealer ledger.", "2026-09-14 16:30:00"),
        ("sess-106", "CX-20260917-0009", 0, 2, 40.0, "Delayed shipment caused significant inconvenience.", "2026-09-19 20:00:00"),
        ("sess-107", "CX-20260922-0011", 1, 5, 100.0, "Fast software team response for OCPP gateway.", "2026-09-23 18:00:00")
    ]
    cursor.executemany("""
    INSERT INTO feedback (session_id, complaint_id, is_helpful, rating, csat_score, feedback_text, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, sample_feedback)

    # Seed Escalations
    sample_escalations = [
        ("complaint", "CX-20260906-0004", "Vikas Verma", "CRITICAL safety alert: smoke reported from EV charging port", "CRITICAL", "Action Taken", "2026-09-06 16:50:00", "2026-09-07 10:00:00"),
        ("complaint", "CX-20260917-0009", "Rohan Deshmukh", "Logistics SLA breached over 12 days for battery pack dispatch", "HIGH", "Resolved", "2026-09-17 17:35:00", "2026-09-19 12:00:00"),
        ("complaint", "CX-20260929-0015", "Amitabh Sen (VP Ops)", "Territory-wide relay latching failure spike in eastern zone", "CRITICAL", "Pending Management Review", "2026-09-29 09:35:00", None)
    ]
    cursor.executemany("""
    INSERT INTO escalations (ticket_type, reference_id, customer_name, reason, urgency, status, escalated_at, resolved_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, sample_escalations)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_database()
    seed_initial_data()
    print("Database initialized and seeded successfully.")
