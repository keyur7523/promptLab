# AI Chat Platform with Experimentation Framework

A production-grade AI chat platform with A/B testing, real-time streaming, and feedback loops. Built to demonstrate scalable system design and experimentation infrastructure.

## 🎯 Overview

This platform showcases the technical skills required to build consumer-scale infrastructure:

- **Real-time streaming** via Server-Sent Events (SSE)
- **A/B experimentation framework** with deterministic variant assignment
- **Feedback pipeline** for continuous improvement (👍/👎)
- **Rate limiting** (100 req/hour per user) and **API key authentication**
- **Structured logging** with correlation IDs for observability
- **PostgreSQL** for persistence, **Redis** for caching/rate-limiting
- **Full-stack implementation** with React + TypeScript frontend

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│             FRONTEND (React + TypeScript)           │
│           Chat UI with SSE streaming                │
└───────────────────┬─────────────────────────────────┘
                    │ HTTP + SSE (x-api-key header)
┌───────────────────▼─────────────────────────────────┐
│              BACKEND (FastAPI)                      │
│                                                     │
│  Auth Middleware → Rate Limiter → Logging          │
│                                                     │
│  /chat:                                             │
│    1. Validate API key                              │
│    2. Check rate limit                              │
│    3. Assign experiment variant (consistent hash)   │
│    4. Build prompt based on variant                 │
│    5. Stream LLM response via SSE                   │
│    6. Store message + metadata                      │
│                                                     │
│  /feedback:                                         │
│    1. Validate message ownership                    │
│    2. Store thumbs up/down rating                   │
│    3. Log for analytics                             │
└────────────────┬────────────────┬───────────────────┘
                 │                │
        ┌────────▼─────┐  ┌──────▼──────┐
        │ PostgreSQL   │  │    Redis    │
        │  (Messages,  │  │ (Rate Limit,│
        │ Experiments, │  │   Cache)    │
        │  Feedback)   │  │             │
        └──────────────┘  └─────────────┘
```

## 🔑 Key Technical Features

### 1. Server-Sent Events (SSE) for Streaming
- Simpler than WebSockets (unidirectional)
- Auto-reconnection built-in
- Standard HTTP (easier to deploy)
- Perfect for chat streaming

### 2. Deterministic A/B Experimentation
```python
variant = hash(user_id + experiment_key) % 100
# User always gets same variant for consistent UX
```
- No database lookup needed (fast!)
- Stateless (scales horizontally)
- Test different system prompts ("concise" vs "detailed")

### 3. Rate Limiting with Redis
- Fixed window algorithm: `rate_limit:{user_id}:{YYYYMMDDHH}`
- Atomic `INCR` operation (thread-safe)
- Automatic TTL cleanup

### 4. Structured Logging with Correlation IDs
- Each request gets unique `trace_id`
- JSON logs for easy parsing
- Full request tracing across services

### 5. Cost & Performance Tracking
Every LLM call tracks:
- `tokens_in` / `tokens_out`
- `latency_ms`
- `cost` (calculated from pricing)

## 📊 Database Schema

### Core Tables
- **users**: API keys, rate limits
- **conversations**: Chat sessions
- **messages**: Full message history with experiment metadata
- **feedback**: Thumbs up/down ratings
- **experiments**: A/B test configurations

## 🚀 Local Development

### Prerequisites
- Python 3.11+
- PostgreSQL
- Redis
- Node.js 18+
- OpenAI API key

### Setup

1. **Clone and configure:**
```bash
git clone <your-repo>
cd promptLab

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Copy and configure .env
cp .env.example .env
# Edit .env: Add your OPENAI_API_KEY
```

2. **Start PostgreSQL and Redis:**
```bash
# macOS with Homebrew
brew services start postgresql
brew services start redis

# Or use Docker
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres
docker run -d -p 6379:6379 redis
```

3. **Initialize database:**
```bash
# Create database
createdb ai_chat

# Run migrations and seed data
python init_db.py
# This creates test user with API key: test-key-123
```

4. **Start backend:**
```bash
uvicorn app.main:app --reload
# Backend running at http://localhost:8000
```

5. **Frontend setup (new terminal):**
```bash
cd frontend
npm install

