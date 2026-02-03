#!/bin/bash
# ==========================================
# High-Speed Camera App - Native Deployment Script
# ==========================================
# Usage: ./deploy.sh [command]
#
#   ./deploy.sh              # Interactive mode
#   ./deploy.sh start        # Start the app
#   ./deploy.sh stop         # Stop the app
#   ./deploy.sh check        # Check dependencies only
#   ./deploy.sh install      # Install dependencies only
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

# Required Python version
PYTHON_VERSION="3.13"
VENV_DIR="$SCRIPT_DIR/.venv"
PID_FILE="$SCRIPT_DIR/.app.pid"

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

# Check operating system
detect_os() {
    case "$(uname -s)" in
        Darwin*)    echo "macos" ;;
        Linux*)     echo "linux" ;;
        CYGWIN*|MINGW*|MSYS*) echo "windows" ;;
        *)          echo "unknown" ;;
    esac
}

OS=$(detect_os)

# Check if Python is installed and meets version requirement
check_python() {
    print_status "Checking Python installation..."

    # Ensure uv is installed first (needed for Python management)
    if ! command -v uv &> /dev/null; then
        print_warning "uv is required for Python management but is not installed"
        install_uv
    fi

    # First, try uv's managed Python
    if command -v uv &> /dev/null; then
        UV_PYTHON=$(uv python find python$PYTHON_VERSION 2>/dev/null || uv python find 3 2>/dev/null || true)
        if [ -n "$UV_PYTHON" ] && [ -f "$UV_PYTHON" ]; then
            PYTHON_CMD="$UV_PYTHON"
            PYTHON_VERSION_INSTALLED=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
            print_status "Found uv-managed Python $PYTHON_VERSION_INSTALLED"

            # Check if version meets requirement
            PYTHON_MAJOR=$(echo "$PYTHON_VERSION_INSTALLED" | cut -d. -f1)
            PYTHON_MINOR=$(echo "$PYTHON_VERSION_INSTALLED" | cut -d. -f2)
            REQUIRED_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
            REQUIRED_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

            if [ "$PYTHON_MAJOR" -ge "$REQUIRED_MAJOR" ] && [ "$PYTHON_MINOR" -ge "$REQUIRED_MINOR" ]; then
                print_success "Python $PYTHON_VERSION_INSTALLED is ready"
                return
            fi
        fi
    fi

    # Fallback: Check system Python
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        PYTHON_CMD=""
    fi

    if [ -z "$PYTHON_CMD" ]; then
        print_error "Python is not installed"
        echo ""
        read -p "Would you like to install Python $PYTHON_VERSION using uv? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            install_python_uv
        else
            print_error "Python is required to run this application"
            exit 1
        fi
        return
    fi

    # Check Python version
    PYTHON_VERSION_INSTALLED=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
    print_status "Found system Python $PYTHON_VERSION_INSTALLED"

    # Compare versions (major.minor)
    PYTHON_MAJOR=$(echo "$PYTHON_VERSION_INSTALLED" | cut -d. -f1)
    PYTHON_MINOR=$(echo "$PYTHON_VERSION_INSTALLED" | cut -d. -f2)
    REQUIRED_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
    REQUIRED_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

    if [ "$PYTHON_MAJOR" -lt "$REQUIRED_MAJOR" ] || ([ "$PYTHON_MAJOR" -eq "$REQUIRED_MAJOR" ] && [ "$PYTHON_MINOR" -lt "$REQUIRED_MINOR" ]); then
        print_warning "Python $PYTHON_VERSION or higher is required (found $PYTHON_VERSION_INSTALLED)"
        echo ""
        read -p "Would you like to install Python $PYTHON_VERSION using uv? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            install_python_uv
        else
            print_error "Python $PYTHON_VERSION or higher is required"
            exit 1
        fi
        return
    fi

    print_success "Python $PYTHON_VERSION_INSTALLED is installed"
}

# Check if Homebrew is installed
check_homebrew() {
    if command -v brew &> /dev/null; then
        return 0
    fi
    
    print_warning "Homebrew is not installed"
    echo ""
    read -p "Would you like to install Homebrew? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        install_homebrew
    else
        print_error "Homebrew is required to install Python on macOS"
        echo "Alternatively, download Python directly from:"
        echo "  https://www.python.org/downloads/"
        exit 1
    fi
}

# Install Homebrew
install_homebrew() {
    print_status "Installing Homebrew..."
    echo "This may take a few minutes..."
    echo ""
    
    # Official Homebrew installer
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add Homebrew to PATH for this session
    if [ -d "/opt/homebrew/bin" ]; then
        # Apple Silicon
        eval "$(/opt/homebrew/bin/brew shellenv)"
    elif [ -d "/usr/local/bin" ]; then
        # Intel Mac
        eval "$(/usr/local/bin/brew shellenv)"
    fi
    
    if command -v brew &> /dev/null; then
        BREW_VERSION=$(brew --version | head -n1)
        print_success "Homebrew installed: $BREW_VERSION"
    else
        print_error "Failed to install Homebrew"
        echo "Please try installing manually:"
        echo '  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
        exit 1
    fi
}

