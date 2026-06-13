# 🧬 Anatomy RAG MVP — Reduced-Hallucination AI for Medical Students

A production-quality, zero-hallucination Retrieval-Augmented Generation (RAG) system for anatomy education. Every answer is traceable to source documents, with claim-level citations.

## ✨ Key Features

- **Zero Hallucination**: Every factual claim must trace to a source chunk. If uncertain, the system says so.
- **Claim-Level Citations**: Each answer includes exact quotes and chunk references.
- **User-Scoped Privacy**: Upload personal PDFs—they're isolated to your account and never visible to other users.
- **Multi-Source Architecture**: Separate collections for trusted preloaded content, user uploads, and cached queries.
- **Streaming Responses**: See answers appear in real-time with progressive citation loading.
- **Citation Inspector**: Click any citation to view the exact source passage in a PDF viewer.
- **Confidence Scoring**: High/Medium/Low/Insufficient confidence badges on every answer.
- **Scanned PDF Detection**: Rejects image-based PDFs; text-based documents only.

---

## 🏗️ Architecture

```
Frontend (Next.js 14)
    ↓
Supabase Auth (JWT) → Next.js API Route
    ↓
Backend (FastAPI + LlamaIndex)
    ├─ Query Analyzer (Gemini 2.0 Flash) → decompose questions
    ├─ Cache Layer 1 (Redis) → exact match cache
    ├─ Cache Layer 2 (Qdrant) → semantic similarity cache
    ├─ Parallel Fetcher (asyncio) → retrieve from 3 sources
    ├─ Reranker (BAAI/bge-reranker-v2-m3) → rank by relevance
    ├─ Generator (Gemini 2.0 Flash) → synthesize answers
    └─ Validator (pure Python) → verify citations
    ↓
Vector Database (Qdrant)
    ├─ anatomy_preloaded (trusted sources)
    ├─ anatomy_user_uploads (user PDFs, filtered by user_id)
    └─ query_cache (semantic cache)
    ↓
Cache (Redis)
    └─ Exact query hash cache (7-day TTL)
    ↓
File Storage (Supabase Storage)
    └─ Uploaded PDFs (temporary, deleted after chunking)
```

---

## 🚀 Quick Start

### Prerequisites

- **macOS/Linux**: Homebrew + Docker
- **Node.js**: v18+ (`node --version`)
- **Python**: 3.11+ (`python3 --version`)
- **Docker**: Running (`docker --version`)

### 1. Get API Keys

Sign up for free accounts and grab credentials:

| Service | URL | What to Get |
|---------|-----|-----------|
| **OpenAI** | https://platform.openai.com/api-keys | API Key (for embeddings) |
| **Google AI** | https://aistudio.google.com/apikey | API Key (for Gemini) |
| **Supabase** | https://supabase.com | Project URL + Anon Key + Service Key |

### 2. Set Up Environment

```bash
cd nestor.ai-v1

# Copy example and add your keys
cp .env.example .env.local

# Edit .env.local with your API keys and Supabase credentials
# (Use your favorite editor)
```

### 3. Start Everything

```bash
# Make script executable (first time only)
chmod +x run_nestor.sh

# Start all services
./run_nestor.sh

# Or manually:
docker-compose up -d
cd backend && python -m uvicorn main:app --reload --port 8000 &
cd ../frontend && npm run dev &
```

### 4. Open in Browser

- **App**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Qdrant Dashboard**: http://localhost:6333/dashboard

### 5. Sign Up & Query

1. Create account via Supabase auth UI
2. Ask a question (e.g., "What is the brachial plexus?")
3. Upload a PDF → ask questions about its content
4. Click citation markers to inspect sources

---

## 📋 Tech Stack