# Copy and configure .env
cp .env.example .env
# Edit .env: Set VITE_API_KEY=test-key-123

npm run dev
# Frontend running at http://localhost:5173
```

6. **Test the system:**
- Open http://localhost:5173
- Start chatting!
- Click 👍/👎 to test feedback

## 🧪 Testing

### Test Chat API
```bash
curl -N -H "x-api-key: test-key-123" \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me about transformers"}' \
  http://localhost:8000/chat
```

### Test Feedback
```bash
curl -H "x-api-key: test-key-123" \
  -H "Content-Type: application/json" \
  -d '{"message_id": "<message-id>", "rating": 1}' \
  http://localhost:8000/feedback
```

### Check Experiment Stats
```bash
curl -H "x-api-key: test-key-123" \
  http://localhost:8000/feedback/stats
```

## 🌐 Deployment

### Deploy Backend to Render

1. **Push to GitHub:**
```bash
git add .
git commit -m "Initial commit"
git push origin main
```

2. **Create Render Web Service:**
   - Go to https://render.com → New → Web Service
   - Connect your GitHub repo
   - Configure:
     - **Name**: `ai-chat-backend`
     - **Root Directory**: `backend`
     - **Environment**: `Python 3`
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

3. **Add Environment Variables:**
   ```
   DATABASE_URL=<from Render PostgreSQL>
   REDIS_URL=<from Render Redis>
   OPENAI_API_KEY=<your-key>
   FRONTEND_URL=<your-vercel-url>
   ```

4. **Create PostgreSQL Database:**
   - Render Dashboard → New → PostgreSQL
   - Copy connection string to `DATABASE_URL`

5. **Create Redis:**
   - Render Dashboard → New → Redis
   - Copy connection string to `REDIS_URL`

6. **Initialize Database:**
   - After deployment, go to Shell and run:
   ```bash
   python init_db.py
   ```

### Deploy Frontend to Vercel

1. **Install Vercel CLI:**
```bash
npm i -g vercel
```

2. **Deploy:**
```bash
cd frontend
vercel
```

3. **Set Environment Variables:**
   - Vercel Dashboard → Settings → Environment Variables
   ```
   VITE_API_URL=https://your-backend.onrender.com
   VITE_API_KEY=test-key-123
   ```

4. **Redeploy:**
```bash
vercel --prod
```

### Post-Deployment
- Update `FRONTEND_URL` in Render backend settings
- Test the live chat!

## 📈 What This Demonstrates

✅ **Consumer-scale backend design** - Rate limiting, streaming, cost tracking
✅ **Experimentation infrastructure** - A/B testing for continuous improvement
✅ **High-throughput data pipelines** - Structured logging ready for analytics
✅ **Reliability thinking** - Health checks, error handling, observability
✅ **End-to-end ownership** - Backend, frontend, database, DevOps

## 🔒 Security Features

- API key authentication (bcrypt hashing with SHA256 fallback)
- Rate limiting (100 req/hour per user)
- Input validation (Pydantic schemas)
- CORS configuration
- Structured error logging

## 💡 Future Enhancements

- [ ] Sliding window rate limiter
- [ ] Response caching for common queries
- [ ] Analytics dashboard
- [ ] API key rotation
- [ ] Horizontal scaling with K8s

## 🛠️ Tech Stack

**Backend:**
- FastAPI (async Python web framework)
- SQLAlchemy (ORM)
- PostgreSQL (persistence)
- Redis (rate limiting)
- OpenAI API (LLM)
- Structlog (structured logging)

**Frontend:**
- React 18
- TypeScript
- Vite (build tool)
- SSE for streaming

**DevOps:**
- Render (backend hosting)
- Vercel (frontend hosting)
- Docker Compose (local dev)

## 📝 License

MIT License - feel free to use for learning!

## 🙋 Contact

Built by Keyur
Resume project demonstrating production backend engineering
[LinkedIn](your-linkedin) | [Email](your-email)

---

**⭐ Star this repo if you find it useful!**
