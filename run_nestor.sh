#!/usr/bin/env bash

# Anatomy RAG MVP - Complete Start Script
# Starts Docker services (Qdrant + Redis), FastAPI backend, and Next.js frontend

set -euo pipefail

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

# Use .env.local if it exists, otherwise .env
if [[ -f "$ROOT_DIR/.env.local" ]]; then
  ENV_FILE="$ROOT_DIR/.env.local"
else
  ENV_FILE="$ROOT_DIR/.env"
fi

BACKEND_HOST="${BACKEND_HOST:-0.0.0.0}"
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"

BACKEND_PID=""
FRONTEND_PID=""
DOCKER_STARTED=false

cleanup() {
  echo ""
  echo -e "${YELLOW}Cleaning up...${NC}"
  if [[ -n "$BACKEND_PID" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
  if [[ -n "$FRONTEND_PID" ]] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi
  if [[ "$DOCKER_STARTED" == true ]]; then
    docker-compose down
  fi
  echo -e "${YELLOW}Cleanup complete${NC}"
}

trap cleanup EXIT INT TERM

echo -e "${BLUE}🧬 Starting Anatomy RAG MVP...${NC}"
echo ""

# Verify environment file
if [[ ! -f "$ENV_FILE" ]]; then
  echo -e "${RED}❌ Missing $ENV_FILE${NC}"
  echo "   Copy .env.example to .env.local and add your API keys:"
  echo "   - OPENAI_API_KEY (from platform.openai.com)"
  echo "   - GOOGLE_API_KEY (from aistudio.google.com)"
  echo "   - SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY (from supabase.com)"
  exit 1
fi

echo -e "${BLUE}Checking prerequisites...${NC}"

# Check for Docker
if ! command -v docker >/dev/null 2>&1; then
  echo -e "${RED}❌ Docker is required but not installed.${NC}"
  exit 1
fi

# Check for Python
if ! command -v python3 >/dev/null 2>&1; then
  echo -e "${RED}❌ Python 3 is required but not installed.${NC}"
  exit 1
fi

# Check for Node
if ! command -v npm >/dev/null 2>&1; then
  echo -e "${RED}❌ Node.js/npm is required but not installed.${NC}"
  exit 1
fi

echo -e "${GREEN}✓ Prerequisites OK${NC}"
echo ""

# Load environment
echo -e "${BLUE}Loading environment from $ENV_FILE${NC}"
set -a
source "$ENV_FILE"
set +a
echo -e "${GREEN}✓ Environment loaded${NC}"
echo ""

# Start Docker services
echo -e "${BLUE}Starting Docker services (Qdrant + Redis)...${NC}"
cd "$ROOT_DIR"
docker-compose up -d
DOCKER_STARTED=true

sleep 3

# Check Qdrant
if curl -s http://localhost:6333/health > /dev/null 2>&1; then
  echo -e "${GREEN}✓ Qdrant running on http://localhost:6333${NC}"
else
  echo -e "${RED}❌ Qdrant failed to start${NC}"
  docker-compose logs qdrant
  exit 1
fi

echo -e "${GREEN}✓ Redis running on localhost:6379${NC}"
echo ""

# Create Python venv if needed
if [[ ! -d "$BACKEND_DIR/venv" ]]; then
  echo -e "${BLUE}Creating Python virtual environment...${NC}"
  python3 -m venv "$BACKEND_DIR/venv"
fi

# Install backend dependencies
echo -e "${BLUE}Installing backend dependencies...${NC}"
source "$BACKEND_DIR/venv/bin/activate"
pip install -q -r "$BACKEND_DIR/requirements.txt"
echo -e "${GREEN}✓ Backend dependencies installed${NC}"
echo ""

# Install frontend dependencies
if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
  echo -e "${BLUE}Installing frontend dependencies...${NC}"
  (cd "$FRONTEND_DIR" && npm install -q)
  echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
else
  echo -e "${GREEN}✓ Frontend dependencies already installed${NC}"
fi
echo ""

# Start FastAPI backend
echo -e "${BLUE}Starting FastAPI backend on port $BACKEND_PORT...${NC}"
(
  cd "$ROOT_DIR"
  source "$BACKEND_DIR/venv/bin/activate"
  python -m uvicorn backend.main:app --reload --host "$BACKEND_HOST" --port "$BACKEND_PORT" 2>&1 | sed 's/^/[Backend] /'
) &
BACKEND_PID=$!

sleep 3

# Verify backend started
if curl -s http://localhost:$BACKEND_PORT/health > /dev/null; then
  echo -e "${GREEN}✓ FastAPI backend running on http://localhost:$BACKEND_PORT${NC}"
else
  echo -e "${YELLOW}⚠️  Backend may still be starting...${NC}"
fi
echo ""

# Start Next.js frontend
echo -e "${BLUE}Starting Next.js frontend on port $FRONTEND_PORT...${NC}"
(
  cd "$FRONTEND_DIR"
  PORT="$FRONTEND_PORT" npm run dev 2>&1 | sed 's/^/[Frontend] /'
) &
FRONTEND_PID=$!

sleep 3

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}🎉 Anatomy RAG MVP is ready!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo -e "📱 ${BLUE}Frontend:${NC}     http://localhost:$FRONTEND_PORT"
echo -e "🔌 ${BLUE}Backend API:${NC}  http://localhost:$BACKEND_PORT"
echo -e "📚 ${BLUE}API Docs:${NC}     http://localhost:$BACKEND_PORT/docs"
echo -e "🗄️  ${BLUE}Qdrant:${NC}      http://localhost:6333/dashboard"
echo ""
echo -e "${YELLOW}📝 NEXT STEPS:${NC}"
echo "   1. Sign up at http://localhost:3000"
echo "   2. Add API keys if not already in .env.local"
echo "   3. Upload a PDF and ask questions"
echo ""
echo -e "${YELLOW}🛑 TO STOP: Press Ctrl+C${NC}"
echo ""

# Wait for both processes
wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true