### Backend
| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Framework** | FastAPI 0.115+ | High-performance Python web server |
| **LLM Orchestration** | LlamaIndex 0.12+ | RAG pipeline framework (NOT LangChain) |
| **Embeddings** | OpenAI text-embedding-3-large | 3072-dim vectors via OpenAI API |
| **Generation** | Google Gemini 2.0 Flash | Fast, zero-temperature LLM |
| **Vector DB** | Qdrant | Self-hosted via Docker, 3 collections |
| **Cache L1** | Redis | Exact-match query hash cache |
| **Cache L2** | Qdrant | Semantic similarity cache (0.92 threshold) |
| **PDF Parsing** | PyMuPDF (fitz) | Fast text extraction + scanned PDF detection |
| **Reranking** | sentence-transformers (BAAI/bge-reranker-v2-m3) | Cross-encoder relevance ranking |
| **Auth** | Supabase JWT | FastAPI dependency injection |
| **Storage** | Supabase Storage + PostgreSQL | Temp file uploads + user metadata |

### Frontend
| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Framework** | Next.js 14 (App Router) | React SSR + streaming |
| **UI Library** | shadcn/ui + Tailwind CSS | Component system + styling |
| **PDF Viewer** | PDF.js (pdfjs-dist) | Client-side PDF rendering |
| **Auth** | @supabase/supabase-js | JWT session management |
| **HTTP** | Fetch API | Native streaming support |

---

## 📁 Project Structure

```
anatomy-rag/
├── backend/
│   ├── main.py                    # FastAPI app + lifespan setup
│   ├── config.py                  # Settings from environment
│   ├── routers/
│   │   ├── query.py               # POST /query (with streaming)
│   │   ├── upload.py              # POST /upload (PDF ingestion)
│   │   └── auth.py                # JWT verification
│   ├── services/
│   │   ├── query_analyzer.py      # Step 1: question decomposition
│   │   ├── source_router.py       # Step 2: routing logic
│   │   ├── fetcher.py             # Step 3: parallel retrieval
│   │   ├── reranker.py            # Step 4: cross-encoder ranking
│   │   ├── generator.py           # Step 5: answer synthesis
│   │   ├── validator.py           # Step 6: citation validation
│   │   ├── cache.py               # Redis + Qdrant caching
│   │   ├── ingestion.py           # PDF → chunks → embeddings
│   │   ├── embeddings.py          # OpenAI embedding service
│   │   ├── qdrant_client.py       # Vector DB helpers
│   │   └── source_router.py       # Routing rules
│   ├── models/
│   │   ├── query.py               # Pydantic request/response schemas
│   │   └── chunk.py               # Chunk dataclass
│   └── requirements.txt
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx               # Homepage + layout
│   │   ├── layout.tsx             # Root layout
│   │   ├── globals.css            # Tailwind + custom
│   │   └── api/query/route.ts     # Next.js proxy to FastAPI
│   ├── components/
│   │   ├── ChatInterface.tsx      # Main UI orchestrator
│   │   ├── MessageBubble.tsx      # Answer + citations rendering
│   │   ├── SourcePanel.tsx        # PDF.js viewer + citation inspector
│   │   ├── ConfidenceBadge.tsx    # High/Medium/Low/Insufficient pills
│   │   ├── AuthPanel.tsx          # Login/signup form
│   │   ├── UploadZone.tsx         # PDF drag-and-drop
│   │   ├── types.ts               # TypeScript types
│   │   └── ui/                    # shadcn/ui components
│   ├── lib/
│   │   ├── supabase.ts            # Client initialization
│   │   └── utils.ts               # Utility functions
│   ├── package.json
│   ├── tsconfig.json
│   └── tailwind.config.ts
│
├── docker-compose.yml             # Qdrant + Redis
├── .env.example                   # Environment template
├── .env.local                     # Local secrets (not committed)
├── SETUP.md                       # Detailed setup guide
├── run_nestor.sh                  # One-command startup script
└── README.md                      # This file
```

---

## 🔐 Security

### Privacy & Data Isolation
- ✅ **User-scoped uploads**: `anatomy_user_uploads` collection filtered by `user_id` on EVERY query
- ✅ **No cross-user leakage**: Assertion in code prevents queries without user filter
- ✅ **Temp file deletion**: Raw PDFs deleted immediately after chunking
- ✅ **Supabase RLS**: Row-level security on storage buckets

