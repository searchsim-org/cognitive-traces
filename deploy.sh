#!/bin/bash
# Deployment script for Cognitive Traces app
# Usage: ./deploy.sh [--backend] [--frontend] [--all]

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="/srv/traces"
BACKEND_DIR="${PROJECT_ROOT}/backend"
FRONTEND_DIR="${PROJECT_ROOT}/frontend"
BACKEND_SERVICE="traces-backend"
FRONTEND_SERVICE="traces-frontend"
API_URL="https://traces.searchsim.org/api/v1"

# Default flags
DEPLOY_BACKEND=false
DEPLOY_FRONTEND=false

# Parse arguments
if [ $# -eq 0 ]; then
    echo -e "${YELLOW}No flags specified. Use --backend, --frontend, or --all${NC}"
    echo "Usage: $0 [--backend] [--frontend] [--all]"
    exit 1
fi

while [[ $# -gt 0 ]]; do
    case $1 in
        --backend|-b)
            DEPLOY_BACKEND=true
            shift
            ;;
        --frontend|-f)
            DEPLOY_FRONTEND=true
            shift
            ;;
        --all|-a)
            DEPLOY_BACKEND=true
            DEPLOY_FRONTEND=true
            shift
            ;;
        --help|-h)
            echo "Deployment script for Cognitive Traces"
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --backend, -b     Deploy backend only"
            echo "  --frontend, -f    Deploy frontend only"
            echo "  --all, -a         Deploy both backend and frontend"
            echo "  --help, -h        Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

echo -e "${GREEN}=== Cognitive Traces Deployment ===${NC}"
echo ""

# Deploy Backend
if [ "$DEPLOY_BACKEND" = true ]; then
    echo -e "${YELLOW}[1/4] Deploying Backend...${NC}"
    
    cd "$BACKEND_DIR"
    
    # Pull latest changes
    echo "  → Pulling latest code..."
    git pull || true
    
    # Install dependencies with Poetry
    echo "  → Installing dependencies..."
    poetry install --only main --no-interaction
    
    # Restart backend service
    echo "  → Restarting backend service..."
    sudo systemctl restart "$BACKEND_SERVICE"
    
    # Wait for service to fully start
    echo "  → Waiting for backend to start..."
    sleep 5
    
    # Check service status
    if sudo systemctl is-active --quiet "$BACKEND_SERVICE"; then
        echo -e "  ${GREEN}✓ Backend service is running${NC}"
        
        # Health check with retries
        echo "  → Testing health endpoint..."
        MAX_RETRIES=5
        RETRY_COUNT=0
        HEALTH_OK=false
        
        while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
            if curl -sf http://127.0.0.1:8000/health > /dev/null 2>&1; then
                HEALTH_OK=true
                break
            fi
            RETRY_COUNT=$((RETRY_COUNT + 1))
            if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
                echo "  → Retry $RETRY_COUNT/$MAX_RETRIES..."
                sleep 2
            fi
        done
        
        if [ "$HEALTH_OK" = true ]; then
            echo -e "  ${GREEN}✓ Backend health check passed${NC}"
        else
            echo -e "  ${YELLOW}⚠ Backend health check failed after $MAX_RETRIES attempts${NC}"
            echo -e "  ${YELLOW}  Service is running but may still be initializing${NC}"
            echo "  → Recent logs:"
            sudo journalctl -u "$BACKEND_SERVICE" -n 10 --no-pager | tail -5
        fi
    else
        echo -e "  ${RED}✗ Backend service failed to start${NC}"
        sudo journalctl -u "$BACKEND_SERVICE" -n 20 --no-pager
        exit 1
    fi
    
    echo ""
fi

# Deploy Frontend
if [ "$DEPLOY_FRONTEND" = true ]; then
    echo -e "${YELLOW}[2/4] Deploying Frontend...${NC}"
    
    cd "$FRONTEND_DIR"
    
    # Pull latest changes
    echo "  → Pulling latest code..."
    git pull || true
    
    # Install dependencies
    echo "  → Installing dependencies..."
    corepack enable
    pnpm install --frozen-lockfile
    
    # Build frontend
    echo "  → Building frontend..."
    export NEXT_PUBLIC_API_URL="$API_URL"
    pnpm build
    
    if [ ! -d ".next" ]; then
        echo -e "  ${RED}✗ Build failed - .next directory not found${NC}"
        exit 1
    fi
    
    echo -e "  ${GREEN}✓ Build successful${NC}"
    
    # Restart frontend service
    echo "  → Restarting frontend service..."
    sudo systemctl restart "$FRONTEND_SERVICE"
    
    # Wait for service to fully start
    echo "  → Waiting for frontend to start..."
    sleep 5
    
    # Check service status
    if sudo systemctl is-active --quiet "$FRONTEND_SERVICE"; then
        echo -e "  ${GREEN}✓ Frontend service is running${NC}"
        
        # Health check with retries
        echo "  → Testing frontend endpoint..."
        MAX_RETRIES=5
        RETRY_COUNT=0
        HEALTH_OK=false
        
        while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
            if curl -sf -I http://127.0.0.1:3000 > /dev/null 2>&1; then
                HEALTH_OK=true
                break
            fi
            RETRY_COUNT=$((RETRY_COUNT + 1))
            if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
                echo "  → Retry $RETRY_COUNT/$MAX_RETRIES..."
                sleep 2
            fi
        done
        
        if [ "$HEALTH_OK" = true ]; then
            echo -e "  ${GREEN}✓ Frontend health check passed${NC}"
        else
            echo -e "  ${YELLOW}⚠ Frontend health check failed after $MAX_RETRIES attempts${NC}"
            echo -e "  ${YELLOW}  Service is running but may still be initializing${NC}"
            echo "  → Recent logs:"
            sudo journalctl -u "$FRONTEND_SERVICE" -n 10 --no-pager | tail -5
        fi
    else
        echo -e "  ${RED}✗ Frontend service failed to start${NC}"
        sudo journalctl -u "$FRONTEND_SERVICE" -n 20 --no-pager
        exit 1
    fi
    
    echo ""
fi

# Reload Caddy
echo -e "${YELLOW}[3/4] Reloading Caddy...${NC}"
sudo systemctl reload caddy
if sudo systemctl is-active --quiet caddy; then
    echo -e "  ${GREEN}✓ Caddy reloaded successfully${NC}"
else
    echo -e "  ${RED}✗ Caddy reload failed${NC}"
    sudo journalctl -u caddy -n 20 --no-pager
    exit 1
fi
echo ""

# Summary
echo -e "${YELLOW}[4/4] Deployment Summary${NC}"
if [ "$DEPLOY_BACKEND" = true ]; then
    echo -e "  ${GREEN}✓ Backend deployed${NC}"
fi
if [ "$DEPLOY_FRONTEND" = true ]; then
    echo -e "  ${GREEN}✓ Frontend deployed${NC}"
fi
echo ""
echo -e "${GREEN}=== Deployment Complete ===${NC}"
echo ""
echo "Access your app at: https://traces.searchsim.org"
echo ""
echo "To view logs:"
if [ "$DEPLOY_BACKEND" = true ]; then
    echo "  Backend:  journalctl -u $BACKEND_SERVICE -f"
fi
if [ "$DEPLOY_FRONTEND" = true ]; then
    echo "  Frontend: journalctl -u $FRONTEND_SERVICE -f"
fi
echo "  Caddy:    journalctl -u caddy -f"

