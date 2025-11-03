#!/bin/bash

# Cleanup script for Cognitive Traces Annotator
# Removes all job data, logs, checkpoints, and cached files

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=================================="
echo "Cognitive Traces Cleanup Script"
echo "=================================="
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Directories to clean
DATA_DIR="./data"
CHECKPOINT_DIR="./data/checkpoints"
UPLOADED_DATASETS_DIR="./data/uploaded_datasets"

# Confirm with user
echo -e "${YELLOW}WARNING: This will delete ALL annotation data including:${NC}"
echo "  - All job directories (UUID folders) in data/"
echo "  - All uploaded datasets in data/uploaded_datasets/"
echo "  - All session logs"
echo "  - All checkpoint files"
echo ""
echo -e "${GREEN}Note: Example CSV files in data/ root will be preserved${NC}"
echo ""
echo -e "${RED}This action CANNOT be undone!${NC}"
echo ""
read -p "Are you sure you want to continue? (type 'yes' to confirm): " confirm

if [ "$confirm" != "yes" ]; then
    echo -e "${GREEN}Cleanup cancelled.${NC}"
    exit 0
fi

echo ""
echo "Starting cleanup..."
echo ""

# Count files before cleanup
if [ -d "$DATA_DIR" ]; then
    # Count UUID directories (job folders)
    job_count=0
    for dir in "$DATA_DIR"/*/ ; do
        if [ -d "$dir" ]; then
            dirname=$(basename "$dir")
            # Check if it's a UUID pattern (contains hyphens and is 36 chars)
            if [[ "$dirname" =~ ^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$ ]]; then
                job_count=$((job_count + 1))
            fi
        fi
    done
    
    if [ -d "$CHECKPOINT_DIR" ]; then
        checkpoint_count=$(find "$CHECKPOINT_DIR" -type f -name "*_checkpoint.json" 2>/dev/null | wc -l)
    else
        checkpoint_count=0
    fi
    
    if [ -d "$UPLOADED_DATASETS_DIR" ]; then
        upload_count=$(find "$UPLOADED_DATASETS_DIR" -type f 2>/dev/null | wc -l)
    else
        upload_count=0
    fi
    
    echo -e "${YELLOW}Found:${NC}"
    echo "  - $job_count job directories"
    echo "  - $checkpoint_count checkpoint files"
    echo "  - $upload_count uploaded datasets"
    echo ""
fi

# Function to safely remove directory
safe_remove() {
    local dir=$1
    local name=$2
    
    if [ -d "$dir" ]; then
        echo -n "  Removing $name... "
        rm -rf "$dir"
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo "  $name not found (skipping)"
        return 1
    fi
}

# Remove job directories (UUID pattern folders only)
if [ -d "$DATA_DIR" ]; then
    echo "Cleaning job directories..."
    
    removed_count=0
    # Only remove directories that match UUID pattern
    for dir in "$DATA_DIR"/*/ ; do
        if [ -d "$dir" ]; then
            dirname=$(basename "$dir")
            # Check if it's a UUID pattern (job folder)
            if [[ "$dirname" =~ ^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$ ]]; then
                echo -n "  Removing job $dirname... "
                rm -rf "$dir"
                echo -e "${GREEN}✓${NC}"
                removed_count=$((removed_count + 1))
            fi
        fi
    done
    
    if [ "$removed_count" -eq 0 ]; then
        echo "  No job directories found"
    fi
    
    echo ""
fi

# Remove uploaded datasets directory
if [ -d "$UPLOADED_DATASETS_DIR" ]; then
    echo "Cleaning uploaded datasets..."
    echo -n "  Removing uploaded_datasets/... "
    rm -rf "$UPLOADED_DATASETS_DIR"
    echo -e "${GREEN}✓${NC}"
    echo ""
fi

# Remove checkpoint directory
if [ -d "$CHECKPOINT_DIR" ]; then
    echo "Cleaning checkpoints..."
    echo -n "  Removing checkpoints/... "
    rm -rf "$CHECKPOINT_DIR"
    echo -e "${GREEN}✓${NC}"
    echo ""
fi

# Recreate empty directories
mkdir -p "$CHECKPOINT_DIR"
mkdir -p "$UPLOADED_DATASETS_DIR"
touch "$CHECKPOINT_DIR/.gitkeep"
touch "$UPLOADED_DATASETS_DIR/.gitkeep"

echo ""
echo -e "${GREEN}=================================="
echo "Cleanup Complete!"
echo "==================================${NC}"
echo ""
echo "Summary:"
echo "  - All job directories (UUID folders) removed"
echo "  - All uploaded datasets deleted"
echo "  - All logs deleted"
echo "  - All checkpoints cleared"
echo "  - Example CSV files in data/ root preserved"
echo "  - Directory structure preserved"
echo ""
echo "You can start fresh with new annotation jobs."
echo ""