### Authentication
- ✅ **Supabase JWT**: All endpoints require valid Bearer token
- ✅ **JWKS verification**: Public keys fetched from Supabase's well-known endpoint
- ✅ **No hardcoded secrets**: All keys in environment variables

### API Safety
- ✅ **Rate limiting**: Semaphore-based concurrency control on Gemini calls
- ✅ **Timeout protection**: 2-second timeout per source; failed sources skipped
- ✅ **File validation**: MIME type + magic bytes check on upload
- ✅ **Size limits**: 20MB max file size

### Citation Integrity
- ✅ **Validation layer**: Every answer validated against retrieved chunks
- ✅ **Quote matching**: Quoted text verified to exist in source (fuzzy match allowed)
- ✅ **Confidence downgrade**: Invalid citations trigger confidence reduction
- ✅ **Explicit insufficient**: If <2 sources survive ranking, returns "insufficient"

---

## 🛠️ Configuration

### Environment Variables

| Variable | Required | Example | Notes |
|----------|----------|---------|-------|
| `OPENAI_API_KEY` | Yes | `sk-proj-...` | Get from https://platform.openai.com/api-keys |
| `GOOGLE_API_KEY` | Yes | `AIzaSy...` | Get from https://aistudio.google.com/apikey |
| `SUPABASE_URL` | Yes | `https://project.supabase.co` | From Supabase settings |
| `SUPABASE_ANON_KEY` | Yes | `eyJ...` | Public anon key |
| `SUPABASE_SERVICE_KEY` | Yes | `eyJ...` | Service role key (backend only) |
| `QDRANT_URL` | No | `http://localhost:6333` | Default: local Docker |
| `REDIS_URL` | No | `redis://localhost:6379` | Default: local Docker |

### Qdrant Collections

Created automatically on startup:

1. **`anatomy_preloaded`** (3072-dim vectors)
   - Pre-loaded anatomy textbooks
   - Payload: `source`, `chapter`, `section`, `page_ref`, `chunk_id`

2. **`anatomy_user_uploads`** (3072-dim vectors)
   - User-uploaded PDFs
   - **CRITICAL**: Always filtered by `user_id` field

3. **`query_cache`** (3072-dim vectors)
   - Semantic cache of answered questions
   - Payload: `query_hash`, `answer_json`, `created_at`

---

## 📊 Pipeline Walkthrough

### Query Flow (6 Steps)

```
User Question
    ↓
[1] Query Analyzer (Gemini)
    → Extract region, system, concept_type
    → Decompose into sub-questions
    → Route to source(s): openstax, ncbi, teachmeanatomy, user_uploads
    ↓
[2] Cache Check
    → Redis exact match (86400s–604800s TTL)
    → Qdrant semantic match (0.92 threshold)
    → Return if hit
    ↓
[3] Parallel Source Fetcher (asyncio.gather)
    → Fetch from openstax (8 chunks)
    → Fetch from ncbi (8 chunks)
    → Fetch from teachmeanatomy (8 chunks)
    → Fetch from user_uploads (8 chunks, filtered by user_id)
    → 2-second timeout per source; skip if slow
    ↓
[4] Reranker (BAAI/bge-reranker-v2-m3)
    → Cross-encoder score all chunks
    → Filter by threshold (>0.3)
    → Return top 5
    ↓
[5] Answer Generator (Gemini, temp=0)
    → Format chunks with [CHUNK_ID] markers
    → Generate JSON: direct_answer + explanation[] + confidence
    → Retry once if invalid JSON
    ↓
[6] Citation Validator (pure Python)
    → Verify chunk_id exists
    → Verify quote found in chunk text
    → Downgrade confidence if issues found
    ↓
Cache Both Tiers
    → Redis hash cache
    → Qdrant semantic cache
    ↓
Return to Client
    → Stream direct_answer immediately
    → Push citations as follow-up
```

### Upload Flow (Ingestion)

