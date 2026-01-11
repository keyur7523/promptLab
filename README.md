# PromptLab

PromptLab is a simplified internal AI experimentation platform, similar to what a Grok team would use to safely iterate on prompts and models using real-time user feedback.

This is not a chatbot. It is infrastructure for controlled prompt experimentation at scale.

## Overview

PromptLab demonstrates the core components of production AI infrastructure:

- **Real-time streaming** via Server-Sent Events (SSE)
- **A/B experimentation framework** with deterministic variant assignment
- **Feedback pipeline** for continuous improvement (👍/👎)
- **Rate limiting** (100 req/hour per user) and **API key authentication**
- **Structured logging** with correlation IDs for observability
- **PostgreSQL** for persistence, **Redis** for caching/rate-limiting
- **Full-stack implementation** with React + TypeScript frontend

## Why PromptLab Exists

At scale, prompt changes are deployments. A single system prompt modification can affect millions of users simultaneously. Unlike code deployments, prompt changes alter model behavior in ways that are difficult to predict through unit tests alone.

**Prompt iteration is risky at scale because:**
- A poorly-worded system prompt can degrade response quality globally
- Model behavior varies across edge cases that only emerge under real traffic
- Rollbacks must happen within seconds, not minutes, when quality drops
- There is no compiler to catch prompt "bugs" before deployment

**Experimentation frameworks are required because:**
- Controlled traffic splitting isolates risk to a percentage of users
- Statistical significance requires structured data collection
- Variant assignment must be deterministic (same user, same experience)
- Metrics comparison needs apples-to-apples traffic conditions

**Feedback loops are essential because:**
- User ratings are the ground truth for subjective quality
- Automated metrics (latency, token count) miss semantic correctness
- Continuous feedback enables iterative prompt refinement
- Regression detection requires baseline comparison

**This is internal AI infrastructure, not a consumer product:**
- The target user is an AI engineer, not an end consumer
- The goal is safe prompt iteration, not chat features
- Success is measured in experiment velocity and rollback speed

## Architecture

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
│    3. Pre-estimate tokens (via Rust sidecar)        │
│    4. Assign experiment variant (consistent hash)   │
│    5. Build prompt based on variant                 │
│    6. Stream LLM response via SSE                   │
│    7. Store message + metadata                      │
│                                                     │
│  /feedback:                                         │
│    1. Validate message ownership                    │
│    2. Store thumbs up/down rating                   │
│    3. Log for analytics                             │
└────────┬───────────────┬───────────────┬────────────┘
         │               │               │
┌────────▼─────┐  ┌──────▼──────┐  ┌─────▼──────────┐
│ PostgreSQL   │  │    Redis    │  │  Token Counter │
│  (Messages,  │  │ (Rate Limit,│  │    (Rust)      │
│ Experiments, │  │   Cache)    │  │  - Tokenization│
│  Feedback)   │  │             │  │  - Cost Calc   │
└──────────────┘  └─────────────┘  └────────────────┘
```

## Key Technical Features

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

The frontend displays these metrics in real-time below each response:
```
↓ 16 in  ↑ 96 out  Σ 112 tokens  ⚡ 1.7s  💰 $0.0002
```

### 6. Rust Token Counter Sidecar
A high-performance Rust microservice handles token estimation:
- **Pre-request estimation**: Estimate input tokens before calling LLM (useful for cost budgeting)
- **Cost calculation**: Centralized pricing logic with model-specific rates
- **Fallback design**: Python backend falls back to local estimation if Rust service is unavailable
- **Low latency**: Sub-millisecond response times, no GC pauses

See `rust-token-counter/README.md` for architecture details and why Rust was chosen.

## Database Schema

### Core Tables
- **users**: API keys, rate limits
- **conversations**: Chat sessions
- **messages**: Full message history with experiment metadata
- **feedback**: Thumbs up/down ratings
- **experiments**: A/B test configurations

## Local Development

### Prerequisites
- Python 3.11+
- PostgreSQL
- Redis
- Node.js 18+
- Rust 1.75+ (optional, for token counter service)
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

4. **Start Rust token counter (optional):**
```bash
cd rust-token-counter
cargo build --release
./target/release/token-counter
# Token counter running at http://localhost:3001
```

If you skip this step, the Python backend will fall back to local token estimation.

5. **Start backend:**
```bash
uvicorn app.main:app --reload
# Backend running at http://localhost:8000
```

6. **Frontend setup (new terminal):**
```bash
cd frontend
npm install

# Copy and configure .env
cp .env.example .env
# Edit .env: Set VITE_API_KEY=test-key-123