# Legacy OS-based Python installation (fallback)
# Kept for reference, but uv-based install is preferred
install_python_legacy() {
    print_warning "Using legacy OS package manager for Python installation..."

    case $OS in
        macos)
            if command -v brew &> /dev/null; then
                print_status "Using Homebrew to install Python..."
                brew install python@$PYTHON_VERSION
                brew link python@$PYTHON_VERSION --force --overwrite 2>/dev/null || true
            else
                print_error "Homebrew not available for legacy install"
                exit 1
            fi
            ;;
        linux)
            if command -v apt-get &> /dev/null; then
                print_status "Using apt to install Python..."
                sudo apt-get update
                sudo apt-get install -y python$PYTHON_VERSION python$PYTHON_VERSION-venv python$PYTHON_VERSION-pip
            elif command -v dnf &> /dev/null; then
                sudo dnf install -y python$PYTHON_VERSION python$PYTHON_VERSION-pip
            elif command -v yum &> /dev/null; then
                sudo yum install -y python$PYTHON_VERSION python$PYTHON_VERSION-pip
            else
                print_error "No supported package manager found"
                exit 1
            fi
            ;;
        *)
            print_error "Legacy install not supported on this OS"
            exit 1
            ;;
    esac
}

# Check if uv is installed
check_uv() {
    print_status "Checking uv installation..."
    
    if command -v uv &> /dev/null; then
        UV_VERSION=$(uv --version 2>&1 | awk '{print $2}')
        print_success "uv $UV_VERSION is installed"
        return
    fi
    
    print_warning "uv is not installed"
    echo ""
    read -p "Would you like to install uv? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        install_uv
    else
        print_error "uv is required for dependency management"
        exit 1
    fi
}

# Install uv
install_uv() {
    print_status "Installing uv..."

    # Official uv installer
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # Add to PATH for this session
    export PATH="$HOME/.local/bin:$PATH"

    if command -v uv &> /dev/null; then
        UV_VERSION=$(uv --version 2>&1 | awk '{print $2}')
        print_success "uv $UV_VERSION installed successfully"
    else
        print_error "Failed to install uv"
        echo "Please try installing manually:"
        echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi
}

# Install Python using uv
install_python_uv() {
    print_status "Installing Python $PYTHON_VERSION using uv..."

    # Install specific Python version with uv
    uv python install $PYTHON_VERSION

    # Pin Python version for this project
    uv python pin $PYTHON_VERSION

    print_success "Python $PYTHON_VERSION installed and pinned"
}

# Get the Python executable path from venv
get_venv_python() {
    if [ "$OS" = "windows" ] || [ "$OS" = "msys" ]; then
        echo "$VENV_DIR/Scripts/python.exe"
    else
        echo "$VENV_DIR/bin/python"
    fi
}

# Get the pip executable path from venv
get_venv_pip() {
    if [ "$OS" = "windows" ] || [ "$OS" = "msys" ]; then
        echo "$VENV_DIR/Scripts/pip.exe"
    else
        echo "$VENV_DIR/bin/pip"
    fi
}

# Check if venv is valid
is_venv_valid() {
    if [ ! -d "$VENV_DIR" ]; then
        return 1
    fi
    
    local venv_python
    venv_python=$(get_venv_python)
    
    if [ ! -f "$venv_python" ]; then
        return 1
    fi
    
    # Test if Python works
    if ! "$venv_python" --version &> /dev/null; then
        return 1
    fi
    
    return 0
}

