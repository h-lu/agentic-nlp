# =============================================================================
# Docusaurus Course Site - Makefile
# =============================================================================
# Convenient commands for building and managing the course site.
#
# Usage:
#   make help          - Show all available commands
#   make install       - Install dependencies
#   make dev           - Start development server with hot reload
#   make build         - Build production version
#   make clean         - Clean build artifacts
# =============================================================================

# ------------------------------------------------------------------------------
# Configuration - Modify these if your directories are different
# ------------------------------------------------------------------------------
PYTHON := python3
SITE_DIR := site
SCRIPTS_DIR := scripts

# Content directories (customize based on your course structure)
CHAPTERS_DIR := ../../chapters
SHARED_DIR := ../../shared

# Output directory (relative to project root)
OUTPUT_DIR := ../../dist

# ------------------------------------------------------------------------------
# Colors for terminal output
# ------------------------------------------------------------------------------
BLUE := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
NC := \033[0m # No Color

# ------------------------------------------------------------------------------
# Default target
# ------------------------------------------------------------------------------
.PHONY: help
help: ## Show this help message
	@echo ""
	@echo "$(BLUE)╔══════════════════════════════════════════════════════════════════════╗$(NC)"
	@echo "$(BLUE)║              Docusaurus Course Site - Available Commands             ║$(NC)"
	@echo "$(BLUE)╚══════════════════════════════════════════════════════════════════════╝$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""

# =============================================================================
# Site Build Commands
# =============================================================================

.PHONY: install dev build clean

install: ## Install site dependencies
	@echo "$(BLUE)Installing site dependencies...$(NC)"
	cd $(SITE_DIR) && npm install
	@echo "$(GREEN)Dependencies installed successfully!$(NC)"

dev: ## Generate documentation and start development server
	@echo "$(BLUE)Generating documentation...$(NC)"
	$(PYTHON) $(SCRIPTS_DIR)/build_site.py --chapters-dir $(CHAPTERS_DIR) --shared-dir $(SHARED_DIR) --verbose
	@echo "$(GREEN)Documentation generated!$(NC)"
	@echo "$(BLUE)Starting development server...$(NC)"
	cd $(SITE_DIR) && npm run start

build: ## Generate documentation and build production version
	@echo "$(BLUE)Generating documentation...$(NC)"
	$(PYTHON) $(SCRIPTS_DIR)/build_site.py --chapters-dir $(CHAPTERS_DIR) --shared-dir $(SHARED_DIR) --verbose
	@echo "$(GREEN)Documentation generated!$(NC)"
	@echo "$(BLUE)Building production site...$(NC)"
	cd $(SITE_DIR) && npm run build
	@echo "$(BLUE)Copying to output directory...$(NC)"
	@rm -rf $(OUTPUT_DIR) && mkdir -p $(OUTPUT_DIR) && cp -r $(SITE_DIR)/build/* $(OUTPUT_DIR)/
	@echo "$(GREEN)Build completed! Output: $(OUTPUT_DIR)/$(NC)"
	@echo ""
	@echo "$(BLUE)To deploy, upload the contents of $(OUTPUT_DIR)/ to your hosting service.$(NC)"

clean: ## Clean site build artifacts
	@echo "$(YELLOW)Cleaning site build artifacts...$(NC)"
	cd $(SITE_DIR) && rm -rf build .docusaurus
	find $(SITE_DIR)/docs -name "*.mdx" -delete 2>/dev/null || true
	find $(SITE_DIR)/docs -type d -empty -delete 2>/dev/null || true
	rm -f $(SITE_DIR)/sidebars.ts
	rm -rf $(OUTPUT_DIR)
	@echo "$(GREEN)Site cleaned successfully!$(NC)"

# =============================================================================
# Utility Commands
# =============================================================================

.PHONY: check-deps update-deps

check-deps: ## Check if required dependencies are installed
	@echo "$(BLUE)Checking dependencies...$(NC)"
	@which node > /dev/null && echo "  $(GREEN)✓$(NC) Node.js: $$(node --version)" || echo "  $(RED)✗$(NC) Node.js not found"
	@which npm > /dev/null && echo "  $(GREEN)✓$(NC) npm: $$(npm --version)" || echo "  $(RED)✗$(NC) npm not found"
	@which $(PYTHON) > /dev/null && echo "  $(GREEN)✓$(NC) Python: $$($(PYTHON) --version)" || echo "  $(RED)✗$(NC) Python not found"
	@test -d $(SITE_DIR)/node_modules && echo "  $(GREEN)✓$(NC) Site dependencies installed" || echo "  $(YELLOW)⚠$(NC) Site dependencies not installed (run: make install)"

update-deps: ## Update site dependencies
	@echo "$(BLUE)Updating site dependencies...$(NC)"
	cd $(SITE_DIR) && npm update
	@echo "$(GREEN)Dependencies updated!$(NC)"
