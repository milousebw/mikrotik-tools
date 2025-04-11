
from flask import Flask, request, jsonify, render_template
from gtts import gTTS
import os
import uuid

app = Flask(__name__)
AUTHORIZED_IPS = ["78.155.148.66", "192.168.0.203"]

@app.before_request
def limit_remote_addr():
    if request.remote_addr not in AUTHORIZED_IPS:
        return "403 Forbidden", 403

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/tts', methods=['POST'])
def tts():
    try:
        text = request.json.get('text')
        lang = request.json.get('lang', 'fr')
        if not text:
            return jsonify({'error': 'Texte manquant'}), 400
        filename = f"{uuid.uuid4()}.mp3"
        path = os.path.join("static", filename)
        tts = gTTS(text=text, lang=lang)
        tts.save(path)
        return jsonify({'audio': f"/static/{filename}"})
    except Exception as e:
        return jsonify({'error': f"Erreur TTS : {str(e)}"}), 500

if __name__ == '__main__':
    os.makedirs("static", exist_ok=True)
    app.run(host='0.0.0.0', port=8080)
