# VigilNet AI

Closed-Loop Red-Team / Blue-Team AI System for Payment Fraud Defense. Developed for Mastercard Innovation Challenge 2026.

## Project Structure

```
/backend
  /app
    /routers      # API endpoints (e.g. /health, /score, /rounds)
    /agents       # Red Team personas (Gemini-driven) & Miss-Analysis Agent
    /detectors    # Blue Team detection models (XGBoost, GNN, Text-layer, etc.)
    /orchestrator # Loop Orchestrator & Round management
    /db           # MongoDB and Redis connection managers
  requirements.txt
  main.py
/frontend         # React (Vite) dashboard (to be built in Phase 8)
/scripts          # Utility and validation scripts (Gemini test, CTGAN training)
/docs             # Architectural logs and design decisions
```

---

## Local Development Setup

### 1. Prerequisites
- **Python 3.10+**
- **Docker Desktop** (for running Redis locally)
- **MongoDB Atlas** Account & Cluster (for database storage)
- **Google AI Studio** Account & API Key (for Gemini models)

### 2. Environment Configuration
Copy the `.env.example` file to `.env`:
```powershell
cp .env.example .env
```
Open `.env` and fill in the required details:
- `GEMINI_API_KEY`: Your Gemini API Key from Google AI Studio.
- `MONGODB_URI`: Connection string for your MongoDB Atlas cluster.
- `MONGODB_DB_NAME`: Database name (e.g., `vigilnet`).
- `REDIS_URL`: URL of the local Redis instance (default: `redis://localhost:6379`).

### 3. Spin up Local Services
Start a local Redis instance using Docker:
```powershell
docker run -d --name vigilnet-redis -p 6379:6379 redis:7-alpine
```

Verify that it is running:
```powershell
docker ps
```

### 4. Create and Activate Virtual Environment
Use `venv` for Python dependency management.

**On Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
```

**On macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

### 5. Running Verifications (Phase 0 Done Criteria)

#### Test Gemini API Connectivity:
```powershell
python scripts/test_gemini.py
```

#### Run FastAPI Web Server:
Start the Uvicorn dev server:
```powershell
uvicorn backend.main:app --reload
```
Navigate to:
- Swagger API Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health Check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

Expected `/health` response:
```json
{
  "status": "healthy",
  "mongodb": "connected",
  "redis": "connected"
}
```

---

## Demo Day Guide & Seeding (Phase 9)

To ensure your Mastercard Innovation Challenge demo runs flawlessly without depleting your Gemini API key free tier quotas, you can seed a clean pre-recorded progression dataset into MongoDB Atlas.

### 1. Seeding Pre-Recorded Demo Data
To populate the database with a clean, presentable round-over-round evasion decay curve (3 rounds of progression for all 5 personas), run:
```powershell
python scripts/seed_demo_data.py
```
> [!NOTE]
> If your MongoDB already contains test rounds, the script will skip seeding by default to avoid overwriting them. If you wish to clear your database and start fresh with the clean demo curves, pass the `--clear` flag:
> `python scripts/seed_demo_data.py --clear`

### 2. Live Demo Safeguard (Stage Runs)
During the live demo on stage, you can trigger a live simulation round from the **Simulation Runner** tab on the React dashboard:
- This will execute the dynamic Gemini-based Red Team agent planning and routing, score it via the ensemble detector, and append the outcome directly to your charts.
- This is safe and does not disrupt the pre-recorded reference curves; it simply appends a new round at the end of the timeline.
- It is recommended to run a 2-round challenge live to show the real-time feedback loop and adaptation.
