
from flask import Flask, request, jsonify, render_template, send_file
import os
from gtts import gTTS
from uuid import uuid4
from pydub import AudioSegment

app = Flask(__name__)

AUTHORIZED_IP = "78.155.148.66"

@app.before_request
def limit_remote_addr():
    if request.remote_addr != AUTHORIZED_IP:
        return "403 Forbidden", 403

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/tts', methods=['POST'])
def tts():
    try:
        text = request.form['text']
        voice = request.form['voice']  # Non utilisé pour gTTS, mais conservé

        filename = f"{uuid4()}.mp3"
        filepath = os.path.join("static", filename)

        tts = gTTS(text=text, lang="fr")
        tts.save(filepath)

        # Conversion vers format WAV compatible 3CX
        wav_path = filepath.replace(".mp3", ".wav")
        sound = AudioSegment.from_mp3(filepath)
        sound.export(wav_path, format="wav", parameters=["-ar", "8000", "-ac", "1"])

        return jsonify({
            "status": "ok",
            "play_url": f"/{filepath}",
            "download_url": f"/{wav_path}"
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/<path:filename>')
def download(filename):
    return send_file(filename, as_attachment=True)

if __name__ == '__main__':
    if not os.path.exists("static"):
        os.makedirs("static")
    app.run(host='0.0.0.0', port=8080)
