import os
from flask import Flask, request, jsonify
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

ANAM_API_KEY = os.getenv("ANAM_API_KEY")

@app.route("/api/session_token", methods=["POST"])
def create_session_token():
    """
    Creates a temporary Anam session token using your server-side API key.
    This token is sent to the client and *used there* to initialize the avatar session.
    """
    try:
        # You can send persona config with text, avatar ID, etc,
        # here we use a stock persona for simplicity.
        persona_config = {
            "name": "Cara",
            "avatarId": "30fa96d0-26c4-4e55-94a0-517025942e18",  # stock avatar
            "voiceId": "6bfbe25a-979d-40f3-a92b-5394170af54b",   # stock voice
            # You can add llmId and systemPrompt if desired
        }

        response = requests.post(
            "https://api.anam.ai/v1/auth/session-token",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {ANAM_API_KEY}",
            },
            json={"personaConfig": persona_config},
        )

        data = response.json()
        return jsonify(data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/send_text", methods=["POST"])
def send_text():
    """
    Sends a text command to the avatar session.
    The client-side JS should keep the anamClient instance alive
    and can receive talk commands via WebSocket or similar,
    but for now this just demonstrates a REST endpoint.
    """
    try:
        session_token = request.json.get("sessionToken")
        text_to_say = request.json.get("text")

        if not session_token or not text_to_say:
            return jsonify({"error": "Missing sessionToken or text"}), 400

        # Forward text to the avatar client via Anam API
        # (In a real app you'd use WebRTC / anam JS SDK to call talk())
        # Here is a placeholder showing the idea:
        # NOTE: This endpoint doesn’t actually make the avatar speak via REST alone;
        # you need the JS anamClient.talk(text) method in the frontend.
        return jsonify({"status": "ok", "message": "send text handled"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(port=5000)
