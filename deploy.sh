#!/bin/bash
# ==========================================
# High-Speed Camera App - Deployment Script
# ==========================================
# Usage: ./deploy.sh [profile]
#
#   ./deploy.sh              # Interactive mode
#   ./deploy.sh development  # Build from source
#   ./deploy.sh production   # Use pre-built image
#   ./deploy.sh webcam       # Test with webcam
#   ./deploy.sh stop         # Stop the app
#
# ==========================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Function to print colored messages
print_status() {
    echo -e "${BLUE}→${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        echo ""
        echo "Please install Docker Desktop:"
        echo "  - macOS: https://docs.docker.com/desktop/install/mac-install/"
        echo "  - Windows: https://docs.docker.com/desktop/install/windows-install/"
        echo "  - Linux: https://docs.docker.com/desktop/install/linux-install/"
        exit 1
    fi
    
    if ! docker compose version &> /dev/null; then
        print_error "Docker Compose plugin not found"
        echo ""
        echo "Docker Desktop includes Docker Compose. If using Linux, install:"
        echo "  sudo apt-get install docker-compose-plugin"
        exit 1
    fi
    
    print_success "Docker is installed"
}

# Check if Docker daemon is running
check_docker_running() {
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running"
        echo ""
        echo "Please start Docker Desktop or the Docker service"
        exit 1
    fi
    print_success "Docker is running"
}

# Setup .env file if it doesn't exist
setup_env() {
    if [ ! -f ".env" ]; then
        print_warning ".env file not found"
        print_status "Creating .env from template..."
        cp .env.example .env
        print_success "Created .env file"
        echo ""
        echo "=========================================="
        echo "IMPORTANT: Edit .env with your camera IP"
        echo "=========================================="
        echo ""
        echo "File location: $SCRIPT_DIR/.env"
        echo ""
        echo "Key settings to update:"
        echo "  CAMERA_IP=169.254.22.149    # Your camera's IP"
        echo "  COMPOSE_PROFILES=development # or 'production' or 'webcam'"
        echo ""
        
        # Try to open in default editor
        if command -v nano &> /dev/null; then
            echo "Opening in nano editor..."
            nano .env
        elif command -v code &> /dev/null; then
            echo "Opening in VS Code..."
            code .env
        else
            echo "Please edit the file manually with your favorite editor"
            echo ""
            echo "Press Enter when ready to continue..."
            read
        fi
        
        print_success "Configuration saved"
    fi
}

# Validate camera network connectivity
validate_camera() {
    if [ -f ".env" ]; then
        source .env
        
        if [ -n "$CAMERA_IP" ] && [ "$COMPOSE_PROFILES" != "webcam" ]; then
            print_status "Checking camera connectivity at $CAMERA_IP..."
            
            # Check if we can ping the camera
            if ping -c 1 -W 2 "$CAMERA_IP" &> /dev/null; then
                print_success "Camera is reachable at $CAMERA_IP"
            else
                print_warning "Cannot reach camera at $CAMERA_IP"
                echo ""
                echo "Possible issues:"
                echo "  1. Camera is not powered on"
                echo "  2. Camera is not connected to network"
                echo "  3. Wrong IP address in .env file"
                echo "  4. Firewall blocking connection"
                echo ""
                echo "The app will try to connect anyway and may fall back to webcam mode."
                echo ""
                read -p "Continue anyway? (y/n) " -n 1 -r
                echo
                if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                    print_status "Deployment cancelled"
                    exit 0
                fi
            fi
        fi
    fi
}

# Start the application
start_app() {
    local profile=$1
    
    print_status "Starting camera app with profile: $profile"
    
    # Set the profile
    export COMPOSE_PROFILES="$profile"
    
    # Build and start
    docker compose up --build -d
    
    if [ $? -eq 0 ]; then
        print_success "App started successfully!"
        echo ""
        echo "=========================================="
        echo "Camera App is running!"
        echo "=========================================="
        echo ""
        echo "Web interface: http://localhost:${GRADIO_PORT:-7860}"
        echo ""
        echo "To stop the app:"
        echo "  ./deploy.sh stop"
        echo ""
        echo "To view logs:"
        echo "  docker compose logs -f"
        echo ""
    else
        print_error "Failed to start app"
        exit 1
    fi
}

# Stop the application
stop_app() {
    print_status "Stopping camera app..."
    docker compose down
    print_success "App stopped"
}

# Show interactive menu
show_menu() {
    echo ""
    echo "=========================================="
    echo "High-Speed Camera App Deployment"
    echo "=========================================="
    echo ""
    echo "Choose deployment mode:"
    echo ""
    echo "  1) Development  - Build from local source (recommended for testing)"
    echo "  2) Production   - Use pre-built Docker image"
    echo "  3) Webcam Mode  - Test without camera hardware"
    echo "  4) Stop App     - Stop running containers"
    echo "  5) Exit"
    echo ""
    read -p "Enter choice [1-5]: " choice
    
    case $choice in
        1)
            start_app "development"
            ;;
        2)
            start_app "production"
            ;;
        3)
            start_app "webcam"
            ;;
        4)
            stop_app
            ;;
        5)
            print_status "Exiting..."
            exit 0
            ;;
        *)
            print_error "Invalid choice"
            show_menu
            ;;
    esac
}

# Main function
main() {
    echo ""
    echo "=========================================="
    echo "High-Speed Camera App Deployment"
    echo "=========================================="
    echo ""
    
    # Pre-flight checks
    check_docker
    check_docker_running
    
    # Handle command-line argument
    case "${1:-}" in
        "development"|"dev")
            setup_env
            validate_camera
            start_app "development"
            ;;
        "production"|"prod")
            setup_env
            validate_camera
            start_app "production"
            ;;
        "webcam"|"test")
            setup_env
            start_app "webcam"
            ;;
        "stop"|"down")
            stop_app
            ;;
        "help"|"--help"|"-h")
            echo "Usage: ./deploy.sh [command]"
            echo ""
            echo "Commands:"
            echo "  development   Build and run from source"
            echo "  production    Run pre-built Docker image"
            echo "  webcam        Run in webcam test mode"
            echo "  stop          Stop the application"
            echo "  help          Show this help message"
            echo ""
            echo "Without arguments, shows interactive menu"
            ;;
        "")
            setup_env
            validate_camera
            show_menu
            ;;
        *)
            print_error "Unknown command: $1"
            echo "Run './deploy.sh help' for usage information"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
