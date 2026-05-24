from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import os

API_KEY = os.environ.get("OPENROUTER_API_KEY")
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL   = "anthropic/claude-haiku-4-5"

app = Flask(__name__)
CORS(app)

SYSTEM_PROMPT = """You are Nova, a warm, compassionate AI companion designed specifically for
senior citizens who may be experiencing loneliness.
Your personality:
- Gentle, patient, cheerful, and caring — like a trusted friend.
- Never clinical or cold; always encouraging and curious about their life.
- Use their name if you know it; reference personal details naturally.
- Keep responses conversational — 2-4 sentences typically.
- Ask a follow-up question to keep the conversation flowing.
- Suggest activities, share a short poem, or offer trivia when appropriate.
- Use small warm emojis (💜 🌸 ☀️ 🌷) sparingly.
- You are NOT a medical advisor; suggest speaking to a doctor for health concerns."""

@app.route("/")
def home():
    return send_from_directory(".", "index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True)
    if not data or "messages" not in data:
        return jsonify({"error": "Missing 'messages' in request body."}), 400

    messages  = data["messages"]
    profile   = data.get("profile", {})
    memories  = data.get("memories", [])

    profile_ctx = ""
    for key in ["name", "age", "city", "hobbies", "family"]:
        if profile.get(key):
            profile_ctx += f"{key.capitalize()}: {profile[key]}. "

    mem_ctx = ""
    if memories:
        mem_snippets = [
            f"[{m.get('tag','')}] {m.get('title','')}: {m.get('body','')}"
            for m in memories[-8:]
        ]
        mem_ctx = "Known memories: " + " | ".join(mem_snippets)

    full_system_content = f"{SYSTEM_PROMPT}\n\n{profile_ctx}\n{mem_ctx}".strip()

    payload = {
        "model": MODEL,
        "messages": [{"role": "system", "content": full_system_content}] + messages
    }
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        reply  = result["choices"][0]["message"]["content"]
        return jsonify({"reply": reply})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Failed to connect to Nova's brain."}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
