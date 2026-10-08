import streamlit as st
import google.generativeai as genai
import pandas as pd
import sqlite3
import json
import plotly.express as px

# --- PAGE SETUP ---
st.set_page_config(page_title="Enterprise AI Ops Lead", page_icon="⚡", layout="wide")
st.title("Project Tracking Assistant")
st.caption("Agentic workflow automation, dynamic database tracking, and visual analytics.")

# --- DATABASE SETUP (SQLite) ---
conn = sqlite3.connect('projects.db', check_same_thread=False)
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS updates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project TEXT,
        member TEXT,
        summary TEXT,
        status TEXT,
        risk_score INTEGER,
        blockers TEXT,
        raw_update TEXT
    )
''')
conn.commit()

# --- API KEY CONFIGURATION ---
api_key = st.secrets.get("GEMINI_API_KEY") if "GEMINI_API_KEY" in st.secrets else None
if not api_key:
    api_key = st.sidebar.text_input("Enter Gemini API Key:", type="password")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-3.8-flash')

    # --- DATABASE FUNCTIONS ---
    def load_data():
        # Removed the Delete checkbox column
        return pd.read_sql_query("SELECT id, project, member, status, risk_score, blockers, summary FROM updates ORDER BY id DESC", conn)

    def add_data(project, member, summary, status, risk_score, blockers, raw):
        c.execute('''
            INSERT INTO updates (project, member, summary, status, risk_score, blockers, raw_update)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (project, member, summary, status, risk_score, blockers, raw))
        conn.commit()

    def update_db_record(record_id, column, new_value):
        c.execute(f"UPDATE updates SET {column} = ? WHERE id = ?", (new_value, record_id))
        conn.commit()

    # Load current data
    df = load_data()
    existing_projects = df['project'].unique().tolist() if not df.empty else []
    existing_members = df['member'].unique().tolist() if not df.empty else []

    # --- SIDEBAR: SINGLE UPDATE ---
    st.sidebar.header("➕ Add Single Update")
    project_options = existing_projects + ["➕ Add New Project..."]
    selected_project = st.sidebar.selectbox("Select Project", project_options)
    project_name = st.sidebar.text_input("Enter New Project Name") if selected_project == "➕ Add New Project..." else selected_project

    member_options = existing_members + ["➕ Add New Member..."]
    selected_member = st.sidebar.selectbox("Select Team Member", member_options)
    developer_name = st.sidebar.text_input("Enter New Member Name") if selected_member == "➕ Add New Member..." else selected_member

    update_text = st.sidebar.text_area("Raw Status Update / Work Log")

    if st.sidebar.button("Analyze & Save Update"):
        if update_text and project_name and developer_name:
            prompt = f"""
            Analyze this update and return ONLY a JSON object:
            {{"summary": "1-sentence summary", "status": "On Track", "risk_score": 1, "blockers": "None"}}
            Update text: "{update_text}"
            """
            with st.spinner("AI analyzing update..."):
                try:
                    # Enforcing strict JSON output to prevent parsing errors
                    res = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
                    parsed = json.loads(res.text)
                    add_data(project_name, developer_name, parsed.get("summary", "N/A"), 
                             parsed.get("status", "On Track"), int(parsed.get("risk_score", 1)), 
                             parsed.get("blockers", "None"), update_text)
                    st.sidebar.success("Saved to database!")
                    st.rerun()
                except Exception as e:
                    st.sidebar.error(f"Error parsing AI response: {e}")
        else:
            st.sidebar.warning("Ensure Project, Member, and Update text are filled out.")

    st.sidebar.divider()

    # --- SIDEBAR: BULK MEETING INGESTION ---
    st.sidebar.header("🎙️ Bulk Meeting Ingest")
    transcript_text = st.sidebar.text_area("Paste Zoom/Meeting Transcript:", height=150)
    if st.sidebar.button("Extract All Updates"):
        if transcript_text:
            prompt = f"""
            Extract EVERY project update from this transcript. Return ONLY a valid JSON ARRAY of objects.
            Format: [{{"project": "Name", "member": "Name", "summary": "...", "status": "On Track", "risk_score": 1, "blockers": "None"}}]
            Transcript: "{transcript_text}"
            """
            with st.spinner("AI mapping meeting notes..."):
                try:
                    res = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
                    parsed_array = json.loads(res.text)
                    for item in parsed_array:
                        add_data(item.get("project", "Unknown"), item.get("member", "Unknown"), 
                                 item.get("summary", ""), item.get("status", "On Track"), 
                                 int(item.get("risk_score", 1)), item.get("blockers", "None"), transcript_text)
                    st.sidebar.success(f"Ingested {len(parsed_array)} updates!")
                    st.rerun()
                except Exception as e:
                    st.sidebar.error(f"Parsing error: {e}")

    # --- MAIN DASHBOARD INTERFACE ---
    if not df.empty:
        # Removed the root cause tab entirely
        tab1, tab2 = st.tabs(["📋 Database & AI Agent", "📊 Visual Analytics"])

        with tab1:
            st.subheader("Interactive Activity Database")
            st.write("Edit cells directly to update the database.")
            
            # Display Table without the Delete column
            edited_df = st.data_editor(df, hide_index=True, disabled=["id"], use_container_width=True)

            # Detect Edits
            if not df.equals(edited_df):
                for index, old_row in df.iterrows():
                    new_row = edited_df.iloc[index]
                    for col in df.columns:
                        if old_row[col] != new_row[col]:
                            update_db_record(new_row['id'], col, new_row[col])
                            st.success("⚡ Database instantly updated!")
                            st.rerun()
            
            st.divider()
            
            # --- AI AGENT SECTION ---
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
                Update format: {{"intent": "update", "project_id": 1, "column_to_update": "status", "new_value": "At Risk", "response": "I updated the status."}}
                Delete format: {{"intent": "delete", "response": "Only admin can delete records for transparency."}}
                Query format: {{"intent": "query", "response": "Your conversational answer here."}}
                """
                with st.spinner("AI Agent processing request..."):
                    try:
                        # Forced JSON formatting to fix the error you were getting
                        res = model.generate_content(agent_prompt, generation_config={"response_mime_type": "application/json"})
                        ai_decision = json.loads(res.text)
                        
                        # Execute the AI's Decision
                        if ai_decision.get("intent") == "update":
                            update_db_record(ai_decision["project_id"], ai_decision["column_to_update"], ai_decision["new_value"])
                            st.success(f"⚡ ACTION EXECUTED: {ai_decision['response']}")
                            st.rerun()
                        elif ai_decision.get("intent") == "delete":
                            # Blocks the user from deleting via AI
                            st.error(f"🔒 ACTION DENIED: {ai_decision.get('response', 'Only admin can delete records for transparency.')}")
                        else:
                            st.info(f"💡 {ai_decision.get('response')}")
                    except Exception as e:
                        # If an error happens, it will now explicitly tell you what went wrong
                        st.error(f"Command could not be processed perfectly. Error details: {e}")

        with tab2:
            st.subheader("📊 Executive Analytics Dashboard")
            col1, col2 = st.columns(2)
            with col1:
                status_counts = df["status"].value_counts().reset_index()
                status_counts.columns = ["Status", "Count"]
                fig_pie = px.pie(status_counts, values="Count", names="Status", title="Portfolio Status Distribution", 
                                 color="Status", color_discrete_map={"On Track":"#00CC96", "At Risk":"#FFA15A", "Blocked":"#EF553B"})
                st.plotly_chart(fig_pie, use_container_width=True)
            with col2:
                fig_bar = px.bar(df, x="project", y="risk_score", color="status", title="Risk Score by Project",
                                 color_discrete_map={"On Track":"#00CC96", "At Risk":"#FFA15A", "Blocked":"#EF553B"})
                st.plotly_chart(fig_bar, use_container_width=True)

    else:
        st.info("Database empty. Add a new update via the sidebar to initialize your workspace.")
