# VigilNet AI 🛡️⚡

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![React Version](https://img.shields.io/badge/React-18.x-cyan?logo=react&logoColor=white)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-emerald?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-green?logo=mongodb&logoColor=white)](https://www.mongodb.com/)
[![Redis](https://img.shields.io/badge/Redis-Cache-red?logo=redis&logoColor=white)](https://redis.io/)
[![Google Gemini](https://img.shields.io/badge/GenAI-Gemini%20Pro-purple?logo=google&logoColor=white)](https://ai.google.dev/)

> **Closed-Loop Red-Team / Blue-Team Multi-Agent Adversarial System for Payment Fraud Defense.** Developed for the **Mastercard Innovation Challenge 2026**.

VigilNet AI is a simulation and stress-testing system designed to evaluate and harden fraud detection algorithms against adaptive, intelligent financial adversaries. The platform pits a Gemini-driven **Red Team** (which dynamically designs evasion strategies) against a multi-layered **Blue Team Ensemble** (tabular, graph, sequence, and text models). A closed-loop feedback agent (the **Miss-Analysis Agent**) dynamically adjusts the next-round generative bounds for blocked actions, modeling a real-world evolving threat vector.

---

## 🏗️ Technical Architecture & Closed Loop

VigilNet operates on an automated, multi-agent feedback loop:

```mermaid
graph TD
    A["1. Red Team Agent (Gemini)"] -->|1. Generation Objective / Bounds| B["2. SDV Generator (Synthetic Data)"]
    B -->|2. High-fidelity synthetic transactions| C["3. Blue Team Ensemble Shield"]
    C -->|3. Multi-layer evaluation (Tabular, Graph, Seq, Text)| D{"Blocked / Allowed?"}
    D -->|Blocked event telemetry| E["4. Miss-Analysis Agent"]
    D -->|Passed event logs| F["Round Scorecard (Evasion Rate)"]
    E -->|4. Adaptive Evasion Brief & directive| A
```

1. **Red Team Agent (Gemini)**: Formulates adversarial attack directives based on target profiles and previous campaign outcomes.
2. **SDV Generator (Synthetic Data)**: Projects realistic, high-fidelity financial transaction entries matching the planned vector bounds.
3. **Blue Team Ensemble Shield**: Evaluates incoming transaction batches across multiple vectors:
   - **Tabular Shield (XGBoost)**: Analyzes numerical fields, balances, and immediate fraud flags.
   - **Graph Shield (DGL/GNN)**: Identifies structure anomalies and smurfing/money-laundering network topologies.
   - **Sequence Shield (LSTM/Markov)**: Validates sequence behaviors, micro-deposits velocity, and card-testing timing.
   - **Text Shield (Prompted Gemini)**: Evaluates unstructured elements like business email communications and invoice descriptions.
4. **Miss-Analysis Agent**: Compiles detailed failure reports for blocked transaction steps, directing the Red Team on how to shift bounds and parameters in subsequent rounds to evade the ensemble.

---

## 📂 Project Structure

```
/VigilNet-AI
├── /backend
│   ├── /app
│   │   ├── /agents       # Red Team personas (Gemini-driven) & Miss-Analysis Agent
│   │   ├── /db           # MongoDB and Redis connection managers
│   │   ├── /detectors    # Blue Team detection models (XGBoost, GNN, Text-layer, etc.)
│   │   ├── /orchestrator # Loop Orchestrator & Round management
│   │   └── /routers      # API endpoints (e.g. /health, /score, /rounds)
│   ├── requirements.txt  # Python requirements
│   └── main.py           # FastAPI entrypoint
├── /frontend             # React (Vite) dashboard UI
│   ├── /src
│   │   ├── App.jsx       # Main dashboard application code
│   │   └── index.css     # Cyberpunk hacker design styles
│   └── package.json      # Node.js configurations
├── /images               # Brand assets and logo files
└── /scripts              # Utility and validation seeding scripts
```

---

## 🛠️ Local Development Setup

### 1. Prerequisites
- **Python 3.10+**
- **Node.js v18+** & **npm**
- **Docker Desktop** (for running Redis locally)
- **MongoDB Atlas** Account & Cluster (for database storage)
- **Google AI Studio** Account & API Key (for Gemini models)

### 2. Environment Configuration
Create a `.env` file in the project root:
```env
GEMINI_API_KEY=your_gemini_api_key_here
MONGODB_URI=your_mongodb_atlas_connection_string
MONGODB_DB_NAME=vigilnet
REDIS_URL=redis://localhost:6379
```

### 3. Spin up Infrastructure Services
Start a local Redis caching instance using Docker:
```powershell
docker run -d --name vigilnet-redis -p 6379:6379 redis:7-alpine
```

### 4. Backend Setup
Create and activate your Python virtual environment, then install dependencies:
```powershell
# In root directory
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows
# source .venv/bin/activate  # macOS/Linux

pip install -r backend/requirements.txt
```

Verify Gemini and database connectivity:
```powershell
python scripts/test_gemini.py
```

Start the FastAPI web server:
```powershell
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```
- **API Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Check**: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

### 5. Frontend Setup
Install npm packages and run the Vite client dev server:
```powershell
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser to view the interactive dashboard.

---

## 📊 Demo Day Guide & Seeding

To run a demo without depleting Gemini API key limits or encountering latency, you can populate the database with a pre-recorded campaign dataset.

### 1. Seeding Pre-Recorded Demo Data
To populate the database with a clean, presentable round-over-round evasion decay curve (3 rounds of progression for all 5 personas), run:
```powershell
python scripts/seed_demo_data.py
```
> [!NOTE]
> If your MongoDB already contains test rounds, the script will skip seeding by default to avoid overwriting them. To clear your database and start fresh with the clean demo curves, pass the `--clear` flag:
> `python scripts/seed_demo_data.py --clear`

### 2. Live Demo Run Safeguard
During the live demo on stage, you can trigger a live simulation round from the **Simulation Runner** tab:
- This will execute the dynamic Gemini-based Red Team agent planning, score it via the ensemble detector, and append the outcome directly to your charts.
- This is safe and does not disrupt the pre-recorded reference curves; it simply appends a new round at the end of the timeline.
- It is recommended to run a **2-round** challenge live to demonstrate the real-time feedback loop and adaptation.

---

## 🛡️ Control Center Views

- **Fraud Taxonomy**: Cyberthreat dictionary outlining active fraud vectors (Card Testing, BEC, Structuring, Identity Theft). Tapping any card opens a technical inspector window displaying mechanics, GNN telemetry fields, and SDV parameters.
- **Simulation Runner**: High-tech dashboard to trigger multi-round challenge loops. Select a persona, choose round bounds, customize objectives, and watch live execution logs scroll in the stdout console.
- **Metrics Curves**: Neon line charts rendering round-over-round Evasion rates vs Ensemble Recall rates, visualizing the adaptive learning degradation curve.
- **Evasion Replay**: Detailed audit portal to select past rounds and view full natural language Evasion Briefs and transaction scorecards.
