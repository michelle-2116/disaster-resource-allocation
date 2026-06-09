# Post Disaster Resource Allocation Agent

An AI-powered decision-support system for disaster response, designed to assist human operators in resource allocation and route optimization during post-disaster scenarios. The system transforms unstructured disaster news into actionable logistics insights while keeping humans in the loop for validation and operational decisions.

---

## System Overview

This project is a monorepo containing two distinct modules:

- **DataIngestion-Allocation**: A dual-layer agentic pipeline that ingests disaster news, verifies incidents using AI, and allocates resources with human approval based on inventory availability.
- **Route-Optimizer**: A map-centric command center that visualizes incidents, shelters, and dispatch routes on an interactive map.

**Integration Status**: These components are **integrated** on this branch! They share a unified Supabase database to synchronize live need cards, dispatches, active roadblocks, and incidents in real time, with a bidirectional cascading reset and real-time polling.

---

## Architecture

### DataIngestion-Allocation
A two-layer intelligence pipeline:
- **Layer 1 (Crisis Analyst)**: Monitors RSS feeds, GDELT, and Exa AI for disaster news. Uses Gemini to verify incidents and extract structured data (type, severity, location) 
- **Layer 2 (Allocator Agent)**: Matches verified incidents against inventory using Gemini function-calling. Includes a Human-in-the-Loop (HITL) gate for high-quantity allocations 

### Route-Optimizer
A logistics visualization and routing system:
- **Ingestion Engine**: Processes raw news text using Gemini to create incident records in Supabase 
- **Routing Service**: Calculates optimal supply routes from hubs to shelters using the **public OSRM API** 
- **Database**: Uses Supabase (PostgreSQL) with PostGIS for spatial queries 

---

## Component 1: DataIngestion-Allocation

### Purpose
Assists in disaster news ingestion, incident verification, and resource allocation based on real-time inventory availability.

### Tech Stack
- **Backend**: Python 3.13+, FastAPI, Google Gemini AI (`gemini-3.1-flash-lite`)  
- **Frontend**: Node.js, React, Vite
- **Database**: SQLite (demo mode) or Supabase (production)

### Configuration
Required environment variables in `backend/.env` :
- `GEMINI_API_KEY`: Google Gemini API key
- `EXA_API_KEY`: Exa AI API key for news fetching

Copy `backend/.env.example` and `frontend/.env.example` when creating local environment files.

### How to Run Locally
**Backend**:
```bash
cd DataIngestion-Allocation/backend
venv/bin/uvicorn src.api:app --host 127.0.0.1 --port 8000
```
**Frontend**:
```bash
cd DataIngestion-Allocation/frontend
npm run dev
```

### Discord Message Ingestion
The DataIngestion backend can ingest messages from selected Discord channels. A standalone bot process listens to Discord and forwards captured messages to `POST /discord/messages`, where disaster-related messages are adapted into the existing incident allocation pipeline.

**Discord bot setup**:
1. Open the Discord Developer Portal and create an application.
2. Add a bot to the application and copy the bot token.
3. In the bot settings, enable the privileged `Message Content Intent`.
4. Invite the bot to your server with permissions to view the target channels and read message history. The bot only needs to read messages for ingestion.
5. Copy the numeric channel IDs for the Discord channels you want monitored. In Discord, enable Developer Mode, right-click a channel, and choose `Copy Channel ID`.

**Backend environment variables** in `DataIngestion-Allocation/backend/.env`:
```env
DISCORD_BOT_TOKEN=your_discord_bot_token
DISCORD_CHANNEL_IDS=123456789012345678,234567890123456789
DISCORD_BACKEND_URL=http://127.0.0.1:8000/discord/messages
DISCORD_INGEST_SECRET=replace_with_a_long_random_secret
DISCORD_REQUEST_TIMEOUT_SECONDS=10
DISCORD_REQUEST_RETRIES=3
```

`DISCORD_INGEST_SECRET` is optional but recommended. If it is set on the backend, the listener sends it as `X-Discord-Ingest-Secret` and the backend rejects mismatches.

**Run locally**:
```bash
cd DataIngestion-Allocation/backend
pip install .
venv/bin/uvicorn src.api:app --host 127.0.0.1 --port 8000
```

In a second terminal:
```bash
cd DataIngestion-Allocation/backend
python -m src.discord_listener
```

**How to test**:
1. Start the DataIngestion backend.
2. Start the Discord listener.
3. Post a disaster-related message in one configured channel, for example: `Flooding near Meppadi relief camp, families need drinking water and medical kits urgently.`
4. Watch the listener logs for a successful forward and the backend logs for `/discord/messages` processing.
5. Check the generated cards:
   ```bash
   curl -fsS http://127.0.0.1:8000/need-cards
   ```
