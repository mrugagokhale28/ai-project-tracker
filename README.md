# ai-project-tracker
Project Risk Tracking Assistant
An AI-powered portfolio risk tracking platform designed for Technical Program Managers (TPMs) and Solutions Engineering teams. The Project Risk Tracking Assistant automates project health monitoring by converting unstructured meeting transcripts and work updates into structured, actionable database records with real-time visual analytics and agentic database operations.

 Key Features
 1. Bulk Meeting Transcript Ingestion
Automated Extraction: Paste Zoom, Teams, or Slack meeting transcripts directly into the ingestion engine.

Structured JSON Parsing: Leverages Google's Gemini API with strict JSON schema enforcement (response_mime_type: application/json) to extract key project attributes: Project Name, Owner, Status, Risk Score (1–10), Blockers, and Risk Summary.

Batch SQL Injection: Automatically parses multi-project discussions and writes structured rows into SQLite in a single atomic transaction.

 2. Agentic Command Center
Natural Language Operations: Execute updates using plain English commands (e.g., "Update Alex's status to At Risk" or "Set Payment Gateway risk score to 8").

Autonomous Intent Routing: The agent analyzes user intent, identifies target database IDs and columns, and executes dynamic SQL updates automatically.

Analytical Querying: Ask conversational questions about portfolio status, team bottlenecks, or blocker distributions.

 3. Enterprise Data Transparency & Guardrails
Data Retention Enforcement: Built with enterprise data governance in mind. Deletion commands (via UI or AI) are explicitly blocked with a security message: "Only admin can delete records for transparency."

Audit Lineage: Preserves raw updates alongside parsed metadata to maintain complete historical audit trails.

 4. Interactive Activity Database
Inline Editing: Edit project names, owners, risk scores, or blockers directly inside the Streamlit table with instant backend SQLite persistence.

Dynamic Field Population: Select boxes automatically capture existing project names and owners while offering continuous text entry for new additions.

Cold-Start Auto-Seeding: Automatically initializes with enterprise sample logs if the database is empty, ensuring immediate dashboard accessibility.

 5. Executive Analytics Dashboard
Status Distribution: Interactive Plotly pie charts color-coding portfolio health (On Track, At Risk, Blocked).

Risk Score Mapping: Interactive bar charts prioritizing high-risk engineering bottlenecks across active workstreams.


## 🌐 Live Demo

Experience the live, interactive app deployed on Streamlit Cloud:

 **[Project Risk Tracking Assistant - Live App](https://ai-project-tracker-mg.streamlit.app/)**

*(Note: If the app is sleeping, click **"Get this app back up"** and it will wake up in a few seconds.)*


Local Setup & Installation
1. PrerequisitesPython 3.9 or higherGoogle Gemini API Key (Obtain from Google AI Studio)

2. Clone RepositoryBashgit clone https://github.com/YOUR_USERNAME/ai-project-tracker.git
cd ai-project-tracker

3. Install DependenciesCreate a requirements.txt file with the following dependencies:Plaintextstreamlit
google-generativeai
pandas
plotly
Then install them:Bashpip install -r requirements.txt

4. Configure Streamlit SecretsCreate a local .streamlit/secrets.toml file in the root directory:Ini, TOMLGEMINI_API_KEY = "your_actual_gemini_api_key_here"

5. Launch the ApplicationBashstreamlit run app.py
☁️ Deployment on Streamlit CloudPush your repository to GitHub.Sign in to Streamlit Cloud.Click New app, select your repository and app.py entry point.Go to Advanced Settings $\rightarrow$ Secrets and add your Gemini API key:Ini, TOMLGEMINI_API_KEY = "your_actual_gemini_api_key_here"

Click Deploy.

 Demonstration WorkflowsBulk Transcript Ingestion Test
 Copy and paste the following snippet into the Bulk Meeting Ingest sidebar:
PlaintextRachel: Morning team! Maya, how is the Fine-Tuning Pipeline?
Maya L: We are completely Blocked. The DevOps team hasn't provisioned GPU nodes in AWS yet. Risk score is 9.
Rachel: Mruga, what’s the status on the Executive KPI Dashboard?
Mruga G: 100% On Track! Finished dynamic Plotly charts and SQLite database sync. Zero blockers, risk score is 1.

Agentic Command TestIn the Agentic Command Center chat box, try the following prompts:
Update Request: "Update Maya's status to At Risk
Query Request: "Which projects currently have a risk score above 5?
