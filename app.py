from flask import Flask, request, jsonify, render_template, send_from_directory, Response
import os
import uuid
import requests
import re
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

AUTHORIZED_IPS = ["78.155.148.66", "192.168.0.203"]

@app.before_request
def limit_remote_addr():
    real_ip = request.headers.get("X-Forwarded-For", request.remote_addr).split(",")[0].strip()
    if AUTHORIZED_IPS and real_ip not in AUTHORIZED_IPS:
        return "403 Forbidden", 403

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/mac')
def lookup_mac():
    mac = request.args.get('address')
    if not mac:
        return jsonify({'error': 'Adresse MAC manquante'}), 400

    api_key = os.getenv("MACLOOKUP_API_KEY")
    headers = {"Authorization": f"Bearer {api_key}"}
    r = requests.get(f"https://api.maclookup.app/v2/macs/{mac}", headers=headers)

    if r.status_code == 200:
        company = r.json().get("company", "Inconnu")
        return jsonify({'vendor': company})
    elif r.status_code == 404:
        return jsonify({'error': "Pas de correspondance d'adresse MAC"}), 404
    return jsonify({'error': 'Erreur API'}), 500

@app.route('/logo')
def get_logo():
    vendor = request.args.get("vendor")
    if not vendor:
        return "Vendor manquant", 400

    api_key = os.getenv("LOGODEV_API_KEY")
    headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}

    try:
        search = requests.get(f"https://api.logo.dev/search?q={vendor}", headers=headers)
        if search.ok:
            results = search.json()
            if isinstance(results, list) and results:
                domain = results[0].get("domain")
                if domain:
                    logo_url = f"https://api.logo.dev/v1/{domain}/logo.png"
                    logo_img = requests.get(logo_url, headers={
                        "Authorization": f"Bearer {api_key}",
                        "Accept": "image/png"
                    })
                    if logo_img.ok:
                        return Response(logo_img.content, content_type="image/png")
    except Exception as e:
        print("Erreur logo.dev :", e)

    fallback_domain = vendor.replace(" ", "").replace(",", "").replace(".", "").lower() + ".com"
    fallback = requests.get(f"https://logo.clearbit.com/{fallback_domain}")
    if fallback.ok:
        return Response(fallback.content, content_type="image/png")

    return "", 404

@app.route('/tts', methods=['POST'])
def tts():
    try:
        text = request.json.get('text')
        voice_id = request.json.get('voice_id')
        if not text or not voice_id:
            return jsonify({'error': 'Texte ou ID voix manquant'}), 400

        output_path = os.path.join("static", f"{uuid.uuid4()}.mp3")

        r = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers={
                "xi-api-key": os.getenv("ELEVEN_API_KEY"),
                "Content-Type": "application/json"
            },
            json={
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.4,
                    "similarity_boost": 0.75
                },
                "optimize_streaming_latency": 4
            }
        )

        if r.ok:
            with open(output_path, "wb") as f:
                f.write(r.content)
            return jsonify({'audio': f"/{output_path}"})
        else:
            return jsonify({'error': r.text}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/speedtest')
def speedtest():
    import paramiko
    ip = request.args.get("ip")
    user = request.args.get("user")
    passwd = request.args.get("pass")
    command = f"/tool bandwidth-test address={ip} user={user} password={passwd} direction=both duration=10s"

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect("192.168.0.252", username="admin", password="FG95876")
        stdin, stdout, stderr = ssh.exec_command(command)
        out = stdout.read().decode()
        err = stderr.read().decode()
        ssh.close()
        return out if not err else f"Erreur MikroTik : {err}"
    except Exception as e:
        return f"Erreur SSH : {str(e)}", 500

@app.route('/static/<path:filename>')
def static_file(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    os.makedirs("static", exist_ok=True)
    app.run(host='0.0.0.0', port=8080)