6. In demo mode, activity can also be checked at:
   ```bash
   curl -fsS http://127.0.0.1:8000/activity-feed
   ```

**Example listener payload**:
```json
{
  "content": "Flooding near Meppadi relief camp, families need drinking water and medical kits urgently.",
  "username": "volunteer#1234",
  "timestamp": "2026-06-04T08:30:00+00:00",
  "channel_id": "123456789012345678",
  "channel_name": "field-reports",
  "attachments": [
    {
      "url": "https://cdn.discordapp.com/attachments/example/photo.jpg",
      "filename": "photo.jpg",
      "content_type": "image/jpeg",
      "size": 245760
    }
  ]
}
```

**Example backend response**:
```json
{
  "status": "processed",
  "source": "discord",
  "incidents_processed": 1,
  "allocation_summary": [
    {
      "incident_id": "DISCORD_MEPPADI_FLOOD_20260604",
      "need_cards_created": 2,
      "allocations_status": "completed"
    }
  ],
  "demo_mode": true
}
```

Non-disaster messages return:
```json
{
  "status": "ignored",
  "reason": "message_not_classified_as_disaster",
  "demo_mode": true
}
```

**Troubleshooting**:
- Missing message text usually means `Message Content Intent` is not enabled in the Discord Developer Portal.
- No messages in logs usually means the channel ID is not listed in `DISCORD_CHANNEL_IDS` or the bot lacks channel access.
- `401 Invalid Discord ingest secret` means `DISCORD_INGEST_SECRET` differs between the backend and listener environment.
- Backend connection errors mean `DISCORD_BACKEND_URL` is wrong or the FastAPI backend is not running.
- Gemini errors require a valid `GEMINI_API_KEY`.
- In production mode, Supabase inventory and incident settings must also be configured because allocation uses the existing inventory store.

---

## Component 2: Route-Optimizer

### Purpose
Provides real-time visualization of disaster incidents, shelters, and resource dispatch routes on an interactive map.


### Tech Stack
- **Backend**: Python 3.10+, FastAPI, Google Generative AI (`gemini-flash-latest`) 
- **Frontend**: Node.js, React, Leaflet 
- **Routing**: Public OSRM API
- **Database**: Supabase (PostgreSQL with PostGIS)

### Configuration
Required environment variables in `backend/.env`  :
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Supabase service role or anon key
- `GEMINI_API_KEY`: Google Gemini API key

Copy `backend/.env.example` and `frontend/.env.example` when creating local environment files. The frontend uses `VITE_API_BASE_URL=http://localhost:8001` by default.

### How to Run Locally
**Backend**:
```bash
cd Route-Optimizer/backend
venv/bin/uvicorn main:app --host 127.0.0.1 --port 8001
```
**Frontend**:
```bash
cd Route-Optimizer/frontend
npm run dev
```

### Root Make Shortcuts
After dependencies are installed, you can run each process from the repo root:
```bash
make data-backend
make data-frontend
make route-backend
make route-frontend
make status
```

### Local URLs
- DataIngestion backend: `http://127.0.0.1:8000`
- DataIngestion health: `http://127.0.0.1:8000/health`
- Route Optimizer backend: `http://127.0.0.1:8001`
- Route Optimizer health: `http://127.0.0.1:8001/health`
- Frontends: use the Vite URL printed by `npm run dev`, usually `http://localhost:5173` or the next available port.

---

## How to Run the Integrated System

To run all services, open **4 separate terminals** and run the following commands:

1. **Terminal 1: Data Ingestion Backend (Port 8000)**
   ```powershell
   conda activate witch
   cd DataIngestion-Allocation/backend
   uvicorn src.api:app --port 8000
   ```

2. **Terminal 2: Unified Frontend Console (Port 5173)**
   ```powershell
   cd DataIngestion-Allocation/frontend
   npm run dev
   ```

3. **Terminal 3: Route Optimizer Backend (Port 8001)**
   ```powershell
   conda activate witch
   cd Route-Optimizer/backend
   uvicorn main:app --port 8001
   ```

4. **Terminal 4: Discord Ingestion Bot**
   ```powershell
   conda activate witch
   cd DataIngestion-Allocation/backend
   python -m src.discord_listener
   ```

*(Note: Turn Demo Mode OFF in the http://localhost:5173 dashboard to write/read live allocations to Supabase).* 
