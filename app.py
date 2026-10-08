import streamlit as st
import google.generativeai as genai
import pandas as pd
import sqlite3
import json
import plotly.express as px

# --- PAGE SETUP ---
st.set_page_config(page_title="Project Risk Tracking Assistant", page_icon="⚡", layout="wide")
st.title("⚡ Project Risk Tracking Assistant")
st.caption("Agentic workflow automation, dynamic database tracking, and executive risk analytics.")

# --- DATABASE SETUP (SQLite) ---
conn = sqlite3.connect('projects.db', check_same_thread=False)
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS risk_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_name TEXT,
        owner TEXT,
        risk_summary TEXT,
        status TEXT,
        risk_score INTEGER,
        blockers TEXT,
        raw_update TEXT
    )
''')
conn.commit()

# --- INITIAL SEED DATA (Populates automatically if empty) ---
c.execute("SELECT COUNT(*) FROM risk_logs")
if c.fetchone()[0] == 0:
    seed_records = [
        ("Payment Gateway", "Alex M.", "Awaiting production credentials for Stripe webhooks from Security.", "Blocked", 9, "Security credential approval", "Initial seed data"),
        ("User Dashboard", "Mruga G.", "Completed dark mode UI and integrated user preferences screen.", "On Track", 1, "None", "Initial seed data"),
        ("Mobile Data Sync", "Devin K.", "Database sync dropping packets due to iOS background execution timeouts.", "At Risk", 7, "iOS execution limits", "Initial seed data"),
        ("Auth Service", "Sarah T.", "Refactoring OAuth2 login flow; waiting on Okta sandbox API availability.", "At Risk", 6, "Okta API downtime", "Initial seed data")
    ]
    c.executemany('''
        INSERT INTO risk_logs (project_name, owner, risk_summary, status, risk_score, blockers, raw_update)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', seed_records)
    conn.commit()

# --- API KEY CONFIGURATION ---
api_key = st.secrets.get("GEMINI_API_KEY") if "GEMINI_API_KEY" in st.secrets else None
if not api_key:
    api_key = st.sidebar.text_input("Enter Gemini API Key:", type="password")

