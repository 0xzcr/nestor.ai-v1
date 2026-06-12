# 🧬 Anatomy RAG MVP - Complete Setup Guide

This guide walks you through setting up the complete Anatomy RAG system for medical students. Follow each step carefully.

---

## Prerequisites

- **macOS/Linux**: Homebrew installed
- **Node.js**: v18+ (for Next.js frontend)
- **Python**: 3.11+ (for FastAPI backend)
- **Docker & Docker Compose**: For Qdrant and Redis containers
- **Git**: For version control

### Quick Check
```bash
node --version  # Should be v18+
python --version  # Should be 3.11+
docker --version
docker-compose --version
```

---

## Step 1: Clone & Install Dependencies

```bash
cd /path/to/nestor.ai-v1

# Backend dependencies
cd backend
pip install -r requirements.txt

# Frontend dependencies  
cd ../frontend
npm install
```

---

## Step 2: Set Up External Services

### A. Supabase (Auth + Storage)

1. **Create Supabase Account**
   - Go to https://supabase.com and sign up (free tier available)
   - Create a new project

2. **Get API Keys**
   - Go to **Project Settings → API**
   - Copy these values:
     - `Project URL` → `SUPABASE_URL`
     - `anon public` → `SUPABASE_ANON_KEY`
     - `service_role` → `SUPABASE_SERVICE_KEY`

3. **Create Storage Bucket**
   - Go to **Storage** in sidebar
   - Create new bucket named `uploads`
   - Set to private (Row Level Security)

4. **Update .env.local**
   ```
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=eyJ...
   SUPABASE_SERVICE_KEY=eyJ...
   NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
   ```

### B. OpenAI API (Embeddings)

1. **Create OpenAI Account**
   - Go to https://platform.openai.com
   - Sign up and verify email

2. **Get API Key**
   - Click on profile → **API keys**
   - Create new secret key
   - Copy to `.env.local`:
   ```
   OPENAI_API_KEY=sk-proj-...
   ```

3. **Enable Billing**
   - Go to **Billing → Overview**
   - Add payment method (free credits may be available)

### C. Google AI API (Gemini)

1. **Create Google Cloud Project** (or use existing)
   - Go to https://aistudio.google.com/apikey
   - Click **Create API Key**
   - Copy to `.env.local`:
   ```
   GOOGLE_API_KEY=AIzaSy...
   ```

---

## Step 3: Start Local Services (Docker)

Start Qdrant (vector database) and Redis (cache) locally:

```bash
# From project root
docker-compose up -d

# Verify services are running
docker-compose ps

# Expected output:
# NAME                STATUS
# qdrant-anatomy-rag  Up
# redis-anatomy-rag   Up
```

**Verify connectivity:**
```bash
# Qdrant should respond with 200 OK
curl http://localhost:6333/health

# Redis should respond with PONG
redis-cli ping
# If redis-cli not available, use: docker exec redis-anatomy-rag redis-cli ping
```

---

## Step 4: Start Backend (FastAPI)

```bash
cd backend

# Option A: Direct Python (development)
python -m uvicorn main:app --reload --port 8000

# Option B: Using Python environment
# If you set up a venv:
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

**Verify backend is running:**
```bash
curl http://localhost:8000/health
# Should return: {"status": "ok"}
```

---

## Step 5: Start Frontend (Next.js)

In a new terminal:

```bash
cd frontend
npm run dev
```

**Expected output:**
```
> ready - started server on 0.0.0.0:3000, url: http://localhost:3000
```

Open http://localhost:3000 in your browser.

---

## Step 6: Test the Full System

### A. Authentication Test

1. **Sign Up** (on the UI)
   - Enter email: `test@example.com`
   - Enter password: `TestPassword123!`
   - Click "Sign up"
   - Check your email for confirmation link (may be in spam)

2. **Log In**
   - Use the same credentials
   - Status should change to "Authenticated."

### B. Query Test

1. **Ask a Question**
   - Input: `"What are the branches of the brachial plexus?"`
   - Should see spinner: "Searching anatomy sources..."

   **Expected Error** (because no pre-loaded content yet):
   ```json
   {
     "confidence": "insufficient",
     "message": "This question couldn't be answered from the available sources."
   }
   ```

### C. Upload Test

1. **Prepare a Test PDF**
   - Create a simple text PDF or use an anatomy textbook sample
   - File size: < 20MB
   - Must be text-based (not scanned)

2. **Upload via UI**
   - Click "Select files" in Upload Zone
   - Choose PDF
   - Should see: "PDF processed successfully."
   - Check the response shows chunks indexed

3. **Query Against Upload**
   - Ask a question related to your PDF
   - Should now return answer with citations
   - Click citation `[1]` to see source passage

---

## Step 7: Verify Citation & Caching

### A. Test Citation Validation

```bash
# Query the API directly
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{"query": "What is the deltoid muscle?"}'
```

You should get a response like:
```json
{
  "direct_answer": "The deltoid is a large triangular muscle covering the shoulder.",
  "explanation": [
    {
      "claim": "Covers the shoulder region",
      "chunk_id": "upload_xxx_0001",
      "quote": "the deltoid muscle covering the shoulder"
    }
  ],
  "confidence": "high"
}
```

### B. Test Redis Cache

```bash
# Connect to Redis
redis-cli

