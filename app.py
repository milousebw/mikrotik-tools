from flask import Flask, request, jsonify, render_template, send_from_directory, abort
import requests
import paramiko
import os
import uuid
from gtts import gTTS
from pydub import AudioSegment

app = Flask(__name__)

# IPs autorisées
AUTHORIZED_IPS = {"78.155.148.66", "192.168.0.203"}

@app.before_request
def limit_remote_addr():
    ip = request.remote_addr
    if ip not in AUTHORIZED_IPS:
        abort(403)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/mac', methods=['GET'])
def lookup_mac():
    mac = request.args.get('address')
    if not mac:
        return jsonify({'error': 'Adresse MAC manquante'}), 400
    url = f"https://api.macvendors.com/{mac}"
    response = requests.get(url)
    if response.status_code == 200:
        return jsonify({'vendor': response.text})
    else:
        return jsonify({'error': 'Fournisseur non trouvé'}), 404

@app.route('/speedtest', methods=['GET'])
def speedtest():
    target_ip = request.args.get('ip')
    target_user = request.args.get('user')
    target_pass = request.args.get('pass')
    if not target_ip or not target_user or not target_pass:
        return "Paramètres requis : ip, user, pass", 400

    local_ip = "192.168.0.252"
    local_user = "admin"
    local_pass = "FG95876"

    command = f"/tool bandwidth-test address={target_ip} user={target_user} password={target_pass} direction=both duration=30s"

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(local_ip, username=local_user, password=local_pass, look_for_keys=False, allow_agent=False)
        stdin, stdout, stderr = client.exec_command(command)
        output = stdout.read().decode()
        error = stderr.read().decode()
        client.close()
        if error:
            return f"[STDERR] {error}", 500
        return output
    except Exception as e:
        return f"[EXCEPTION] {str(e)}", 500

@app.route('/tts', methods=['POST'])
def tts():
    text = request.form.get('text')
    voice = request.form.get('voice', 'fr')
    if not text:
        return jsonify({'error': 'Texte manquant'}), 400

    filename = f"{uuid.uuid4()}.mp3"
    filepath = os.path.join("static", filename)

    try:
        tts = gTTS(text, lang=voice)
        tts.save(filepath)

        # Conversion en 8 kHz mono WAV (si besoin pour compatibilité)
        wav_filename = filename.replace('.mp3', '.wav')
        wav_path = os.path.join("static", wav_filename)
        audio = AudioSegment.from_file(filepath)
        audio.set_frame_rate(8000).set_channels(1).export(wav_path, format="wav")

        return jsonify({"file": filename, "wav": wav_filename})
    except Exception as e:
        return jsonify({'error': f"Erreur TTS : {str(e)}"}), 500

@app.route('/static/<path:filename>')
def serve_file(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
