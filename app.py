from flask import Flask, request, jsonify, render_template, send_file
import requests
import paramiko
import tempfile
import os
import openai

app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")  # Assure-toi que ta clé est dans les variables d'env

# Route principale (interface HTML)
@app.route('/')
def index():
    return render_template('index.html')


# 1. Recherche MAC
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


# 2. Test de débit MikroTik
@app.route('/speedtest', methods=['GET'])
def speedtest():
    target_ip = request.args.get('ip')
    target_user = request.args.get('user')
    target_pass = request.args.get('pass')

    if not target_ip or not target_user or not target_pass:
        return "Paramètres requis : ip, user, pass", 400

    local_chrouter_ip = "192.168.0.252"  # À adapter selon ta VM Mikrotik CHR
    local_user = "admin"
    local_pass = "FG95876"

    command = f"/tool bandwidth-test address={target_ip} user={target_user} password={target_pass} direction=both duration=30s"

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(local_chrouter_ip, username=local_user, password=local_pass, look_for_keys=False, allow_agent=False)

        stdin, stdout, stderr = client.exec_command(command)
        output = stdout.read().decode()
        error = stderr.read().decode()
        client.close()

        if error:
            return f"[STDERR] {error}", 500
        return output

    except Exception as e:
        return f"[EXCEPTION] {str(e)}", 500


# 3. Synthèse vocale (TTS)
@app.route('/tts', methods=['POST'])
def tts():
    data = request.get_json()
    text = data.get("text", "")
    voice = data.get("voice", "nova")

    if not text:
        return "Texte manquant", 400

    try:
        response = openai.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text
        )

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            tmp.write(response.content)
            tmp.seek(0)
            return send_file(tmp.name, mimetype="audio/mpeg")

    except Exception as e:
        return f"[EXCEPTION TTS] {str(e)}", 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
