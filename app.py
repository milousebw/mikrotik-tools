from flask import Flask, request, jsonify, render_template, abort
import requests
import paramiko
import os

app = Flask(__name__)

AUTHORIZED_IPS = ["78.155.148.66", "192.168.0.203"]

@app.before_request
def restrict_by_ip():
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    print(f"[Sécurité] IP reçue : {client_ip}")
    if client_ip not in AUTHORIZED_IPS:
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
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return jsonify({'vendor': response.text})
        else:
            return jsonify({'error': 'Fournisseur non trouvé'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/speedtest', methods=['GET'])
def speedtest():
    target_ip = request.args.get('ip')
    target_user = request.args.get('user')
    target_pass = request.args.get('pass')

    if not target_ip or not target_user or not target_pass:
        return "Paramètres requis : ip, user, pass", 400

    local_chrouter_ip = "192.168.0.252"
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
            return f"[ERREUR MikroTik] {error}", 500
        return output
    except Exception as e:
        return f"[EXCEPTION SSH] {str(e)}", 500

@app.route('/tts', methods=['POST'])
def tts():
    data = request.json
    text = data.get('text')
    voice = data.get('voice', 'nova')

    if not text:
        return jsonify({'error': 'Texte requis'}), 400

    try:
        api_key = os.environ.get('OPENAI_API_KEY')
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "tts-1",
            "input": text,
            "voice": voice
        }

        response = requests.post(
            "https://api.openai.com/v1/audio/speech",
            headers=headers,
            json=payload
        )

        if response.status_code == 200:
            return response.content, 200, {
                "Content-Type": "audio/mpeg"
            }
        else:
            return jsonify({'error': response.json()}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)