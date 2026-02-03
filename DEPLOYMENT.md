# High-Speed Camera App - Deployment Guide

This guide helps you deploy the camera application using Docker. No Docker experience is required.

## Quick Start (3 Steps)

### 1. Install Docker

**macOS:**
```bash
# Download Docker Desktop
# Visit: https://docs.docker.com/desktop/install/mac-install/
```

**Windows:**
```bash
# Download Docker Desktop
# Visit: https://docs.docker.com/desktop/install/windows-install/
```

**Linux (Ubuntu/Debian):**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# Log out and log back in for changes to take effect
```

### 2. Clone and Configure

```bash
# Clone the repository
git clone <your-repo-url>
cd high-speed-camera-testing

# Run the deployment script
./deploy.sh
```

The script will create a `.env` file. **Edit it** with your camera's IP address:

```bash
# Open .env in your editor
nano .env    # or code .env, vim .env, etc.
```

Set your camera IP:
```
CAMERA_IP=169.254.22.149    # Replace with your camera's actual IP
```

### 3. Start the App

Run the deployment script again:

```bash
./deploy.sh
```

Choose option `1) Development` to build from source, or `2) Production` for pre-built image.

**Access the app:** Open http://localhost:7860 in your browser

---

## Deployment Modes

### Development Mode (Recommended for Testing)
Builds the app from your local source code. Best for:
- First-time setup
- Testing changes
- Debugging issues

```bash
./deploy.sh development
# or
COMPOSE_PROFILES=development docker compose up --build
```

### Production Mode (Recommended for Deployment)
Uses a pre-built Docker image from Docker Hub. Best for:
- Sharing with colleagues
- Stable deployments
- Faster startup

```bash
./deploy.sh production
# or
COMPOSE_PROFILES=production docker compose up
```

### Webcam Mode (Testing Only)
Runs without MindVision camera hardware. Uses your computer's webcam.

```bash
./deploy.sh webcam
# or
COMPOSE_PROFILES=webcam docker compose up --build
```

---

## Configuration

### Environment Variables

Edit the `.env` file to customize your deployment:

| Variable | Default | Description |
|----------|---------|-------------|
| `CAMERA_IP` | `169.254.22.149` | Your GigE camera's IP address |
| `CAMERA_PORT` | `8080` | Camera port (usually not needed) |
| `GRADIO_PORT` | `7860` | Web interface port |
| `COMPOSE_PROFILES` | `development` | Deployment mode |

### Finding Your Camera IP

1. **Check camera documentation** - IP is often on a label
2. **Use camera manufacturer's software** - MindVision provides tools
3. **Network scan** - Use `arp -a` or network scanner tools
4. **Link-local addresses** - Cameras often use 169.254.x.x range

### Network Requirements

- Camera and computer must be on the same subnet
- No firewall blocking port 554 (RTSP) or port 3956 (GigE Vision)
- For link-local addresses (169.254.x.x), ensure network adapter supports it

---

## Using the Application

### Access the Web Interface

Open your browser and navigate to:
```
http://localhost:7860
```

### Downloading Clips

1. Capture video using the Gradio interface
2. Clips are saved to the `clips/` folder on your computer
3. Click the download button in the UI
4. Files persist even after stopping the container

### Clip Storage Location

- **Inside Docker:** `/app/clips`
- **On your computer:** `./clips/` (relative to where you run the app)

---

## Troubleshooting

### Docker Not Found

**Problem:** `./deploy.sh` shows "Docker is not installed"

**Solution:** Install Docker Desktop from https://docs.docker.com/get-docker/

### Cannot Reach Camera

**Problem:** "Cannot reach camera at [IP]" warning

**Solutions:**
1. Verify camera is powered on
2. Check network cable connection
3. Confirm IP address in `.env` is correct
4. Try pinging the camera: `ping 169.254.22.149`
5. Check firewall settings

### App Won't Start

**Problem:** Docker containers fail to start

**Solutions:**
```bash
# Check what's running
docker ps

# View logs
docker compose logs

# Restart everything
./deploy.sh stop
./deploy.sh
```

### Port Already in Use

**Problem:** "port 7860 is already allocated"

**Solution:** Change the port in `.env`:
```
GRADIO_PORT=8080
```

Then restart: `./deploy.sh`

### Permission Denied (Linux)

**Problem:** `permission denied while trying to connect to Docker daemon`

**Solution:**
```bash
sudo usermod -aG docker $USER
# Log out and log back in
```

---

## Managing the Application

### Stop the App

```bash
./deploy.sh stop
# or
docker compose down
```

### View Logs

```bash
# Real-time logs
docker compose logs -f

# Last 100 lines
docker compose logs --tail=100
```

### Update to Latest Version

**For Production Mode:**
```bash
./deploy.sh stop
docker pull highspeedcamera/camera-app:latest
./deploy.sh production
```

**For Development Mode:**
```bash
./deploy.sh stop
git pull
./deploy.sh development
```

### Completely Remove

```bash
./deploy.sh stop
docker compose down --volumes --rmi all
```

This removes containers, volumes, and images. Your clips in `./clips/` remain.

---

## Advanced Usage

### Custom Docker Compose

Run with custom environment file:
```bash
docker compose --env-file .env.production up
```

### Build and Push Your Own Image

```bash
# Build
docker build -t your-org/camera-app:v1.0 .

# Push (requires Docker Hub login)
docker push your-org/camera-app:v1.0
```

### Multi-Camera Setup

For multiple cameras, create multiple `.env` files and services:

```bash
# .env.camera1
CAMERA_IP=169.254.22.149
GRADIO_PORT=7860

# .env.camera2  
CAMERA_IP=169.254.22.150
GRADIO_PORT=7861
```

Run each with:
```bash
docker compose --env-file .env.camera1 up -d
docker compose --env-file .env.camera2 up -d
```

---

## Getting Help

1. **Check the logs:** `docker compose logs`
2. **Test camera connectivity:** Edit `main.py` and run with `--check` flag
3. **Review this guide:** Make sure your `.env` is configured correctly
4. **Contact the team:** Reach out to the person who shared this repository

---

## Architecture Overview

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Web Browser   │────→│   Gradio UI  │────→│  Camera App     │
│  localhost:7860 │     │  (Docker)    │     │  (Python)       │
└─────────────────┘     └──────────────┘     └─────────────────┘
                                                      │
                                                      ↓
                                               ┌──────────────┐
                                               │ GigE Camera  │
                                               │  (Network)   │
                                               └──────────────┘
```

- **Docker** runs the Python application in an isolated container
- **Gradio** provides the web interface on port 7860
- **Camera SDK** connects to your GigE MindVision camera
- **Clips** are saved to local `./clips/` folder

---

## Next Steps

After successful deployment:

1. **Test the interface** - Verify video feed appears
2. **Capture a clip** - Try recording and downloading
3. **Share with colleagues** - They can follow this same guide
4. **Customize** - Edit `.env` to adjust settings

Happy filming! 🎥
