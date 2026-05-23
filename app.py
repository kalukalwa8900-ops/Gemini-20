import os
from io import BytesIO
import base64
from flask import Flask, request, jsonify, render_template_string, send_file
from google import genai

app = Flask(__name__)

# Load API key from environment variable (supports both naming conventions)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gemini Image Generator</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: rgba(255,255,255,0.07);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255,255,255,0.15);
            border-radius: 20px;
            padding: 40px;
            width: 100%;
            max-width: 700px;
            color: white;
        }
        h1 { font-size: 2rem; margin-bottom: 8px; text-align: center; }
        p.sub { color: #aaa; text-align: center; margin-bottom: 30px; font-size: 0.95rem; }
        textarea {
            width: 100%;
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 12px;
            color: white;
            padding: 16px;
            font-size: 1rem;
            resize: vertical;
            min-height: 120px;
            outline: none;
        }
        textarea::placeholder { color: #888; }
        textarea:focus { border-color: #a78bfa; }
        button {
            margin-top: 16px;
            width: 100%;
            padding: 14px;
            background: linear-gradient(90deg, #7c3aed, #a78bfa);
            border: none;
            border-radius: 12px;
            color: white;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: opacity 0.2s;
        }
        button:hover { opacity: 0.88; }
        button:disabled { opacity: 0.5; cursor: not-allowed; }
        #status { margin-top: 14px; text-align: center; color: #a78bfa; min-height: 22px; font-size: 0.95rem; }
        #result { margin-top: 24px; text-align: center; }
        #result img {
            max-width: 100%;
            border-radius: 14px;
            border: 2px solid rgba(167,139,250,0.4);
            box-shadow: 0 8px 32px rgba(124,58,237,0.3);
        }
        .download-btn {
            display: inline-block;
            margin-top: 14px;
            padding: 10px 28px;
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 10px;
            color: white;
            text-decoration: none;
            font-size: 0.95rem;
            transition: background 0.2s;
        }
        .download-btn:hover { background: rgba(255,255,255,0.2); }
    </style>
</head>
<body>
<div class="container">
    <h1>✨ Gemini Image Generator</h1>
    <p class="sub">Powered by Google Gemini 2.5 Flash Image API</p>
    <textarea id="prompt" placeholder="Describe your image... e.g. A gorgeous anime cherry blossom tree under a starry sky, cinematic lighting, 4k"></textarea>
    <button id="genBtn" onclick="generate()">Generate Image</button>
    <div id="status"></div>
    <div id="result"></div>
</div>

<script>
async function generate() {
    const prompt = document.getElementById('prompt').value.trim();
    if (!prompt) { alert('Please enter a prompt!'); return; }

    const btn = document.getElementById('genBtn');
    const status = document.getElementById('status');
    const result = document.getElementById('result');

    btn.disabled = true;
    status.textContent = '⏳ Generating your image...';
    result.innerHTML = '';

    try {
        const res = await fetch('/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt })
        });
        const data = await res.json();
        if (data.success) {
            status.textContent = '✅ Image ready!';
            result.innerHTML = `
                <img src="data:image/png;base64,${data.image_b64}" alt="Generated image">
                <br>
                <a class="download-btn" href="data:image/png;base64,${data.image_b64}" download="gemini_image.png">⬇ Download PNG</a>
            `;
        } else {
            status.textContent = '❌ Error: ' + (data.error || 'Unknown error');
        }
    } catch (e) {
        status.textContent = '❌ Request failed: ' + e.message;
    } finally {
        btn.disabled = false;
    }
}

document.getElementById('prompt').addEventListener('keydown', function(e) {
    if (e.ctrlKey && e.key === 'Enter') generate();
});
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_PAGE)

@app.route("/generate", methods=["POST"])
def generate():
    if not GEMINI_API_KEY:
        return jsonify({"success": False, "error": "GEMINI_API_KEY environment variable not set."}), 500

    data = request.get_json()
    if not data or not data.get("prompt"):
        return jsonify({"success": False, "error": "Missing 'prompt' in request body."}), 400

    prompt = data["prompt"].strip()
    if len(prompt) > 1000:
        return jsonify({"success": False, "error": "Prompt too long (max 1000 chars)."}), 400

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model="gemini-3.1-flash-image-preview",
            contents=[prompt],
            config=genai.types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )

        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                image_b64 = base64.b64encode(part.inline_data.data).decode("utf-8")
                return jsonify({"success": True, "image_b64": image_b64})

        # If we got here, no image was returned — maybe a text block explains why
        text_parts = [p.text for p in response.candidates[0].content.parts if p.text]
        reason = " ".join(text_parts) if text_parts else "No image returned by the model."
        return jsonify({"success": False, "error": reason}), 500

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/health")
def health():
    return jsonify({"status": "ok", "api_key_set": bool(GEMINI_API_KEY)})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
