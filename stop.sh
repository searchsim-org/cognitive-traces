#!/bin/bash

# Cognitive Traces - Stop Script
# This script stops all running backend and frontend servers

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════╗"
echo "║           Stopping Cognitive Traces Servers          ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# Stop backend from PID file
if [ -f ".backend.pid" ]; then
    BACKEND_PID=$(cat .backend.pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        print_info "Stopping backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID
        print_success "Backend stopped"
    else
        print_warning "Backend process not running"
    fi
    rm .backend.pid
fi

# Stop frontend from PID file
if [ -f ".frontend.pid" ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        print_info "Stopping frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID
        print_success "Frontend stopped"
    else
        print_warning "Frontend process not running"
    fi
    rm .frontend.pid
fi

# Kill any remaining processes by name
print_info "Checking for any remaining processes..."

if pkill -f "uvicorn app.main:app" 2>/dev/null; then
    print_success "Stopped remaining backend processes"
fi

if pkill -f "next dev" 2>/dev/null; then
    print_success "Stopped remaining frontend processes"
fi

echo ""
print_success "All servers stopped successfully!"

