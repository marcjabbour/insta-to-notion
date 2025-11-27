# Insta → Notion Automation: Architecture & Operations Guide

## 🏗️ System Overview

This document describes the full end-to-end infrastructure for the **Instagram → Notion automation** project, covering Docker, Cloudflare, Oracle Cloud, and GoDaddy integrations.

---

## 1️⃣ ASCII Architecture Diagram

```text
                      ┌─────────────────────┐
                      │   iPhone (iOS 26)   │
                      │  Instagram → Share  │
                      │   → Shortcut →      │
                      │ POST https://...    │
                      └─────────┬───────────┘
                                │
                                │ HTTPS + Header: marcs-key: ****
                                ▼
                    ┌────────────────────────────┐
                    │     Cloudflare (SaaS)      │
                    │                            │
                    │  - DNS for insta2notion.com│
                    │    • n8n.insta2notion.com  │
                    │      CNAME → <TUNNEL_ID>.  │
                    │         cfargotunnel.com   │
                    │  - Proxy / TLS Termination │
                    └─────────┬──────────────────┘
                              │
                              │ Encrypted tunnel
                              ▼
       ┌────────────────────────────────────────────────┐
       │          Cloudflare Tunnel (cloudflared)       │
       │      running on OCI VM as systemd service      │
       │                                                │
       │  /etc/cloudflared/config.yml:                  │
       │    tunnel: <TUNNEL_ID>                         │
       │    ingress:                                    │
       │      - hostname: n8n.insta2notion.com          │
       │        service: http://localhost:5678          │
       └───────────────┬────────────────────────────────┘
                       │
                       │ HTTP (internal)
                       ▼
      ┌──────────────────────────────────────────────────┐
      │        Oracle Cloud (OCI) VM (Ubuntu)           │
      │              Host machine                       │
      │                                                  │
      │  ~/insta-to-notion/                              │
      │    ├─ docker-compose.yml                         │
      │    ├─ Dockerfile                                 │
      │    ├─ insta-extractor.py                         │
      │    └─ workflows/ (exported n8n workflows)        │
      │                                                  │
      │  Docker Engine                                   │
      │    └─ n8n container (service: n8n)               │
      │         - Exposes port 5678 inside VM            │
      │         - Runs n8n app                           │
      │         - Has insta-extractor.py baked in        │
      │         - Uses instaloader + IG session          │
      └───────────────┬──────────────────────────────────┘
                      │
                      ▼
      ┌──────────────────────────────────────────────────┐
      │                  n8n (inside container)          │
      │                                                  │
      │  Webhook Node (POST /webhook/ig-ingest)          │
      │    - Auth: Header Auth (marcs-key: <secret>)     │
      │    - Receives JSON: { url, note }                │
      │         │                                         │
      │         ▼                                         │
      │   Normalize Inputs Node                           │
      │     - Ensures url + note fields are set           │
      │         │                                         │
      │         ▼                                         │
      │   Execute Command Node                            │
      │     - Calls insta-extractor.py <shortcode>        │
      │         │                                         │
      │         ▼                                         │
      │   File/Parsing Nodes                              │
      │     - Read downloaded files                       │
      │     - Send to OpenAI for extraction/summarizing   │
      │         │                                         │
      │         ▼                                         │
      │   Notion Node                                     │
      │     - Writes final record into insta2notion DB    │
      └──────────────────────────────────────────────────┘
```

---

## 2️⃣ Debug & Maintenance Cheatsheet

### A. Cloudflare Tunnel (n8n.insta2notion.com)

Check if it’s active:
```bash
sudo systemctl status cloudflared
```

Restart if needed:
```bash
sudo systemctl restart cloudflared
sudo systemctl status cloudflared
```

View live logs:
```bash
journalctl -u cloudflared -f
```

---

### B. n8n / Docker

```bash
cd ~/insta-to-notion

# See containers
docker compose ps

# View logs
docker compose logs n8n --tail=50

# Restart cleanly
docker compose down
docker compose up -d

# If code changed (e.g. insta-extractor.py)
docker compose build
docker compose up -d
```

---

### C. Quick Tests

**Test locally (on VM):**
```bash
curl -X POST 'http://127.0.0.1:5678/webhook/ig-ingest' \
  -H 'marcs-key: marc726' \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://www.instagram.com/p/DRPk8qPChUC/","note":"local test"}'
```

**Test remotely (through Cloudflare):**
```bash
curl -X POST 'https://n8n.insta2notion.com/webhook/ig-ingest' \
  -H 'marcs-key: marc726' \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://www.instagram.com/p/DRPk8qPChUC/","note":"remote test"}'
```

If local works but remote fails → tunnel issue.
If both fail → n8n issue.

---

### D. Edit Workflow Without Rebuilding

1. SSH to VM:
   ```bash
   ssh -L 5678:localhost:5678 ubuntu@<YOUR_OCI_IP>
   ```
2. On your Mac, open [http://localhost:5678](http://localhost:5678)
3. Import or edit workflow in n8n UI, then activate.

---

### E. Update the Extractor Script

```bash
cd ~/insta-to-notion
nano insta-extractor.py
```

After saving:
```bash
docker compose build
docker compose down
docker compose up -d
```

---

### F. Re-login to Instagram (session refresh)

Inside the n8n container:
```bash
cd ~/insta-to-notion
docker compose exec n8n /bin/sh
instaloader --login=marcjabbour
exit
```

Make sure `insta-extractor.py` uses:
```python
"--sessionfile", "/home/node/.config/instaloader/session-marcjabbour",
```

---

## 3️⃣ iOS Shortcut Configuration

**Trigger:** Share Sheet → Instagram URL

**Actions:**
1. Get Contents of URL
2. Method: POST
3. URL: `https://n8n.insta2notion.com/webhook/ig-ingest`
4. Request Body: JSON
   ```json
   {
     "url": Shortcut Input,
     "note": "Ask Each Time"
   }
   ```
5. Headers:
   ```json
   {
     "marcs-key": "marc726"
   }
   ```
6. (Optional) Show Notification: "✅ Sent to n8n"

---

## 4️⃣ Instagram Rate-Limiting Notes

If you see:
> `Please wait a few minutes before you try again.`

It means Instagram rate-limited you. Mitigations:
- Lower call frequency.
- Always use `--sessionfile` (logged-in requests).
- If it persists: wait 30–60 minutes.

---

## 5️⃣ Summary of Key Paths

| Purpose | Path |
|----------|------|
| Project Root | `~/insta-to-notion/` |
| Docker Compose File | `~/insta-to-notion/docker-compose.yml` |
| Python Extractor | `~/insta-to-notion/insta-extractor.py` |
| IG Session File | `/home/node/.config/instaloader/session-marcjabbour` |
| Cloudflare Config | `/etc/cloudflared/config.yml` |

---

## 🧠 Quick Recap

**Primary Workflow:**
- iOS Shortcut → Cloudflare Tunnel → OCI VM → n8n Webhook → Python Extractor → Notion

**To debug:**
- Check `cloudflared` → then `docker compose ps` → then n8n logs.

**To update:**
- Workflow only → edit via port-forward & n8n UI.
- Python logic → edit, rebuild Docker.

---

✅ _This architecture is designed for reliability and minimal maintenance — Cloudflare handles public access and TLS, OCI provides the always-on compute, and Docker isolates the n8n + Python environment._