npm run dev
# Frontend running at http://localhost:5173
```

7. **Test the system:**
- Open http://localhost:5173
- Start chatting!
- Check logs for "pre_estimated_tokens" to verify Rust integration

## Testing

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

## Deployment

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

## What This Demonstrates

✅ **Consumer-scale backend design** - Rate limiting, streaming, cost tracking
✅ **Experimentation infrastructure** - A/B testing for continuous improvement
✅ **High-throughput data pipelines** - Structured logging ready for analytics
✅ **Reliability thinking** - Health checks, error handling, observability
✅ **End-to-end ownership** - Backend, frontend, database, DevOps

## Security Features

- API key authentication (bcrypt hashing with SHA256 fallback)
- Rate limiting (100 req/hour per user)
- Input validation (Pydantic schemas)
- CORS configuration
- Structured error logging

## Future Enhancements

- [ ] Sliding window rate limiter
- [ ] Response caching for common queries
- [ ] Analytics dashboard
- [ ] API key rotation
- [ ] Horizontal scaling with K8s

## Tech Stack

**Backend:**
- FastAPI (async Python web framework)
- SQLAlchemy (ORM)
- PostgreSQL (persistence)
- Redis (rate limiting)
- OpenAI API (LLM)
- Structlog (structured logging)
- Rust token counter (high-performance tokenization)

**Frontend:**
- React 18
- TypeScript
- Vite (build tool)
- SSE for streaming

**DevOps:**
- Render (backend hosting)
- Vercel (frontend hosting)
- Docker Compose (local dev)

## Scale Thought Experiment

This section analyzes how PromptLab would behave under production load and what architectural decisions would be required to scale to millions of users.

### Expected QPS

**Traffic Assumptions by Environment:**

| Environment | Read QPS | Write QPS | Concurrent Streams | Notes |
|-------------|----------|-----------|-------------------|-------|
| Development | 1 | 0.5 | 5 | Single developer testing |
| Beta | 50 | 20 | 200 | Internal dogfooding, ~500 DAU |
| Production | 2,000 | 500 | 10,000 | 1M+ DAU, peak hours |

**Read vs Write Traffic:**
- Reads: Health checks, experiment config fetches, conversation history loads
- Writes: New messages, feedback submissions, experiment assignments logged

**Streaming Impact:**
- Each chat request holds an HTTP connection for 5-30 seconds during LLM response generation
- At 2,000 QPS with 10-second average stream duration, steady-state is 20,000 concurrent connections
- Connection count scales linearly with request rate and response latency
- SSE connections are lightweight (no WebSocket upgrade overhead) but still consume file descriptors and memory per connection

### Bottlenecks

**1. LLM Provider Latency and Rate Limits**
- OpenAI rate limits vary by tier: 3,500 RPM (tier 1) to 10,000+ RPM (tier 4)
- P50 latency: 500ms-2s for GPT-3.5, 2-5s for GPT-4
- P99 latency can spike to 30s+ during provider degradation
- Mitigation: Provider pooling (OpenAI + Anthropic + self-hosted), request queuing, circuit breakers

**2. Streaming Connection Fan-out**
- Each Python async worker can handle ~1,000 concurrent SSE streams (limited by asyncio event loop overhead)
- At 10,000 concurrent streams, need 10+ workers minimum
- Memory per stream: ~50KB (request context + response buffer)
- Mitigation: Dedicated streaming workers, connection limits per worker, horizontal scaling

**3. Database Write Amplification**
- Each chat completion triggers 2 message inserts (user + assistant) + 1 conversation update
- Feedback adds 1 insert per rating
- At 500 write QPS: 1,500+ DB writes/second
- Mitigation: Async write queue, batch inserts, connection pooling (PgBouncer)

**4. Redis Hot Keys**
- Rate limit keys: `rate_limit:{user_id}:{hour}` - INCR operations are O(1) but high volume
- Popular experiment keys read by every request
- At 2,000 QPS: 2,000+ Redis operations/second
- Mitigation: Redis cluster with read replicas, local caching for experiment config, rate limit sharding by user_id prefix

**5. Feedback Ingestion Pressure**
- Feedback is optional but critical for experiment evaluation
- Burst patterns: Users submit feedback after reading response (seconds delay)
- Risk: Feedback queue backup during traffic spikes
- Mitigation: Async ingestion, separate feedback workers, graceful degradation (accept but delay processing)

### Failure Modes

**1. LLM Provider Partial Outages or Slowdowns**
- Symptom: Timeouts increase, successful responses drop
- Detection: P99 latency threshold alerts, error rate monitoring
- Response: Circuit breaker trips, failover to secondary provider, queue incoming requests
- Recovery: Gradual traffic shift back after provider stabilizes

**2. Redis Unavailability**
- Symptom: Rate limiting fails open (or closed, depending on policy)
- Detection: Redis connection pool exhaustion, timeout errors
- Response: Fall back to in-memory rate limiting (per-instance, less accurate), log rate limit bypass
- Recovery: Redis reconnection with exponential backoff

**3. Database Connection Pool Exhaustion**
- Symptom: New requests queue, then timeout
- Detection: Pool wait time metrics, active connection count
- Response: Reject new requests with 503, prioritize streaming response completion
- Recovery: Pool reconfiguration, read replica failover for read traffic

**4. Streaming Client Disconnects**
- Symptom: Orphaned server-side streams consuming resources
- Detection: Connection state monitoring, memory growth
- Response: Aggressive timeout on idle streams (30s), cleanup on disconnect detection
- Recovery: Automatic via connection lifecycle management

**5. Bad Prompt Rollout Causing Global Quality Degradation**
- Symptom: Feedback approval rate drops across experiment variants
- Detection: Real-time feedback monitoring, anomaly detection on approval rate
- Response: Automatic experiment pause at threshold (e.g., >10% approval rate drop)
- Recovery: Rollback to previous prompt version, manual review before re-enabling

### Horizontal Scaling Plan

**1. Stateless FastAPI Services Behind Load Balancer**
- All request state stored in PostgreSQL/Redis, not in memory
- Any worker can handle any request
- Load balancer: Consistent hashing by user_id for cache locality, round-robin otherwise
- Health checks: `/health` endpoint, remove unhealthy instances within 10s

**2. Connection Pooling Strategies**
- Database: PgBouncer in transaction mode, 20 connections per pool, 10 pools per instance
- Redis: Connection pool per instance, 50 connections, lazy initialization
- HTTP (to LLM providers): aiohttp connection pool, keep-alive, 100 connections per provider

**3. Redis Sharding Considerations**
- Rate limits: Shard by `hash(user_id) % 16` across 16 Redis instances
- Experiment config: Single primary with read replicas (infrequent writes)
- Session data (if added): Consistent hashing by session_id

**4. Database Read/Write Separation**
- Primary: All writes (messages, feedback, experiments)
- Read replicas: Conversation history loads, experiment stats queries, analytics
- Replication lag tolerance: 100ms acceptable for read-after-write on history
- Connection routing: Application-level based on query type

**5. Async Background Ingestion for Feedback/Events**
- Feedback writes: Enqueue to Redis list, batch insert every 100ms or 100 items
- Event logging: Async structured logger, buffer to file, ship to log aggregator
- Metrics: In-memory aggregation, flush to metrics backend every 10s
- Benefits: Decouples request latency from storage latency

### Prompt Rollback Strategy

**1. Versioned Prompt Registry**
- Every prompt change creates a new version with immutable ID
- Schema: `{id, experiment_key, variant, prompt_text, created_at, created_by, active}`
- Prompt text stored in database, not code (enables runtime changes)
- Version history retained indefinitely for audit and rollback

**2. Experiment-Level Kill Switches**
- Each experiment has `active` boolean flag
- Kill switch disables experiment immediately, all users get control variant
- Kill switch state cached in Redis with 1s TTL (fast propagation)
- Admin API: `POST /experiments/{id}/kill` - no deploy required

**3. Global Rollback in Seconds**
- Rollback operation: Set previous version as active, invalidate cache
- Cache invalidation: Redis PUBLISH to all instances, local cache cleared
- Time to full rollback: <5 seconds (cache TTL + propagation)
- Rollback is atomic: No partial state during transition

**4. Canary Deployments for Prompt Changes**
- New prompt version starts at 1% traffic allocation
- Automatic promotion: 1% → 10% → 50% → 100% over hours/days
- Promotion gated on metrics: Approval rate, latency, error rate
- Automatic rollback if metrics degrade beyond threshold

**5. Auditability and Reproducibility**
- Every message records: `experiment_key`, `variant`, `prompt_version_id`
- Any historical response can be attributed to exact prompt text
- Audit log: Who changed what prompt, when, with what justification
- Reproducibility: Given message ID, can reconstruct exact prompt + model used

### Capacity Planning Summary

| Resource | Current Limit | Production Target | Scaling Method |
|----------|--------------|-------------------|----------------|
| Web Workers | 4 | 50+ | Horizontal (K8s HPA) |
| DB Connections | 20 | 500 (pooled) | PgBouncer |
| Redis Connections | 10 | 200 | Connection pooling |
| Concurrent Streams | 100 | 10,000+ | Worker count |
| Messages/day | 10K | 10M+ | Async writes, partitioning |

## License

MIT License - feel free to use for learning!

## Contact

Built by Keyur
Resume project demonstrating production backend engineering
[LinkedIn](your-linkedin) | [Email](your-email)

---

**⭐ Star this repo if you find it useful!**