```
File Upload
    ↓
Validate
    → MIME type: application/pdf
    → Magic bytes: %PDF
    → Size: <20MB
    ↓
Detect Scanned PDF
    → Extract text from all pages
    → Count characters
    → If avg <100 chars/page → reject
    ↓
Extract & Chunk
    → Parse with PyMuPDF (fitz)
    → Split by SentenceSplitter (500 chars, 50 overlap)
    → Create Chunk objects with metadata
    ↓
Embed Batch
    → Call OpenAI batch embedding API
    → Get 3072-dim vectors
    ↓
Store in Qdrant
    → User collection: `anatomy_user_uploads`
    → Payload: user_id, chunk_id, filename, text, page_ref
    → No vectors returned to user
    ↓
Delete Raw File
    → Remove temporary PDF
    → Only embeddings kept
    ↓
Return Success
    → chunks_indexed: 42
```

---

## 🧪 Testing

### Manual Tests

```bash
# Health check
curl http://localhost:8000/health

# List Qdrant collections
curl http://localhost:6333/collections

# List Redis keys
redis-cli KEYS '*'

# Query API (requires JWT token from Supabase)
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT" \
  -d '{"query": "What is the deltoid?"}'
```

### Test Credentials

For local development, create test account:
- Email: `test@example.com`
- Password: `TestPassword123!`

---

## 🐛 Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| "Connection refused: 6333" | Qdrant not running | `docker-compose up -d` |
| "Missing bearer token" | No auth header | Log in via UI first |
| "SCANNED_PDF" error | Image-based PDF | Upload text-based PDF only |
| "Rate limit exceeded" | OpenAI quota | Add billing to OpenAI account |
| "Insufficient sources" | No matching chunks | Verify PDF uploaded + content relevant |
| Redis connection error | Not running | `docker-compose up -d redis` |

See [SETUP.md](./SETUP.md) for detailed troubleshooting.

---

## 📚 Next Steps

### For MVP → Production

1. **Load Pre-Built Content**
   - Download OpenStax A&P PDF
   - Download NCBI books (via E-utilities)
   - Parse and ingest into `anatomy_preloaded`

2. **Scale Infrastructure**
   - Qdrant Cloud (not self-hosted)
   - Redis via Upstash
   - Supabase managed database

3. **Add Monitoring**
   - Log queries + responses
   - Track cache hit rates
   - Monitor API latency
   - Alert on failed chunks

4. **Fine-Tuning**
   - Test confidence thresholds
   - Adjust reranker threshold
   - Optimize chunk size
   - Benchmark different LLMs

5. **User Features**
   - Search history
   - Saved annotations
   - PDF library management
   - Citation export (BibTeX, etc.)

---

## 📖 Documentation

- **[SETUP.md](./SETUP.md)** — Step-by-step setup with troubleshooting
- **[backend/](./backend/)** — Python backend services
- **[frontend/](./frontend/)** — TypeScript React frontend
- **API Docs** — http://localhost:8000/docs (when running)

---

## 🤝 Contributing

This is a medical education tool. All contributions should prioritize:
1. **Accuracy** — No hallucinations
2. **Privacy** — User data isolation
3. **Transparency** — Clear citations
4. **Safety** — Rate limits, timeouts, validation

---

## ⚖️ License & Disclaimer

**Educational Use Only**

This software is provided for medical education. It is NOT clinical advice. Always verify information with authoritative sources. Developers assume no liability for errors or omissions.

---

## 🎯 Key Design Principles

1. **Zero Hallucination First**: Architecture designed to fail gracefully when uncertain
2. **Source Transparency**: Every claim must be traceable to a passage
3. **User Privacy**: Data isolation by `user_id` at database level
4. **Performance**: Parallel fetching, caching, semantic matching
5. **Developer Experience**: Simple setup, clear error messages, good logging

---

## 🧠 Questions?

- Check [SETUP.md](./SETUP.md) for detailed walkthroughs
- Run `./run_nestor.sh` to start everything
- Access API docs at http://localhost:8000/docs
- Check backend logs for detailed error messages

**Happy learning! 🧬**
