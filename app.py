from flask import Flask, request, jsonify, render_template, send_from_directory
from gtts import gTTS
from pydub import AudioSegment
import os
import uuid
import paramiko
import requests

app = Flask(__name__)
AUTHORIZED_IP = "78.155.148.66"

@app.before_request
def limit_remote_addr():
    if request.remote_addr != AUTHORIZED_IP:
        return "403 Forbidden", 403

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
    text = request.json.get('text')
    lang = request.json.get('lang', 'fr')
    if not text:
        return jsonify({'error': 'Texte manquant'}), 400
    filename = f"{uuid.uuid4()}"
    mp3_path = f"static/{filename}.mp3"
    wav_path = f"static/{filename}_3cx.wav"
    try:
        tts = gTTS(text, lang=lang)
        tts.save(mp3_path)
        return jsonify({'mp3': mp3_path, 'wav': wav_path})
    except Exception as e:
        return jsonify({'error': f'Erreur TTS: {e}'}), 500

@app.route('/convert_wav', methods=['POST'])
def convert_wav():
    mp3_path = request.json.get('mp3')
    if not mp3_path or not os.path.exists(mp3_path):
        return jsonify({'error': 'Fichier MP3 introuvable'}), 400
    wav_path = mp3_path.replace('.mp3', '_3cx.wav')
    try:
        sound = AudioSegment.from_mp3(mp3_path)
        sound = sound.set_frame_rate(8000).set_channels(1).set_sample_width(2)
        sound.export(wav_path, format="wav")
        return jsonify({'wav': wav_path})
    except Exception as e:
        return jsonify({'error': f'Erreur conversion: {e}'}), 500

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)