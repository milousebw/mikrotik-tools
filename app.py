from flask import Flask, request, jsonify, render_template, send_from_directory
from gtts import gTTS
from pydub import AudioSegment
import os
import uuid

app = Flask(__name__)
AUTHORIZED_IPS = ["78.155.148.66", "192.168.0.203"]

@app.before_request
def limit_remote_addr():
    if AUTHORIZED_IPS and request.remote_addr not in AUTHORIZED_IPS:
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

        mp3_filename = f"{uuid.uuid4()}.mp3"
        mp3_path = os.path.join("static", mp3_filename)

        tts = gTTS(text=text, lang=lang)
        tts.save(mp3_path)

        # Conversion WAV 8kHz mono
        wav_filename = mp3_filename.replace(".mp3", ".wav")
        wav_path = os.path.join("static", wav_filename)
        audio = AudioSegment.from_mp3(mp3_path)
        audio.set_frame_rate(8000).set_channels(1).export(wav_path, format="wav")

        return jsonify({
            'audio': f"/static/{mp3_filename}",
            'wav': f"/static/{wav_filename}"
        })
    except Exception as e:
        return jsonify({'error': f"Erreur TTS : {str(e)}"}), 500

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    os.makedirs("static", exist_ok=True)
    app.run(host='0.0.0.0', port=8080)