# Setup virtual environment and install dependencies
install_dependencies() {
    print_status "Setting up virtual environment for this project..."
    print_status "Venv location: $VENV_DIR"

    # First, ensure the required Python version is available via uv
    # uv will download and install it if needed
    print_status "Ensuring Python $PYTHON_VERSION is available..."
    uv python install $PYTHON_VERSION --quiet

    # Pin Python version for this project
    if [ ! -f ".python-version" ]; then
        uv python pin $PYTHON_VERSION
        print_success "Pinned Python $PYTHON_VERSION for this project"
    fi

    # Check if we should recreate the venv
    if [ -d "$VENV_DIR" ]; then
        if [ "${FORCE_REINSTALL:-0}" = "1" ]; then
            print_warning "Force reinstall requested, removing existing venv..."
            rm -rf "$VENV_DIR"
        elif ! is_venv_valid; then
            print_warning "Existing virtual environment is corrupted, recreating..."
            rm -rf "$VENV_DIR"
        else
            # Check if venv uses correct Python version
            local venv_python
            venv_python=$(get_venv_python)
            local venv_version
            venv_version=$("$venv_python" --version 2>&1 | awk '{print $2}')
            local venv_major_minor
            venv_major_minor=$(echo "$venv_version" | cut -d. -f1,2)

            if [ "$venv_major_minor" != "$PYTHON_VERSION" ]; then
                print_warning "Virtual environment uses Python $venv_version, but $PYTHON_VERSION is required"
                print_status "Recreating virtual environment with Python $PYTHON_VERSION..."
                rm -rf "$VENV_DIR"
            else
                print_status "Virtual environment already exists with Python $venv_version"
            fi
        fi
    fi

    # Create venv if it doesn't exist (uv will use the pinned version)
    if [ ! -d "$VENV_DIR" ]; then
        uv venv "$VENV_DIR"
        print_success "Created virtual environment at $VENV_DIR"
    fi

    # Verify venv Python version
    local venv_python
    venv_python=$(get_venv_python)
    local venv_version
    venv_version=$("$venv_python" --version 2>&1 | awk '{print $2}')
    print_status "Using Python $venv_version from virtual environment"

    # Upgrade pip in venv
    print_status "Upgrading pip in virtual environment..."
    "$venv_python" -m pip install --upgrade pip -q

    # Install dependencies
    print_status "Installing dependencies into virtual environment..."
    uv pip install --python "$venv_python" -e "."

    print_success "Dependencies installed successfully in $VENV_DIR"
    echo ""
    echo "Python version pinned: $(cat .python-version)"
    echo ""
    echo "To activate the virtual environment manually:"
    if [ "$OS" = "windows" ] || [ "$OS" = "msys" ]; then
        echo "  source $VENV_DIR/Scripts/activate"
    else
        echo "  source $VENV_DIR/bin/activate"
    fi
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
        echo "  GRADIO_PORT=7860            # Web interface port"
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
        # Source the .env file
        set -a
        source .env
        set +a
        
        if [ -n "$CAMERA_IP" ]; then
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
    local mode=$1
    
    # Check if already running
    if [ -f "$PID_FILE" ]; then
        local existing_pid
        existing_pid=$(cat "$PID_FILE" 2>/dev/null)
        if ps -p "$existing_pid" > /dev/null 2>&1; then
            print_warning "App is already running (PID: $existing_pid)"
            echo "Visit: http://localhost:${GRADIO_PORT:-7860}"
            return
        else
            rm -f "$PID_FILE"
        fi
    fi
    
    print_status "Starting camera app in $mode mode..."
    
    # Source environment variables
    if [ -f ".env" ]; then
        set -a
        source .env
        set +a
    fi
    
    local port=${GRADIO_PORT:-7860}
    local camera_ip=${CAMERA_IP:-}
    
    # Build command using venv Python
    local venv_python
    venv_python=$(get_venv_python)
    local cmd="$venv_python main.py --port $port"
    if [ -n "$camera_ip" ] && [ "$mode" != "webcam" ]; then
        cmd="$cmd --camera-ip $camera_ip"
    fi
    
    # Start in background
    print_status "Launching: $cmd"
    nohup $cmd > app.log 2>&1 &
    local pid=$!
    echo $pid > "$PID_FILE"
    
    # Wait a moment to check if it started successfully
    sleep 2
    if ps -p "$pid" > /dev/null 2>&1; then
        print_success "App started successfully!"
        echo ""
        echo "=========================================="
        echo "Camera App is running!"
        echo "=========================================="
        echo ""
        echo "Web interface: http://localhost:$port"
        echo "PID: $pid"
        echo ""
        echo "To stop the app:"
        echo "  ./deploy.sh stop"
        echo ""
        echo "To view logs:"
        echo "  tail -f app.log"
        echo ""
        
        # Try to open browser
        if command -v open &> /dev/null; then
            sleep 1
            open "http://localhost:$port"
        elif command -v xdg-open &> /dev/null; then
            sleep 1
            xdg-open "http://localhost:$port"
        fi
    else
        print_error "Failed to start app"
        rm -f "$PID_FILE"
        echo "Check the logs: cat app.log"
        exit 1
    fi
}

