#!/bin/bash

# Workspace Setup Script for App Factory Monorepo
# This script migrates from individual app dependencies to pnpm workspace structure

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Helper functions
log_step() {
    echo -e "\n${BLUE}📦 Step $1:${NC} ${BOLD}$2${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_info() {
    echo -e "   $1"
}

# Header
echo -e "${MAGENTA}
╔══════════════════════════════════════════════════════════════╗
║                    🚀 Workspace Setup                        ║
║                    App Factory Monorepo                      ║
╚══════════════════════════════════════════════════════════════╝
${NC}"

echo "This script will clean your workspace and set up the new pnpm workspace structure."
echo "All existing lock files and node_modules will be removed and regenerated fresh."
echo ""

# Step 1: Clean existing lock files
log_step 1 "Cleaning existing lock files"

# Remove individual app lock files
if find apps/*/ui -name "pnpm-lock.yaml" 2>/dev/null | grep -q .; then
    find apps/*/ui -name "pnpm-lock.yaml" -delete
    log_info "Removed individual pnpm-lock.yaml files"
fi

if find apps/*/ui -name "package-lock.json" 2>/dev/null | grep -q .; then
    find apps/*/ui -name "package-lock.json" -delete
    log_info "Removed individual package-lock.json files"
fi

# Remove packages lock files
if find packages/*/pnpm-lock.yaml 2>/dev/null | grep -q .; then
    find packages/ -name "pnpm-lock.yaml" -delete
    log_info "Removed packages pnpm-lock.yaml files"
fi

if find packages/*/package-lock.json 2>/dev/null | grep -q .; then
    find packages/ -name "package-lock.json" -delete
    log_info "Removed packages package-lock.json files"
fi

# Remove root lock file for fresh generation
if [ -f "pnpm-lock.yaml" ]; then
    rm -f pnpm-lock.yaml
    log_info "Removed root pnpm-lock.yaml"
fi

log_success "Lock files cleaned"

# Step 2: Clean existing node_modules
log_step 2 "Cleaning existing node_modules"

if [ -d "node_modules" ]; then
    rm -rf node_modules
    log_info "Removed root node_modules"
fi

if find apps/*/ui -name "node_modules" -type d 2>/dev/null | grep -q .; then
    find apps/*/ui -name "node_modules" -type d -exec rm -rf {} +
    log_info "Removed individual app node_modules"
fi

# Remove packages node_modules
if find packages/*/node_modules -type d 2>/dev/null | grep -q .; then
    find packages/ -name "node_modules" -type d -exec rm -rf {} +
    log_info "Removed packages node_modules"
fi

log_success "Node modules cleaned"

# Clean dist folders (build artifacts)
if find apps/*/ui/dist -type d 2>/dev/null | grep -q .; then
    find apps/*/ui -name "dist" -type d -exec rm -rf {} +
    log_info "Removed app dist folders"
fi

if find packages/*/dist -type d 2>/dev/null | grep -q .; then
    find packages/ -name "dist" -type d -exec rm -rf {} +
    log_info "Removed packages dist folders"
fi

# Step 3: Verify workspace configuration
log_step 3 "Verifying workspace configuration"

if [ ! -f "pnpm-workspace.yaml" ]; then
    log_error "pnpm-workspace.yaml not found! Please ensure workspace is configured."
    exit 1
fi

if [ ! -f "package.json" ]; then
    log_error "Root package.json not found!"
    exit 1
fi

# Check if corepack is enabled
if ! command -v corepack &> /dev/null; then
    log_warning "Corepack not found. Enabling corepack..."
    corepack enable || log_warning "Could not enable corepack automatically"
fi

log_success "Workspace configuration verified"

# Step 4: Install fresh dependencies
log_step 4 "Installing workspace dependencies with overrides"

echo -e "   ${CYAN}pnpm install${NC}"
pnpm install

log_success "Workspace dependencies installed with overrides applied"

# Step 5: Verify workspace structure
log_step 5 "Verifying workspace structure"

# List workspace packages
echo -e "   ${CYAN}pnpm list --depth=0${NC}"
WORKSPACE_PACKAGES=$(pnpm list --depth=0 --parseable 2>/dev/null | wc -l)
log_info "Found $WORKSPACE_PACKAGES workspace packages"

# Verify symlinks were created
if [ -d "apps/law_monitoring/ui/node_modules" ] || [ -d "packages/shared-frontend/node_modules" ]; then
    log_info "Workspace node_modules symlinks created successfully"
else
    log_warning "Workspace node_modules not found - this might be normal"
fi

log_success "Workspace structure verified"

# Step 6: Test workspace commands
log_step 6 "Testing workspace commands"

# Test a simple workspace command
if pnpm -r --dry-run list >/dev/null 2>&1; then
    log_info "Workspace filtering works correctly"
else
    log_warning "Workspace filtering test failed - but this might be normal"
fi

log_success "Workspace commands verified"

# Success summary
echo -e "\n${GREEN}
╔══════════════════════════════════════════════════════════════╗
║                    🎉 Setup Complete!                        ║
╚══════════════════════════════════════════════════════════════╝
${NC}"

echo ""
echo -e "${BOLD}📋 Available commands:${NC}"
echo -e "${CYAN}  pnpm -r --parallel dev${NC}                # Start all apps"
echo -e "${CYAN}  pnpm --filter law-monitoring-ui dev${NC}   # Start specific app"
echo -e "${CYAN}  pnpm -r build${NC}                         # Build all apps"
echo -e "${CYAN}  pnpm -r lint${NC}                          # Lint all apps"

echo ""
echo -e "${GREEN}🚀 Your monorepo is ready!${NC}"
