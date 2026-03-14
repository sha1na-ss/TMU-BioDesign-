from flask import Flask, jsonify, send_from_directory, request
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__, static_folder='../dashboard', static_url_path='')

# ── Serve dashboard pages ──────────────────────────────────────────
@app.route('/')
def index():
    return send_from_directory('../dashboard', 'login.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('../dashboard', filename)

# ── Firebase config endpoint ───────────────────────────────────────
@app.route('/firebase-config')
def firebase_config():
    return jsonify({
        "apiKey":            os.getenv("FIREBASE_API_KEY"),
        "authDomain":        os.getenv("FIREBASE_AUTH_DOMAIN"),
        "projectId":         os.getenv("FIREBASE_PROJECT_ID"),
        "storageBucket":     os.getenv("FIREBASE_STORAGE_BUCKET"),
        "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
        "appId":             os.getenv("FIREBASE_APP_ID"),
    })

if __name__ == '__main__':
    app.run(debug=True)
