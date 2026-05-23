import os
import base64
from flask import Flask, request, jsonify, render_template_string
from google import genai
import google.genai.types as gentypes

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

# Model registry — shown in the UI dropdown
MODELS = [
    {
        "id": "gemini-2.0-flash-exp-image-generation",
        "label": "Gemini 2.0 Flash Experimental",
        "free": True,
        "note": "Free ✅ — shutting down June 1 2026",
        "config_style": "exp",   # uses responseModalities list
    },
    {
        "id": "gemini-2.5-flash-image",
        "label": "Gemini 2.5 Flash Image (Nano Banana)",
        "free": False,
        "note": "Paid 💳 — best quality, $0.039/image",
        "config_style": "flash",
    },
    {
        "id": "gemini-3.1-flash-image-preview",
        "label": "Gemini 3.1 Flash Image (Nano Banana 2)",
        "free": False,
        "note": "Paid 💳 — latest model, $0.067/image",
        "config_style": "flash",
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
    .card{background:rgba(255,255,255,.07);backdrop-filter:blur(12px);border:1px solid rgba(255,255,255,.15);border-radius:20px;padding:36px;width:100%;max-width:720px;color:#fff}
    h1{font-size:1.9rem;text-align:center;margin-bottom:6px}
    .sub{color:#aaa;text-align:center;margin-bottom:28px;font-size:.9rem}
    label{display:block;font-size:.85rem;color:#ccc;margin-bottom:6px;margin-top:16px}
    select,textarea{width:100%;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.2);border-radius:12px;color:#fff;padding:14px;font-size:.95rem;outline:none}
    select{cursor:pointer}
    select option{background:#1e1b4b;color:#fff}
    textarea{resize:vertical;min-height:110px}
    textarea::placeholder,select::placeholder{color:#888}
    textarea:focus,select:focus{border-color:#a78bfa}
    .badge{display:inline-block;font-size:.75rem;padding:3px 10px;border-radius:20px;margin-left:8px;vertical-align:middle}
    .free{background:rgba(52,211,153,.15);color:#34d399;border:1px solid rgba(52,211,153,.3)}
    .paid{background:rgba(251,191,36,.12);color:#fbbf24;border:1px solid rgba(251,191,36,.3)}
    #modelNote{font-size:.8rem;color:#9ca3af;margin-top:8px;padding:8px 12px;background:rgba(255,255,255,.05);border-radius:8px}
    button{margin-top:20px;width:100%;padding:14px;background:linear-gradient(90deg,#7c3aed,#a78bfa);border:none;border-radius:12px;color:#fff;font-size:1.05rem;font-weight:600;cursor:pointer;transition:opacity .2s}
    button:hover{opacity:.88}
    button:disabled{opacity:.45;cursor:not-allowed}
    #status{margin-top:12px;text-align:center;color:#a78bfa;min-height:20px;font-size:.9rem}
    #result{margin-top:22px;text-align:center}
    #result img{max-width:100%;border-radius:14px;border:2px solid rgba(167,139,250,.4);box-shadow:0 8px 32px rgba(124,58,237,.3)}
    .dl{display:inline-block;margin-top:12px;padding:10px 26px;background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.2);border-radius:10px;color:#fff;text-decoration:none;font-size:.9rem;transition:background .2s}
    .dl:hover{background:rgba(255,255,255,.2)}
    .divider{border:none;border-top:1px solid rgba(255,255,255,.1);margin:24px 0}
    .models-info{font-size:.78rem;color:#6b7280;text-align:center}
  </style>
</head>
<body>
<div class="card">
  <h1>✨ Gemini Image Generator</h1>
  <p class="sub">Select a model, type a prompt, generate!</p>

  <label>Model</label>
  <select id="modelSelect" onchange="updateNote()">
    {% for m in models %}
    <option value="{{ m.id }}" data-note="{{ m.note }}" data-free="{{ m.free|lower }}">
      {{ m.label }}  —  {{ "FREE" if m.free else "PAID" }}
    </option>
    {% endfor %}
  </select>
  <div id="modelNote">Loading...</div>

  <label>Prompt</label>
  <textarea id="prompt" placeholder="e.g. A futuristic city at night, neon lights, cyberpunk, cinematic wide shot, 4k"></textarea>

  <button id="genBtn" onclick="generate()">🎨 Generate Image</button>
  <div id="status"></div>
  <div id="result"></div>

  <hr class="divider">
  <div class="models-info">
    Free models use your Gemini API key quota &nbsp;•&nbsp; Paid models require billing enabled in Google AI Studio
  </div>
</div>

<script>
const models = {{ models_json|safe }};

function updateNote() {
  const sel = document.getElementById('modelSelect');
  const opt = sel.options[sel.selectedIndex];
  const note = opt.dataset.note;
  const isFree = opt.dataset.free === 'true';
  const noteEl = document.getElementById('modelNote');
  noteEl.innerHTML = `<span class="badge ${isFree ? 'free' : 'paid'}">${isFree ? '✅ Free Tier' : '💳 Paid'}</span> ${note}`;
}

async function generate() {
  const prompt = document.getElementById('prompt').value.trim();
  const model = document.getElementById('modelSelect').value;
  if (!prompt) { alert('Please enter a prompt!'); return; }

  const btn = document.getElementById('genBtn');
  const status = document.getElementById('status');
  const result = document.getElementById('result');

  btn.disabled = true;
  status.textContent = '⏳ Generating... this can take 10–30 seconds';
  result.innerHTML = '';

  try {
    const res = await fetch('/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt, model })
    });
    const data = await res.json();
    if (data.success) {
      status.textContent = '✅ Done!';
      result.innerHTML = `
        <img src="data:image/png;base64,${data.image_b64}" alt="Generated image">
        <br>
        <a class="dl" href="data:image/png;base64,${data.image_b64}" download="gemini_image.png">⬇ Download PNG</a>`;
    } else {
      status.textContent = '❌ ' + (data.error || 'Unknown error');
    }
  } catch (e) {
    status.textContent = '❌ Request failed: ' + e.message;
  } finally {
    btn.disabled = false;
  }
}

document.getElementById('prompt').addEventListener('keydown', e => {
  if (e.ctrlKey && e.key === 'Enter') generate();
});

updateNote();
</script>
</body>
</html>
"""

import json

@app.route("/")
def index():
    return render_template_string(
        HTML_PAGE,
        models=MODELS,
        models_json=json.dumps(MODELS)
    )


@app.route("/models")
def list_models():
    return jsonify(MODELS)


@app.route("/generate", methods=["POST"])
def generate():
    if not GEMINI_API_KEY:
        return jsonify({"success": False, "error": "GEMINI_API_KEY not set in environment variables."}), 500

    body = request.get_json()
    if not body or not body.get("prompt"):
        return jsonify({"success": False, "error": "Missing 'prompt'."}), 400

    prompt = body["prompt"].strip()[:1000]
    model_id = body.get("model", "gemini-2.0-flash-exp-image-generation")

    # Validate model ID is in our list
    valid_ids = [m["id"] for m in MODELS]
    if model_id not in valid_ids:
        return jsonify({"success": False, "error": f"Unknown model: {model_id}"}), 400

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)

        # gemini-2.0-flash-exp uses responseModalities; others use response_modalities
        model_meta = next(m for m in MODELS if m["id"] == model_id)

        if model_meta["config_style"] == "exp":
            config = gentypes.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"]
            )
        else:
            config = gentypes.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"]
            )

        response = client.models.generate_content(
            model=model_id,
            contents=[prompt],
            config=config,
        )

        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                image_b64 = base64.b64encode(part.inline_data.data).decode("utf-8")
                return jsonify({"success": True, "image_b64": image_b64, "model": model_id})

        # No image found — extract any text reason
        text_parts = []
        for part in response.candidates[0].content.parts:
            if hasattr(part, "text") and part.text:
                text_parts.append(part.text)
        reason = " ".join(text_parts) if text_parts else "Model returned no image. Try a different prompt or model."
        return jsonify({"success": False, "error": reason}), 500

    except Exception as e:
        err = str(e)
        # Give friendly hints for common errors
        if "RESOURCE_EXHAUSTED" in err or "quota" in err.lower():
            err = "Quota exceeded for this model. Try switching to a different model or wait and retry."
        elif "billing" in err.lower() or "payment" in err.lower():
            err = "This model requires billing enabled. Switch to a Free model from the dropdown."
        return jsonify({"success": False, "error": err}), 500


@app.route("/health")
def health():
    return jsonify({"status": "ok", "api_key_set": bool(GEMINI_API_KEY)})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
