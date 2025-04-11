from flask import Flask, request, jsonify, render_template
import paramiko
from gtts import gTTS
import os
import uuid

app = Flask(__name__)

AUTHORIZED_IP = None  # Désactivé pour accès libre

@app.before_request
def limit_remote_addr():
    if AUTHORIZED_IP:
        if request.remote_addr != AUTHORIZED_IP:
            return "Accès refusé", 403

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/mac', methods=['GET'])
def lookup_mac():
    mac = request.args.get('address')
    if not mac:
        return jsonify({'error': 'Adresse MAC manquante'}), 400
    try:
        import requests
        url = f"https://api.macvendors.com/{mac}"
        response = requests.get(url)
        if response.status_code == 200:
            return jsonify({'vendor': response.text})
        else:
            return jsonify({'error': 'Fournisseur non trouvé'}), 404
    except Exception as e:
        return jsonify({'error': f'Erreur de requête: {str(e)}'}), 500

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
        client.connect(local_ip, username=local_user, password=local_pass, look_for_keys=False)
        stdin, stdout, stderr = client.exec_command(command)
        output = stdout.read().decode()
        client.close()
        return output
    except Exception as e:
        return f"[EXCEPTION] {str(e)}", 500

@app.route('/tts', methods=['POST'])
def tts():
    data = request.json
    text = data.get("text", "")
    lang = data.get("lang", "fr")
    if not text:
        return jsonify({'error': 'Texte manquant'}), 400
    try:
        filename = f"static/{uuid.uuid4()}.mp3"
        tts = gTTS(text=text, lang=lang)
        tts.save(filename)
        return jsonify({"url": f"/{filename}"})
    except Exception as e:
        return jsonify({'error': f'Erreur TTS: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080)