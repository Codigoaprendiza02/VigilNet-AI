# VigilNet AI — Production Deployment Guide 🚀

This document guides the process of deploying the **VigilNet AI** application suite on **Railway** (backend FastAPI services + Redis caching worker) and **Vercel** (frontend React SPA). 

---

## 🏛️ Deployment Architecture & Services

```
                   +----------------------------------+
                   |          Vercel Hosting          |
                   |      Static React Front-end      |
                   +----------------+-----------------+
                                    |
                                    | CORS Requests
                                    v
+-----------------------------------+-----------------------------------+
|                           Railway Cloud                               |
|                                                                       |
|  +---------------------------+             +-----------------------+  |
|  |     FastAPI Service       |             |     Redis Service     |  |
|  |  uvicorn uvicorn.app      | <---------> |   internal tcp link   |  |
|  |  (PORT 8000 redirect)     |   Private   |  (internal port 6379) |  |
|  +---------------------------+             +-----------------------+  |
+-------------------+---------------------------------------------------+
                    |
                    | MongoDB Driver Link (SSL)
                    v
    +---------------+-----------------+
    |       MongoDB Atlas Cloud       |
    |      Managed Cluster (M0)       |
    +---------------------------------+
```

---

## 📋 Environment Configuration Checklists

### 1. Backend Service (Railway)
Ensure the following variables are declared inside your Railway backend service dashboard:

| Variable | Recommended Value / Source | Description |
|---|---|---|
| `GEMINI_API_KEY` | *Your Google AI Studio Gemini API Key* | Authenticates LLM agent prompts |
| `MONGODB_URI` | `mongodb+srv://<user>:<password>@cluster.mongodb.net/` | Connection link for MongoDB Atlas |
| `MONGODB_DB_NAME` | `vigilnet` | Target database name inside Atlas |
| `REDIS_URL` | `${{Redis.REDIS_URL}}` | Internal Railway reference pointing to the Redis service |
| `PORT` | `8000` | Redirect port (Railway injects this automatically) |
| `ENVIRONMENT` | `production` | Switches log handlers to production outputs |
| `FRONTEND_URL` | *Your deployed Vercel domain URL* | Configures CORS whitelist permissions |

### 2. Frontend Client (Vercel)
Ensure the following variable is declared inside your Vercel client deployment project:

| Variable | Value | Description |
|---|---|---|
| `VITE_API_BASE` | *Your deployed Railway backend endpoint URL* | Targets the API routes in production |

---

## 🛠️ Step-by-Step Deployment Walkthrough

### Step A: MongoDB Atlas Network Permissions
Since Railway servers scale dynamically and exit via a randomized pool of IP ranges, standard static IP whitelisting will block connections.
1. Log in to your **MongoDB Atlas Dashboard**.
2. Navigate to **Security** -> **Network Access**.
3. Temporarily set the IP whitelist address to allow access from anywhere: **`0.0.0.0/0`**.

### Step B: Deploying Backend to Railway
1. Access your **Railway Dashboard** and create a new project.
2. Click **New** -> **GitHub Repo** and connect your `VigilNet-AI` repository.
3. Once the service is spawned, click **New** -> **Database** -> **Add Redis** within the same project.
4. Click into the **FastAPI Backend Service** -> **Variables** tab, and copy the environment parameters listed in the checklist above.
5. In the **Settings** tab under **Networking**, click **Generate Domain** to create a public HTTPS URL (e.g. `https://vigilnet-ai-production.up.railway.app`).
6. Railway will automatically build and execute the application container using the root [`backend/Dockerfile`](file:///c:/Users/riyan/Projects/VigilNet%20AI/backend/Dockerfile).

### Step C: Deploying Frontend to Vercel
1. Access your **Vercel Dashboard** and click **Add New** -> **Project**.
2. Import the `VigilNet-AI` repository.
3. Configure the build parameters:
   * **Framework Preset**: `Vite`
   * **Root Directory**: `frontend`
   * **Environment Variables**: Add `VITE_API_BASE` and set it to your generated Railway domain URL.
4. Click **Deploy**. Vercel will automatically build the client bundles and publish a public URL.

### Step D: Whitelist CORS in Railway
1. Copy the generated Vercel deployment URL (e.g. `https://vigilnet-ai.vercel.app`).
2. Go back to the **Railway Backend Service** -> **Variables** tab.
3. Update the `FRONTEND_URL` variable with your copied Vercel URL.
4. Railway will automatically redeploy the backend container with the updated CORS whitelists.

---

## 🩺 Diagnostics & Health Verification

Once both deployments are active, confirm system connectivity by accessing the following health path in your browser:
```
https://your-railway-backend-url.railway.app/health
```
Verify the JSON response confirms full DB connectivity in production:
```json
{
  "status": "healthy",
  "mongodb": "connected",
  "redis": "connected"
}
```
You can now access your Vercel URL to run live closed-loop simulations in the production cloud!
