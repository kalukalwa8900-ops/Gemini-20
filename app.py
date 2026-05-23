import os
import base64
import json
from flask import Flask, request, jsonify, render_template_string
from google import genai
from google.genai import types

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

MODELS = [
    {
        "id": "gemini-2.5-flash-image",
        "label": "Gemini 2.5 Flash Image — Nano Banana",
        "free": True,
        "quota": "500 images/day · 10/min",
        "note": "Fast, reliable, high-volume. Best starting point.",
    },
    {
        "id": "gemini-3.1-flash-image-preview",
        "label": "Gemini 3.1 Flash Image — Nano Banana 2",
        "free": True,
        "quota": "500 images/day",
        "note": "Newer engine. Better text-in-image & character consistency.",
    },
]

HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Gemini Image Generator</title>
  <style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{font-family:'Segoe UI',sans-serif;background:linear-gradient(135deg,#0f0c29,#302b63,#24243e);min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
    .card{background:rgba(255,255,255,.07);backdrop-filter:blur(14px);border:1px solid rgba(255,255,255,.15);border-radius:22px;padding:38px;width:100%;max-width:740px;color:#fff}
    h1{font-size:1.9rem;text-align:center;margin-bottom:6px}
    .sub{color:#aaa;text-align:center;margin-bottom:28px;font-size:.9rem}
    label{display:block;font-size:.82rem;color:#ccc;margin-bottom:6px;margin-top:18px;letter-spacing:.03em;text-transform:uppercase}
    /* Model cards */
    .model-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:4px}
    .model-card{border:2px solid rgba(255,255,255,.12);border-radius:14px;padding:14px 16px;cursor:pointer;transition:all .2s;background:rgba(255,255,255,.04)}
    .model-card:hover{border-color:#a78bfa;background:rgba(167,139,250,.08)}
    .model-card.selected{border-color:#7c3aed;background:rgba(124,58,237,.18)}
    .model-card .name{font-size:.9rem;font-weight:600;margin-bottom:4px}
    .model-card .quota{font-size:.75rem;color:#34d399;margin-bottom:4px}
    .model-card .desc{font-size:.73rem;color:#9ca3af;line-height:1.4}
    .free-badge{display:inline-block;background:rgba(52,211,153,.15);color:#34d399;border:1px solid rgba(52,211,153,.35);font-size:.68rem;padding:2px 8px;border-radius:20px;margin-bottom:6px}
    textarea{width:100%;background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.18);border-radius:12px;color:#fff;padding:14px;font-size:.95rem;resize:vertical;min-height:110px;outline:none;margin-top:4px}
    textarea::placeholder{color:#666}
    textarea:focus{border-color:#a78bfa}
    button{margin-top:20px;width:100%;padding:14px;background:linear-gradient(90deg,#7c3aed,#a78bfa);border:none;border-radius:12px;color:#fff;font-size:1.05rem;font-weight:600;cursor:pointer;transition:opacity .2s}
    button:hover{opacity:.88}
    button:disabled{opacity:.4;cursor:not-allowed}
    #status{margin-top:12px;text-align:center;color:#a78bfa;min-height:20px;font-size:.9rem}
    #result{margin-top:24px;text-align:center}
    #result img{max-width:100%;border-radius:14px;border:2px solid rgba(167,139,250,.35);box-shadow:0 8px 40px rgba(124,58,237,.3)}
    .dl{display:inline-block;margin-top:14px;padding:10px 28px;background:rgba(255,255,255,.09);border:1px solid rgba(255,255,255,.2);border-radius:10px;color:#fff;text-decoration:none;font-size:.9rem;transition:background .2s}
    .dl:hover{background:rgba(255,255,255,.18)}
    .footer{margin-top:24px;font-size:.75rem;color:#4b5563;text-align:center;border-top:1px solid rgba(255,255,255,.08);padding-top:16px}
    @media(max-width:500px){.model-grid{grid-template-columns:1fr}}
  </style>
</head>
<body>
<div class="card">
  <h1>✨ Gemini Image Generator</h1>
  <p class="sub">100% free · powered by Google AI Studio</p>

  <label>Choose Model</label>
  <div class="model-grid" id="modelGrid">
    {% for m in models %}
    <div class="model-card {% if loop.first %}selected{% endif %}"
         data-id="{{ m.id }}" onclick="selectModel(this)">
      <div class="free-badge">✅ FREE — {{ m.quota }}</div>
      <div class="name">{{ m.label }}</div>
      <div class="desc">{{ m.note }}</div>
    </div>
    {% endfor %}
  </div>

  <label>Prompt</label>
  <textarea id="prompt" placeholder="e.g. A photorealistic golden-hour mountain landscape, dramatic clouds, wide shot, 4k, award-winning photography"></textarea>

  <button id="genBtn" onclick="generate()">🎨 Generate Image &nbsp;(Ctrl+Enter)</button>
  <div id="status"></div>
  <div id="result"></div>

  <div class="footer">Both models are on the free tier · 500 images/day · no billing required</div>
</div>

<script>
let selectedModel = "{{ models[0].id }}";

function selectModel(el) {
  document.querySelectorAll('.model-card').forEach(c => c.classList.remove('selected'));
  el.classList.add('selected');
  selectedModel = el.dataset.id;
}

async function generate() {
  const prompt = document.getElementById('prompt').value.trim();
  if (!prompt) { alert('Enter a prompt first!'); return; }

  const btn = document.getElementById('genBtn');
  const status = document.getElementById('status');
  const result = document.getElementById('result');

  btn.disabled = true;
  status.textContent = '⏳ Generating — this takes 10–25 seconds…';
  result.innerHTML = '';

  try {
    const res = await fetch('/generate', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({ prompt, model: selectedModel })
    });
    const data = await res.json();
    if (data.success) {
      status.textContent = '✅ Done! Model used: ' + data.model;
      result.innerHTML = `
        <img src="data:image/png;base64,${data.image_b64}" alt="Generated image">
        <br>
        <a class="dl" href="data:image/png;base64,${data.image_b64}" download="gemini_image.png">⬇ Download PNG</a>`;
    } else {
      status.textContent = '❌ ' + (data.error || 'Unknown error');
    }
  } catch(e) {
    status.textContent = '❌ Request failed: ' + e.message;
  } finally {
    btn.disabled = false;
  }
}

document.getElementById('prompt').addEventListener('keydown', e => {
  if (e.ctrlKey && e.key === 'Enter') generate();
});
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_PAGE, models=MODELS)

@app.route("/models")
def list_models():
    return jsonify(MODELS)

@app.route("/generate", methods=["POST"])
def generate():
    if not GEMINI_API_KEY:
        return jsonify({"success": False, "error": "GEMINI_API_KEY not set in Railway environment variables."}), 500

    body = request.get_json()
    if not body or not body.get("prompt"):
        return jsonify({"success": False, "error": "Missing 'prompt'."}), 400

    prompt = body["prompt"].strip()[:1000]
    model_id = body.get("model", "gemini-2.5-flash-image")

    valid_ids = [m["id"] for m in MODELS]
    if model_id not in valid_ids:
        model_id = "gemini-2.5-flash-image"

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)

        response = client.models.generate_content(
            model=model_id,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
            ),
        )

        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                image_b64 = base64.b64encode(part.inline_data.data).decode("utf-8")
                return jsonify({"success": True, "image_b64": image_b64, "model": model_id})

        # No image — get any text explanation
        texts = [p.text for p in response.candidates[0].content.parts if getattr(p, "text", None)]
        reason = " ".join(texts) if texts else "Model returned no image. Try rephrasing your prompt."
        return jsonify({"success": False, "error": reason}), 500

    except Exception as e:
        err = str(e)
        if "RESOURCE_EXHAUSTED" in err or "quota" in err.lower():
            err = "Daily quota hit for this model. Switch to the other model or try again tomorrow."
        elif "billing" in err.lower() or "PERMISSION_DENIED" in err:
            err = "API key issue or billing required. Check your key at aistudio.google.com."
        return jsonify({"success": False, "error": err}), 500

@app.route("/health")
def health():
    return jsonify({"status": "ok", "api_key_set": bool(GEMINI_API_KEY)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
