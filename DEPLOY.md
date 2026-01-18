# Server Deployment Guide

## Quick Deploy Commands

### 1. Install Dependencies
```bash
cd realtime-rag-dynamic
pip install -r requirements.txt
```

### 2. Configure Environment
Edit `.env` with your credentials (already done)

### 3. Run Server
```bash
python app.py
```

Server runs on: http://0.0.0.0:8003

---

## Production Deployment

### Option 1: Run with Gunicorn (Recommended)
```bash
pip install gunicorn
gunicorn app:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8003
```

### Option 2: Run with systemd (Linux)

Create `/etc/systemd/system/realtime-rag.service`:
```ini
[Unit]
Description=Realtime RAG Dynamic Service
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/realtime-rag-dynamic
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable realtime-rag
sudo systemctl start realtime-rag
sudo systemctl status realtime-rag
```

### Option 3: Run with Docker

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8003
CMD ["python", "app.py"]
```

Build and run:
```bash
docker build -t realtime-rag .
docker run -d -p 8003:8003 --env-file .env realtime-rag
```

### Option 4: Run with PM2 (Node.js process manager)
```bash
npm install -g pm2
pm2 start app.py --name realtime-rag --interpreter python3
pm2 save
pm2 startup
```

---

## Nginx Reverse Proxy (Optional)

Create `/etc/nginx/sites-available/realtime-rag`:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8003;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Enable:
```bash
sudo ln -s /etc/nginx/sites-available/realtime-rag /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Firewall Rules
```bash
# Allow port 8003
sudo ufw allow 8003/tcp

# Or if using nginx
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

---

## Monitoring

Check logs:
```bash
# If using systemd
sudo journalctl -u realtime-rag -f

# If using PM2
pm2 logs realtime-rag

# If using Docker
docker logs -f container-id
```

---

## Quick Test

After deployment, test:
```bash
curl http://your-server:8003/
```

Should return the HTML page.

Open in browser:
```
http://your-server:8003/
```