# Stop the application
stop_app() {
    print_status "Stopping camera app..."
    
    local stopped=0
    
    # Try PID file first
    if [ -f "$PID_FILE" ]; then
        local pid
        pid=$(cat "$PID_FILE" 2>/dev/null)
        if [ -n "$pid" ] && ps -p "$pid" > /dev/null 2>&1; then
            kill "$pid" 2>/dev/null
            sleep 1
            if ps -p "$pid" > /dev/null 2>&1; then
                kill -9 "$pid" 2>/dev/null
            fi
            print_success "Stopped app (PID: $pid)"
            stopped=1
        fi
        rm -f "$PID_FILE"
    fi
    
    # Also check for any running main.py processes
    local pids
    pids=$(pgrep -f "python.*main\.py" 2>/dev/null || true)
    if [ -n "$pids" ]; then
        echo "$pids" | while read -r pid; do
            if [ -n "$pid" ]; then
                kill "$pid" 2>/dev/null || true
                print_success "Stopped process (PID: $pid)"
                stopped=1
            fi
        done
    fi
    
    if [ "$stopped" -eq 0 ]; then
        print_warning "No running app found"
    fi
}

# View logs
view_logs() {
    if [ -f "app.log" ]; then
        tail -f app.log
    else
        print_warning "No log file found"
    fi
}

# Show interactive menu
show_menu() {
    echo ""
    echo "=========================================="
    echo "High-Speed Camera App Deployment"
    echo "=========================================="
    echo ""
    echo "Choose action:"
    echo ""
    echo "  1) Start App    - Launch the camera app"
    echo "  2) Stop App     - Stop the running app"
    echo "  3) View Logs    - Watch application logs"
    echo "  4) Install Only - Just install dependencies"
    echo "  5) Clean/Reinstall - Remove venv and start fresh"
    echo "  6) Exit"
    echo ""
    read -p "Enter choice [1-6]: " choice

    case $choice in
        1)
            setup_env
            validate_camera
            start_app "camera"
            ;;
        2)
            stop_app
            ;;
        3)
            view_logs
            ;;
        4)
            install_dependencies
            ;;
        5)
            print_status "Cleaning virtual environment..."
            stop_app 2>/dev/null || true
            rm -rf "$VENV_DIR"
            rm -f "$PID_FILE"
            rm -f app.log
            print_success "Virtual environment cleaned"
            echo ""
            read -p "Would you like to reinstall dependencies? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                check_python
                check_uv
                install_dependencies
            fi
            ;;
        6)
            print_status "Exiting..."
            exit 0
            ;;
        *)
            print_error "Invalid choice"
            show_menu
            ;;
    esac
}

# Check all dependencies
check_all() {
    echo ""
    echo "=========================================="
    echo "Dependency Check"
    echo "=========================================="
    echo ""
    check_python
    check_uv
    echo ""
    print_success "All dependencies are ready!"
}

# Main function
main() {
    echo ""
    echo "=========================================="
    echo "High-Speed Camera App Deployment"
    echo "=========================================="
    echo ""
    
    # Handle command-line argument
    case "${1:-}" in
        "start"|"run")
            check_python
            check_uv
            if [ ! -d "$VENV_DIR" ]; then
                install_dependencies
            fi
            setup_env
            validate_camera
            start_app "camera"
            ;;
        "stop"|"down"|"kill")
            stop_app
            ;;
        "logs"|"log")
            view_logs
            ;;
        "install"|"setup")
            check_python
            check_uv
            install_dependencies
            ;;
        "clean"|"reset")
            print_status "Cleaning virtual environment..."
            stop_app 2>/dev/null || true
            rm -rf "$VENV_DIR"
            rm -f "$PID_FILE"
            rm -f app.log
            print_success "Virtual environment cleaned"
            echo ""
            read -p "Would you like to reinstall dependencies? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                check_python
                check_uv
                install_dependencies
            fi
            ;;
        "check"|"verify"|"test")
            check_all
            ;;
        "help"|"--help"|"-h")
            echo "Usage: ./deploy.sh [command]"
            echo ""
            echo "Commands:"
            echo "  start       Launch the camera app"
            echo "  stop        Stop the running app"
            echo "  logs        View application logs"
            echo "  install     Install dependencies only"
            echo "  clean       Remove venv and reinstall (fresh start)"
            echo "  check       Check dependencies only"
            echo "  help        Show this help message"
            echo ""
            echo "Without arguments, shows interactive menu"
            echo ""
            echo "The script will:"
            echo "  1. Check for Python 3.13+ (offer to install if missing)"
            echo "  2. Check for uv (offer to install if missing)"
            echo "  3. Create virtual environment at $VENV_DIR"
            echo "  4. Install dependencies from pyproject.toml"
            echo "  5. Start the Gradio app on http://localhost:7860"
            ;;
        "clean"|"reset")
            print_status "Cleaning virtual environment..."
            stop_app 2>/dev/null || true
            rm -rf "$VENV_DIR"
            rm -f "$PID_FILE"
            rm -f app.log
            print_success "Virtual environment cleaned"
            echo ""
            read -p "Would you like to reinstall dependencies? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                check_python
                check_uv
                install_dependencies
            fi
            ;;
        "")
            check_python
            check_uv
            if [ ! -d "$VENV_DIR" ]; then
                install_dependencies
            fi
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