# Check cache keys
KEYS *

# Should see keys like:
# query:a1b2c3d4e5f6...
```

### C. Test Qdrant Collections

```bash
# List collections
curl http://localhost:6333/collections

# Should show:
# {
#   "result": {
#     "collections": [
#       {"name": "anatomy_preloaded"},
#       {"name": "anatomy_user_uploads"},
#       {"name": "query_cache"}
#     ]
#   }
# }
```

---

## Step 8: Load Pre-Loaded Content (Optional)

To add trusted anatomy sources (OpenStax, NCBI, Teach Me Anatomy), you would need to:

1. Download PDFs from:
   - OpenStax: https://openstax.org/details/books/anatomy-and-physiology-2e
   - NCBI: https://www.ncbi.nlm.nih.gov/books/
   - Teach Me Anatomy: https://www.teachmeanatomy.info/

2. Create a script to ingest these (similar to upload flow)

3. Store in `anatomy_preloaded` collection

**For MVP testing**: User uploads are sufficient.

---

## Troubleshooting

### Problem: "Connection refused" on localhost:6333
- **Solution**: Ensure Docker is running and containers are up
  ```bash
  docker-compose ps
  docker-compose up -d  # Restart if needed
  ```

### Problem: "Invalid token" errors
- **Solution**: Make sure you're logged in via Supabase auth
  - Check browser console for JWT token
  - Verify SUPABASE_URL and keys are correct

### Problem: OpenAI rate limit errors
- **Solution**: 
  - Check your OpenAI quota at https://platform.openai.com/account/billing/overview
  - Ensure billing is enabled
  - Rate limiting: Free tier has 3 RPM, paid has 3500 RPM

### Problem: "No PDF magic bytes" on upload
- **Solution**: Ensure file is a real PDF, not renamed
  - Check: `file your-file.pdf` shows `PDF document`

### Problem: "Scanned PDF detected"
- **Solution**: Upload a text-based PDF only
  - PDFs extracted from images are not supported in MVP
  - Use original digital PDFs instead

### Problem: Redis connection errors
- **Solution**: Verify Redis is accessible
  ```bash
  redis-cli ping
  # Should return: PONG
  ```

---

## Architecture Summary

```
┌─────────────────┐
│   Frontend      │
│   (Next.js)     │
│  Port 3000      │
└────────┬────────┘
         │
         ├─── SSO (Supabase Auth) ───┐
         │                           │
         └── API Calls ──┬──────────┐│
                         │          ││
                ┌────────▼──────────┴┤
                │   Backend          │
                │   (FastAPI)        │
                │   Port 8000        │
                └────┬───┬───┬───────┘
                     │   │   │
         ┌───────────┘   │   └──────────────┐
         │               │                  │
    ┌────▼────┐   ┌──────▼──────┐   ┌──────▼───┐
    │ Qdrant  │   │    Redis    │   │ Supabase │
    │ 6333    │   │    6379     │   │ (Cloud)  │
    └─────────┘   └─────────────┘   └──────────┘
```

---

## Production Considerations

When moving to production:

1. **Use managed services**:
   - Qdrant Cloud instead of self-hosted
   - Redis via Upstash or AWS ElastiCache
   - Supabase free tier or paid

2. **Environment variables**:
   - Never commit `.env` files
   - Use GitHub Actions secrets or CI/CD platform

3. **Authentication**:
   - Enforce HTTPS
   - Keep JWT tokens short-lived
   - Implement token refresh

4. **Rate limiting**:
   - Add rate limiter middleware
   - Monitor API usage
   - Implement backoff strategies

5. **Monitoring**:
   - Log all errors
   - Track API latency
   - Monitor cache hit rates

---

## Quick Commands

```bash
# Start everything
docker-compose up -d && \
  (cd backend && python -m uvicorn main:app --reload --port 8000 &) && \
  (cd frontend && npm run dev &)

# Stop everything
docker-compose down && pkill -f uvicorn && pkill -f "next dev"

# View logs
docker-compose logs -f qdrant
docker-compose logs -f redis

# Clean up
docker-compose down -v  # Removes volumes too
```

---

## Support & Next Steps

- 📚 API Documentation: http://localhost:8000/docs (when running)
- 🐛 Bug Reports: Create a GitHub issue
- 💡 Feature Requests: Discussions tab
- 📖 Anatomy Content: See Step 8 for pre-loaded sources

**Happy learning with Nestor.ai! 🧠**
