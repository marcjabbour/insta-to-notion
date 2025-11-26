# 📸 Instagram → Notion Knowledge Vault (n8n + Docker)

This project automates the process of extracting text content from Instagram posts (including multi-image slides), summarizing that content using AI, and storing the results as structured entries in a Notion database.  

It’s powered by **n8n** running inside a **Docker container** with a custom Python + Instaloader integration for image extraction, and OpenAI for OCR and summarization.

---

## 🧠 What This Does

When you send an Instagram post URL to the webhook (e.g., via a curl command or iOS Shortcut):

1. The **Python script (`insta-extractor.py`)** downloads the images for that post using Instaloader.  
2. n8n converts those images to base64 and sends them to **GPT-4o** for text extraction.  
3. The workflow merges the extracted text, summarizes it, and prepares structured content (Title, Summary, Takeaways, etc.).  
4. A new **Notion database page** is created with all the extracted and summarized content.  
5. The temporary image files are automatically deleted from the container.  

---

## 🧱 Tech Stack

| Layer | Technology | Purpose |
|-------|-------------|----------|
| **Automation Engine** | [n8n](https://n8n.io) | Workflow orchestration |
| **Container Runtime** | Docker + docker-compose | Reproducible environment |
| **Python Script** | `insta-extractor.py` | Downloads images via Instaloader |
| **AI Model** | GPT-4o (OpenAI) | Extracts text from images |
| **Database** | Notion API | Stores structured content |
| **Entry Trigger** | Webhook (`POST /webhook/ig-ingest`) | Receives Instagram URL + optional note |

---

## 🧩 Folder Structure

```
n8n-insta-app/
├─ Dockerfile
├─ docker-compose.yml
├─ insta-extractor.py
├─ workflows/
│  └─ instagram-to-notion.json
├─ data/
│  ├─ n8n/
│  └─ insta/
└─ README.md
```

---

## 🔧 Notion Setup (Prerequisite)

Before running this workflow, you must already have a **Notion database** ready to receive entries.

### 1. Create your Notion database

Create a new Notion database (table view is fine) and include at least the following properties:

| Property Name | Type | Purpose |
|----------------|------|----------|
| **Title** | Title | The post title or summary |
| **Summary** | Text | AI-generated summary of the post |
| **Takeaways** | Text | Key bullet points extracted by GPT |
| **Category** | Select / Multi-select | Optional categorization or tags |
| **URL** | URL | The original Instagram post URL |
| **Note** | Text | Your optional user-supplied note |

You can rename these later — just make sure the property names in your workflow’s **Notion “Create Page” node** match your database.

### 2. Share the database with your Notion integration

- In Notion, click **Share → Invite → [Your Integration Name]**
- Select your integration and click **Invite**
- Copy your **Database ID** from the database URL  
  (It’s the 32-character string after `notion.so/` and before the `?`)

Example:
```
https://www.notion.so/My-Knowledge-Vault-2b6a604fb9cf8079a5a1cde4669f2e3e
```
➡️ Database ID: `2b6a604fb9cf8079a5a1cde4669f2e3e`

### 3. Paste your Database ID into the n8n workflow

In the **“Create a database page”** node, replace the placeholder `databaseId` with your actual one.

---

## ⚙️ Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/n8n-insta-app.git
cd n8n-insta-app
```

### 2. Build and start the container

```bash
docker compose up -d --build
```

Then open the n8n UI at:

👉 [http://localhost:5678](http://localhost:5678)

---

## 🧭 Configure n8n

### 1. Import the workflow

In the n8n UI:

- Go to **Workflows → Import**
- Select `workflows/instagram-to-notion.json`
- Save and activate

### 2. Add your credentials

| Credential | Purpose |
|-------------|----------|
| **Notion API** | Connects to your Notion workspace |
| **OpenAI API** | Uses GPT-4o for OCR and summarization |

You’ll need:
- A Notion integration token  
- Your target Notion database ID  
- Your OpenAI API key  

### 3. Update database property mappings

In the final **“Create a database page”** node:
- Replace `databaseId` with your Notion database ID.
- Map the fields (e.g., `Title`, `Summary`, `Category`, `Takeaways`, `URL`) to match your Notion schema.

---

## 🚀 Run the workflow

### Trigger via curl

```bash
curl -X POST http://localhost:5678/webhook/ig-ingest   -H "Content-Type: application/json"   -d '{"url":"https://www.instagram.com/p/DRPk8qPChUC/", "note":"Antimatter"}'
```

Expected response:
```json
{"message": "Workflow was started"}
```

Within a few seconds, a new entry appears in your Notion database containing:
- Post title and extracted text  
- AI-generated summary  
- Key takeaways  
- The original Instagram URL  

---

## 🧰 Docker Breakdown

- **Python + Instaloader layer:** built directly into the image.  
  Script path inside container: `/scripts/insta-extractor.py`  
- **Volumes:**  
  - `./data/n8n → /home/node/.n8n` (persistent n8n config)  
  - `./data/insta → /data` (temporary downloaded images)  
- **Web access:**  
  Exposed at `http://localhost:5678` (mapped to container port `5678`).  

---

## 🔒 Environment Variables

All editable inside `docker-compose.yml`:

| Variable | Description |
|-----------|-------------|
| `N8N_HOST` | Host binding (usually `0.0.0.0`) |
| `N8N_PORT` | Port (default `5678`) |
| `N8N_PROTOCOL` | `http` or `https` |
| `N8N_EDITOR_BASE_URL` | Base URL for editor |
| `N8N_ENCRYPTION_KEY` | Any long random string |
| `DATA_FOLDER` | Where downloaded Instagram content lives (`/data`) |

---

## 💡 Example Flow Overview

**Webhook** → **Normalize Inputs** → **Extract Instagram ID** → **Execute Command (Python)** →  
**Parse JSON** → **Read Files from Disk** → **Analyze Image (OpenAI)** →  
**Combine Text** → **Summarize and Structure Text (OpenAI)** → **Create Notion Page** → **Cleanup Files**

---

## 🧹 Cleanup and Data Management

After each run:

- Images are written under `/data/insta_<shortcode>`
- Once processed, the cleanup command deletes that folder
- Only the summarized text remains in Notion

To persist logs or debug runs, you can comment out the cleanup node in n8n.

---

## 🌍 Sharing and Collaboration

Anyone can replicate your setup by:

1. Cloning the repo  
2. Running `docker compose up -d`  
3. Importing the provided workflow  
4. Configuring their own credentials  

No local Python setup required — the container includes everything.

---

## 🧠 Future Enhancements

- ✅ Auto-detect videos and extract transcripts  
- ✅ Add metadata (likes, caption, hashtags) to Notion  
- 🕒 Schedule daily sync jobs  
- ☁️ Deploy to Fly.io / Render for 24/7 uptime  
- 🔐 Add HTTPS via Cloudflare Tunnel or Caddy  

---

## 🪄 Credits

Created by [**Marc Jabbour**](https://github.com/marcjabbour)  
Built with ❤️ using:
- [n8n](https://n8n.io)
- [Docker](https://www.docker.com/)
- [Instaloader](https://instaloader.github.io/)
- [OpenAI GPT-4o](https://platform.openai.com/)
- [Notion API](https://developers.notion.com/)
