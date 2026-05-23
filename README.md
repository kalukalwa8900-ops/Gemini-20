# 🎨 Gemini Image Generator — Free Deployment on Railway

A simple Flask web app that uses Google's **Gemini 3.1 Flash Image** model (`gemini-3.1-flash-image-preview`) to generate images from text prompts. Deploy for free on Railway.

---

## 📁 Files Overview

| File | Purpose |
|------|---------|
| `app.py` | Flask app — web UI + `/generate` API endpoint |
| `requirements.txt` | Python dependencies |
| `Procfile` | Tells Railway how to start the app |
| `railway.toml` | Railway-specific config (health check, restart policy) |
| `runtime.txt` | Specifies Python 3.11 |

---

## 🚀 Deploy to Railway (Step-by-Step)

### 1. Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git push -u origin main
```

### 2. Create Railway Project

1. Go to [railway.app](https://railway.app) and sign in with GitHub
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Select your repository
4. Railway will auto-detect Python and start building

### 3. Add Your Gemini API Key

1. In your Railway project dashboard, click on your service
2. Go to the **"Variables"** tab
3. Click **"New Variable"** and add:
   - **Key:** `GEMINI_API_KEY`  *(or `GOOGLE_API_KEY` — both work)*
   - **Value:** your actual Gemini API key (from [aistudio.google.com](https://aistudio.google.com))
4. Railway will automatically redeploy with the key set

### 4. Get Your Public URL

- In Railway, go to **Settings → Networking → Generate Domain**
- Your app will be live at something like: `https://your-app.up.railway.app`

---

## 🔑 Getting a Free Gemini API Key

1. Visit [aistudio.google.com](https://aistudio.google.com)
2. Sign in with your Google account
3. Click **"Get API key"** → **"Create API key"**
4. Copy it and paste into Railway as shown above

> Free tier: **250+ free image generations per day** (quota varies by account)

---

## 📡 API Usage (for developers)

**POST** `/generate`

```json
{
  "prompt": "A futuristic city at night, neon lights, cyberpunk style, 4k"
}
```

**Response:**
```json
{
  "success": true,
  "image_b64": "<base64 encoded PNG>"
}
```

**Health check:** `GET /health`

---

## 💡 Prompt Tips for Best Results

Always include these 3 things in your prompt:
- **Style:** `Anime`, `Photorealistic`, `Oil painting`, `Vector art`
- **Lighting:** `Cinematic`, `Golden hour`, `Neon`, `Volumetric`
- **Framing:** `Wide shot`, `Close-up`, `Aerial view`, `Portrait`

Example: *"A photorealistic golden hour mountain landscape, dramatic clouds, wide shot, 4k, award-winning photography"*