if api_key:
    genai.configure(api_key=api_key)
    # Using lightweight high-throughput Gemini model
    model = genai.GenerativeModel('gemini-2.0-flash-lite')

    # --- DATABASE FUNCTIONS ---
    def load_data():
        df = pd.read_sql_query("""
            SELECT 
                id, 
                project_name AS 'Project Name', 
                owner AS 'Owner', 
                status AS 'Status', 
                risk_score AS 'Risk Score', 
                blockers AS 'Blockers', 
                risk_summary AS 'Risk Summary' 
            FROM risk_logs ORDER BY id DESC
        """, conn)
        return df

    def add_data(project_name, owner, risk_summary, status, risk_score, blockers, raw):
        c.execute('''
            INSERT INTO risk_logs (project_name, owner, risk_summary, status, risk_score, blockers, raw_update)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (project_name, owner, risk_summary, status, risk_score, blockers, raw))
        conn.commit()

    def update_db_record(record_id, display_column, new_value):
        col_map = {
            'Project Name': 'project_name',
            'Owner': 'owner',
            'Status': 'status',
            'Risk Score': 'risk_score',
            'Blockers': 'blockers',
            'Risk Summary': 'risk_summary'
        }
        db_col = col_map.get(display_column, display_column)
        c.execute(f"UPDATE risk_logs SET {db_col} = ? WHERE id = ?", (new_value, record_id))
        conn.commit()

    # Load current data
    df = load_data()
    existing_projects = df['Project Name'].unique().tolist() if not df.empty else []
    existing_owners = df['Owner'].unique().tolist() if not df.empty else []

    # --- SIDEBAR: SINGLE UPDATE ---
    st.sidebar.header("➕ Add Single Update")
    project_options = existing_projects + ["➕ Add New Project..."]
    selected_project = st.sidebar.selectbox("Select Project", project_options)
    project_name = st.sidebar.text_input("Enter New Project Name") if selected_project == "➕ Add New Project..." else selected_project

    owner_options = existing_owners + ["➕ Add New Owner..."]
    selected_owner = st.sidebar.selectbox("Select Owner", owner_options)
    owner_name = st.sidebar.text_input("Enter New Owner Name") if selected_owner == "➕ Add New Owner..." else selected_owner

    update_text = st.sidebar.text_area("Raw Status Update / Work Log")

    if st.sidebar.button("Analyze & Save Update"):
        if update_text and project_name and owner_name:
            prompt = f"""
            Analyze this update and return ONLY a JSON object:
            {{"risk_summary": "1-sentence summary", "status": "On Track", "risk_score": 1, "blockers": "None"}}
            Update text: "{update_text}"
            """
            with st.spinner("AI analyzing update..."):
                try:
                    res = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
                    parsed = json.loads(res.text)
                    add_data(project_name, owner_name, parsed.get("risk_summary", "N/A"), 
                             parsed.get("status", "On Track"), int(parsed.get("risk_score", 1)), 
                             parsed.get("blockers", "None"), update_text)
                    st.sidebar.success("Saved to database!")
                    st.rerun()
                except Exception as e:
                    st.sidebar.error(f"Error parsing AI response: {e}")
        else:
            st.sidebar.warning("Ensure Project, Owner, and Update text are filled out.")

    st.sidebar.divider()

    # --- SIDEBAR: BULK MEETING INGESTION ---
    st.sidebar.header("🎙️ Bulk Meeting Ingest")
    transcript_text = st.sidebar.text_area("Paste Zoom/Meeting Transcript:", height=150)
    if st.sidebar.button("Extract All Updates"):
        if transcript_text:
            prompt = f"""
            Extract EVERY project update from this transcript. Return ONLY a valid JSON ARRAY of objects.
            Format: [{{"project_name": "Name", "owner": "Name", "risk_summary": "...", "status": "On Track", "risk_score": 1, "blockers": "None"}}]
            Transcript: "{transcript_text}"
            """
            with st.spinner("AI mapping meeting notes..."):
                try:
                    res = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
                    parsed_array = json.loads(res.text)
                    for item in parsed_array:
                        add_data(item.get("project_name", "Unknown"), item.get("owner", "Unknown"), 
                                 item.get("risk_summary", ""), item.get("status", "On Track"), 
                                 int(item.get("risk_score", 1)), item.get("blockers", "None"), transcript_text)
                    st.sidebar.success(f"Ingested {len(parsed_array)} updates!")
                    st.rerun()
                except Exception as e:
                    st.sidebar.error(f"Parsing error: {e}")

    # --- MAIN DASHBOARD INTERFACE ---
    if not df.empty:
        tab1, tab2 = st.tabs(["📋 Database & AI Agent", "📊 Visual Analytics"])

        with tab1:
            st.subheader("Interactive Activity Database")
            st.write("Edit cells directly to update the database.")
            
            edited_df = st.data_editor(df, hide_index=True, disabled=["id"], use_container_width=True)

            if not df.equals(edited_df):
                for index, old_row in df.iterrows():
                    new_row = edited_df.iloc[index]
                    for col in df.columns:
                        if old_row[col] != new_row[col]:
                            update_db_record(new_row['id'], col, new_row[col])
                            st.success("⚡ Database instantly updated!")
                            st.rerun()
            
            st.divider()
            
            st.subheader("🤖 Agentic Command Center: Chat & Update")
            st.markdown("""
            **This AI acts as an autonomous database administrator.** 
            You can ask it questions, OR command it to Update records.
            *(Examples: "Update Alex's status to At Risk" | "Change the Payment Gateway risk score to 8")*
            """)
            
            user_query = st.text_input("Issue a command or ask a question:")
            if user_query:
                context = df.to_json(orient="records")
                agent_prompt = f"""
                You are an Agentic AI with direct access to this SQL database: {context}
                User Input: "{user_query}"
                
                Decide if the user wants to UPDATE, DELETE, or QUERY the database. Return ONLY JSON:
                Update format: {{"intent": "update", "project_id": 1, "column_to_update": "Status", "new_value": "At Risk", "response": "I updated the status."}}
                Delete format: {{"intent": "delete", "response": "Only admin can delete records for transparency."}}
                Query format: {{"intent": "query", "response": "Your conversational answer here."}}
                """
                with st.spinner("AI Agent processing request..."):
                    try:
                        res = model.generate_content(agent_prompt, generation_config={"response_mime_type": "application/json"})
                        ai_decision = json.loads(res.text)
                        
                        if ai_decision.get("intent") == "update":
                            update_db_record(ai_decision["project_id"], ai_decision["column_to_update"], ai_decision["new_value"])
                            st.success(f"⚡ ACTION EXECUTED: {ai_decision['response']}")
                            st.rerun()
                        elif ai_decision.get("intent") == "delete":
                            st.error(f"🔒 ACTION DENIED: {ai_decision.get('response', 'Only admin can delete records for transparency.')}")
                        else:
                            st.info(f"💡 {ai_decision.get('response')}")
                    except Exception as e:
                        st.error(f"Command could not be processed perfectly. Error details: {e}")

        with tab2:
            st.subheader("📊 Executive Analytics Dashboard")
            col1, col2 = st.columns(2)
            with col1:
                status_counts = df["Status"].value_counts().reset_index()
                status_counts.columns = ["Status", "Count"]
                fig_pie = px.pie(status_counts, values="Count", names="Status", title="Portfolio Status Distribution", 
                                 color="Status", color_discrete_map={"On Track":"#00CC96", "At Risk":"#FFA15A", "Blocked":"#EF553B"})
                st.plotly_chart(fig_pie, use_container_width=True)
            with col2:
                fig_bar = px.bar(df, x="Project Name", y="Risk Score", color="Status", title="Risk Score by Project",
                                 color_discrete_map={"On Track":"#00CC96", "At Risk":"#FFA15A", "Blocked":"#EF553B"})
                st.plotly_chart(fig_bar, use_container_width=True)

    else:
        st.info("Database empty. Add a new update via the sidebar to initialize your workspace.")
