
from flask import Flask, request, jsonify, render_template, send_from_directory
from gtts import gTTS
import paramiko
import requests
import uuid
import os

app = Flask(__name__)

# Crée le dossier static s’il n’existe pas
os.makedirs("static", exist_ok=True)

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

    host = "192.168.0.252"
    username = "admin"
    password = "FG95876"
    command = f"/tool bandwidth-test address={target_ip} user={target_user} password={target_pass} direction=both duration=30s"

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=username, password=password, look_for_keys=False, allow_agent=False)
        stdin, stdout, stderr = client.exec_command(command)
        output = stdout.read().decode()
        error = stderr.read().decode()
        client.close()

        if error:
            return f"[ERREUR MikroTik] {error}", 500
        return output

    except Exception as e:
        return f"[EXCEPTION SSH] {str(e)}", 500

@app.route('/tts', methods=['POST'])
def tts():
    data = request.get_json()
    text = data.get('text')
    lang = data.get('lang', 'fr')
    if not text:
        return jsonify({'error': 'Texte manquant'}), 400
    try:
        filename = f"{uuid.uuid4()}.mp3"
        filepath = os.path.join("static", filename)
        tts = gTTS(text, lang=lang)
        tts.save(filepath)
        return jsonify({'url': f"/static/{filename}"})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
