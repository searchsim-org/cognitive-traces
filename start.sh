#!/bin/bash

# Cognitive Traces - Development Start Script
# This script checks for dependencies and starts both backend and frontend servers

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_section() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    print_section "Checking Prerequisites"
    
    local missing_tools=0
    
    # Check Python
    if command_exists python3; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_success "Python $PYTHON_VERSION installed"
    else
        print_error "Python 3 not found. Please install Python 3.10+"
        missing_tools=$((missing_tools + 1))
    fi
    
    # Check Poetry
    if command_exists poetry; then
        POETRY_VERSION=$(poetry --version | cut -d' ' -f3)
        print_success "Poetry $POETRY_VERSION installed"
    else
        print_error "Poetry not found. Install with: curl -sSL https://install.python-poetry.org | python3 -"
        missing_tools=$((missing_tools + 1))
    fi
    
    # Check Node.js
    if command_exists node; then
        NODE_VERSION=$(node --version)
        print_success "Node.js $NODE_VERSION installed"
    else
        print_error "Node.js not found. Please install Node.js 18+"
        missing_tools=$((missing_tools + 1))
    fi
    
    # Check pnpm
    if command_exists pnpm; then
        PNPM_VERSION=$(pnpm --version)
        print_success "pnpm $PNPM_VERSION installed"
    else
        print_error "pnpm not found. Install with: npm install -g pnpm"
        missing_tools=$((missing_tools + 1))
    fi
    
    if [ $missing_tools -gt 0 ]; then
        print_error "Missing $missing_tools required tool(s). Please install them first."
        exit 1
    fi
}

# Setup backend
setup_backend() {
    print_section "Setting Up Backend"
    
    cd backend
    
    # Check if dependencies are installed
    if [ -d ".venv" ] || poetry env info --path >/dev/null 2>&1; then
        print_info "Backend dependencies already installed, skipping..."
    else
        print_info "Installing backend dependencies..."
        poetry install
        print_success "Backend dependencies installed"
    fi
    
    # Check for .env file
    if [ ! -f ".env" ]; then
        if [ -f "env.example" ]; then
            print_warning ".env file not found. Creating from env.example..."
            cp env.example .env
            print_warning "Please edit backend/.env with your API keys before running!"
        else
            print_warning ".env file not found. Please create one from env.example"
        fi
    else
        print_success ".env file exists"
    fi
    
    cd ..
}

# Setup frontend
setup_frontend() {
    print_section "Setting Up Frontend"
    
    cd frontend
    
    # Check if node_modules exists
    if [ -d "node_modules" ]; then
        print_info "Frontend dependencies already installed, skipping..."
    else
        print_info "Installing frontend dependencies..."
        pnpm install
        print_success "Frontend dependencies installed"
    fi
    
    # Check for .env.local file
    if [ ! -f ".env.local" ]; then
        if [ -f "env.local.example" ]; then
            print_info "Creating .env.local from env.local.example..."
            cp env.local.example .env.local
            print_success ".env.local file created"
        else
            print_info ".env.local will use defaults"
        fi
    else
        print_success ".env.local file exists"
    fi
    
    cd ..
}

# Start backend
start_backend() {
    print_info "Starting backend server on port 8000..."
    cd backend
    poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    cd ..
    sleep 2
    
    # Check if backend started successfully
    if kill -0 $BACKEND_PID 2>/dev/null; then
        print_success "Backend server started (PID: $BACKEND_PID)"
        echo $BACKEND_PID > .backend.pid
    else
        print_error "Failed to start backend server"
        return 1
    fi
}

# Start frontend
start_frontend() {
    print_info "Starting frontend server on port 3000..."
    cd frontend
    pnpm dev &
    FRONTEND_PID=$!
    cd ..
    sleep 2
    
    # Check if frontend started successfully
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        print_success "Frontend server started (PID: $FRONTEND_PID)"
        echo $FRONTEND_PID > .frontend.pid
    else
        print_error "Failed to start frontend server"
        return 1
    fi
}

# Cleanup function
cleanup() {
    print_section "Shutting Down Servers"
    
    if [ -f ".backend.pid" ]; then
        BACKEND_PID=$(cat .backend.pid)
        if kill -0 $BACKEND_PID 2>/dev/null; then
            print_info "Stopping backend (PID: $BACKEND_PID)..."
            kill $BACKEND_PID
            print_success "Backend stopped"
        fi
        rm .backend.pid
    fi
    
    if [ -f ".frontend.pid" ]; then
        FRONTEND_PID=$(cat .frontend.pid)
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            print_info "Stopping frontend (PID: $FRONTEND_PID)..."
            kill $FRONTEND_PID
            print_success "Frontend stopped"
        fi
        rm .frontend.pid
    fi
    
    # Kill any remaining processes
    pkill -f "uvicorn app.main:app" 2>/dev/null || true
    pkill -f "next dev" 2>/dev/null || true
    
    print_success "Cleanup complete"
}

# Trap CTRL+C and other termination signals
trap cleanup EXIT INT TERM

# Main execution
main() {
    clear
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════════════════════╗"
    echo "║        Cognitive Traces Development Server           ║"
    echo "║                  Starting Up...                       ║"
    echo "╚═══════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    # Check prerequisites
    check_prerequisites
    
    # Setup backend and frontend
    setup_backend
    setup_frontend
    
    # Start services
    print_section "Starting Services"
    
    start_backend
    if [ $? -ne 0 ]; then
        print_error "Backend failed to start. Check the logs above."
        exit 1
    fi
    
    start_frontend
    if [ $? -ne 0 ]; then
        print_error "Frontend failed to start. Check the logs above."
        cleanup
        exit 1
    fi
    
    # Success message
    print_section "✨ Servers Running ✨"
    echo ""
    print_success "Backend API:      http://localhost:8000"
    print_success "API Documentation: http://localhost:8000/api/docs"
    print_success "Frontend App:      http://localhost:3000"
    echo ""
    print_info "Press CTRL+C to stop all servers"
    print_info "View logs in your terminal"
    echo ""
    
    # Wait for user interrupt
    wait
}

# Run main function
main

