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

@app.route('/mac', methods=['GET'])
def lookup_mac():
    mac = request.args.get('address')
    if not mac:
        return jsonify({'error': 'Adresse MAC manquante'}), 400
    api_key = os.getenv("MACLOOKUP_API_KEY")
    headers = {"Authorization": f"Bearer {api_key}"}
    r = requests.get(f"https://api.maclookup.app/v2/macs/{mac}", headers=headers)
    if r.status_code == 200:
        return jsonify({'vendor': r.json().get('company', 'Inconnu')})
    elif r.status_code == 404:
        return jsonify({'error': 'Fournisseur non trouvé'}), 404
    return jsonify({'error': 'Erreur API'}), 500

@app.route('/logo')
def proxy_logo():
    vendor = request.args.get("vendor")
    if not vendor:
        return "Vendor manquant", 400

    api_key = os.getenv("LOGODEV_API_KEY")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    }

    try:
        # 1. Rechercher domaine avec Logo.dev
        search_url = f"https://api.logo.dev/search?q={vendor}"
        r = requests.get(search_url, headers=headers)
        if r.status_code == 200:
            results = r.json()
            if isinstance(results, list) and results:
                domain = results[0].get("domain")
                if domain:
                    # 2. Récupérer logo haute qualité
                    logo_url = f"https://api.logo.dev/v1/{domain}/logo.png?hq=true"
                    logo_headers = {
                        "Authorization": f"Bearer {api_key}",
                        "Accept": "image/png"
                    }
                    logo_resp = requests.get(logo_url, headers=logo_headers)
                    if logo_resp.status_code == 200 and logo_resp.content:
                        return Response(logo_resp.content, content_type="image/png")
    except Exception as e:
        print(f"[LOGO] Erreur logo.dev : {e}")

    # Fallback Clearbit
    try:
        fallback_domain = vendor.replace(" ", "").replace(",", "").replace(".", "").lower() + ".com"
        clearbit_url = f"https://logo.clearbit.com/{fallback_domain}"
        fallback_img = requests.get(clearbit_url)
        if fallback_img.status_code == 200 and fallback_img.content:
            return Response(fallback_img.content, content_type="image/png")
    except Exception as e:
        print(f"[LOGO] Erreur Clearbit : {e}")

    return "Logo introuvable", 404

@app.route('/tts', methods=['POST'])
def tts():
    try:
        text = request.json.get('text')
        voice_id = request.json.get('voice_id')
        if not text or not voice_id:
            return jsonify({'error': 'Texte ou ID voix manquant'}), 400

        output_path = os.path.join("static", f"{uuid.uuid4()}.mp3")

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "xi-api-key": os.getenv("ELEVEN_API_KEY"),
            "Content-Type": "application/json"
        }
        payload = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.4,
                "similarity_boost": 0.75
            },
            "optimize_streaming_latency": 4
        }

        r = requests.post(url, headers=headers, json=payload)
        if r.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(r.content)
            return jsonify({'audio': f"/{output_path}"})
        else:
            return jsonify({'error': f"Erreur ElevenLabs: {r.text}"}), 500
    except Exception as e:
        return jsonify({'error': f"Erreur TTS : {str(e)}"}), 500

@app.route('/speedtest', methods=['GET'])
def speedtest():
    import paramiko
    target_ip = request.args.get("ip")
    target_user = request.args.get("user")
    target_pass = request.args.get("pass")
    command = f"/tool bandwidth-test address={target_ip} user={target_user} password={target_pass} direction=both duration=10s"
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect("192.168.0.252", username="admin", password="FG95876", look_for_keys=False, allow_agent=False)
        stdin, stdout, stderr = client.exec_command(command)
        out, err = stdout.read().decode(), stderr.read().decode()
        client.close()
        return out if not err else f"Erreur MikroTik :\n{err}"
    except Exception as e:
        return f"Erreur SSH : {str(e)}", 500

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

if __name__ == '__main__':
    os.makedirs("static", exist_ok=True)
    app.run(host='0.0.0.0', port=8080)
