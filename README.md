# QR Relay — Railway Deployment Package

This directory contains the production-ready package for deploying **QR Relay** to [Railway](https://railway.app).

## Key Deployment Features Included
- **Dockerfile**: Lightweight `python:3.11-slim` container with proxy header support.
- **Dynamic Port**: Binds to `${PORT:-8000}` automatically as required by Railway.
- **Automatic HTTPS / WSS**: Railway edge terminates SSL, so mobile cameras work securely out of the box with zero certificate warnings.
- **WebSocket Fan-out**: Real-time binary camera crop relay with low latency.

---

## Deployment Option 1: Via GitHub (Recommended)

1. Initialize a git repository and push to GitHub:
   ```bash
   cd ~/qr-relay-railway
   git init
   git add .
   git commit -m "Initial Railway deployment package"
   # Create a repo on GitHub, then link and push:
   git branch -M main
   git remote add origin https://github.com/<your-username>/<your-repo-name>.git
   git push -u origin main
   ```
2. Go to [railway.app](https://railway.app) and sign in.
3. Click **New Project** → **Deploy from GitHub repo** → select the repository.
4. Once deployed, click **Settings** → **Networking** → **Generate Domain**.
5. Your service is live at `https://<your-domain>.up.railway.app`:
   - Sender: `https://<your-domain>.up.railway.app/sender.html`
   - Viewer: `https://<your-domain>.up.railway.app/`

---

## Deployment Option 2: Via Railway CLI

If you have the Railway CLI installed:
```bash
cd ~/qr-relay-railway
railway login
railway init
railway up
```
