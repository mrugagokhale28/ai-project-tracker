import streamlit as st
import google.generativeai as genai
import pandas as pd
import json

# Page Configuration
st.set_page_config(page_title="AI Project Health Tracker", page_icon="📊", layout="wide")

st.title("AI Project Health & Blocker Tracker")
st.write("Automated project status parsing, risk scoring, and interactive Q&A assistant.")

# Fetch key safely from Streamlit Cloud Secrets
api_key = st.secrets.get("GEMINI_API_KEY") if "GEMINI_API_KEY" in st.secrets else None

if not api_key:
    api_key = st.sidebar.text_input("Enter Gemini API Key:", type="password")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-3.8-flash')

    # Pre-populate demo data so Eddie sees results immediately
    if "tasks" not in st.session_state:
        st.session_state.tasks = [
            {
                "Project": "Payment Gateway Integration",
                "Member": "Alex",
                "Summary": "Stripe integration blocked due to missing webhook credentials.",
                "Status": "Blocked",
                "Risk Score": 9,
                "Blockers": "Missing webhook secret keys from DevOps.",
                "Raw Update": "Tried setting up Stripe webhooks today but blocked waiting on secrets."
            },
            {
                "Project": "User Dashboard UI",
                "Member": "Mruga",
                "Summary": "Completed dark mode UI and user settings page.",
                "Status": "On Track",
                "Risk Score": 2,
                "Blockers": "None",
                "Raw Update": "Finished dark mode toggle and user profile settings screen."
            },
            {
                "Project": "Mobile Data Sync",
                "Member": "Devin",
                "Summary": "Database sync dropping packets on iOS background tasks.",
                "Status": "At Risk",
                "Risk Score": 7,
                "Blockers": "iOS background execution timeout limits.",
                "Raw Update": "Background data sync failing on iOS test devices."
            }
        ]

    # Sidebar: Add New Updates
    st.sidebar.header("➕ Add Project Update")
    project_name = st.sidebar.text_input("Project Name")
    developer_name = st.sidebar.text_input("Team Member Name")
    update_text = st.sidebar.text_area("Daily Status Update / Raw Work Log")

    if st.sidebar.button("Analyze & Log Update"):
        if update_text and project_name:
            prompt = f"""
            Analyze the following project update and return ONLY a valid JSON object:
            {{
                "summary": "1-sentence concise summary",
                "status": "On Track" or "At Risk" or "Blocked",
                "risk_score": integer between 1 and 10,
                "blockers": "Specific blocker or None"
            }}

            Update text: "{update_text}"
            """
            with st.spinner("AI is analyzing status..."):
                try:
                    response = model.generate_content(prompt)
                    clean_json = response.text.strip().replace("```json", "").replace("```", "").strip()
                    parsed = json.loads(clean_json)

                    st.session_state.tasks.append({
                        "Project": project_name,
                        "Member": developer_name,
                        "Summary": parsed.get("summary", "N/A"),
                        "Status": parsed.get("status", "On Track"),
                        "Risk Score": int(parsed.get("risk_score", 1)),
                        "Blockers": parsed.get("blockers", "None"),
                        "Raw Update": update_text
                    })
                    st.sidebar.success("Update analyzed and logged!")
                except Exception as e:
                    st.sidebar.error(f"Parsing error: {e}")
        else:
            st.sidebar.warning("Please fill in both Project Name and Update text.")

    # Metrics Dashboard
    df = pd.DataFrame(st.session_state.tasks)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Updates", len(df))
    col2.metric("Blocked Tasks", len(df[df["Status"] == "Blocked"]))
    col3.metric("At Risk Tasks", len(df[df["Status"] == "At Risk"]))
    col4.metric("Avg Risk Score", round(df["Risk Score"].mean(), 1))

    st.divider()

    # Data Table
    st.subheader("📋 Active Project Activity Log")
    st.dataframe(
        df[["Project", "Member", "Status", "Risk Score", "Blockers", "Summary"]],
        use_container_width=True
    )

    st.divider()

    # AI Q&A Assistant
    st.subheader("🤖 Ask AI Assistant About Projects")
    user_query = st.text_input("Ask a question (e.g., 'Which tasks are blocked right now?'):")

    if user_query:
        context = json.dumps(st.session_state.tasks)
        qa_prompt = f"""
        You are an enterprise AI project manager.
        Answer the user's question clearly based ONLY on this dataset:
        {context}

        Question: {user_query}
        """
        with st.spinner("Analyzing project data..."):
            answer = model.generate_content(qa_prompt)
            st.info(answer.text)

else:
    st.warning("Please configure your Gemini API key in Streamlit Secrets or enter it in the sidebar.")
