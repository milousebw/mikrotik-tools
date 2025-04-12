from flask import Flask, request, jsonify, render_template, send_from_directory
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

def sanitize_vendor(vendor):
    return re.sub(r'[^a-zA-Z0-9]', '', vendor).lower()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/mac")
def lookup_mac():
    mac = request.args.get("address")
    if not mac:
        return jsonify({"error": "Adresse MAC manquante"}), 400
    api_key = os.getenv("MACLOOKUP_API_KEY")
    headers = {"Authorization": f"Bearer {api_key}"}
    r = requests.get(f"https://api.maclookup.app/v2/macs/{mac}", headers=headers)
    if r.status_code == 200:
        return jsonify({"vendor": r.json().get("company", "Inconnu")})
    elif r.status_code == 404:
        return jsonify({"error": "Fournisseur non trouvé"}), 404
    return jsonify({"error": "Erreur API"}), 500

@app.route("/logo")
def proxy_logo():
    vendor = request.args.get("vendor")
    if not vendor:
        return jsonify({"error": "Vendor manquant"}), 400

    api_key = os.getenv("LOGODEV_API_KEY")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    }

    try:
        search_url = f"https://api.logo.dev/search?q={vendor}"
        r = requests.get(search_url, headers=headers)
        if r.status_code == 200:
            results = r.json()
            if isinstance(results, list) and results:
                domain = results[0].get("domain")
                if domain:
                    return jsonify({
                        "url": f"https://api.logo.dev/v1/{domain}/logo.png",
                        "link": f"https://{domain}"
                    })
    except Exception as e:
        print(f"Erreur Logo.dev: {e}")

    # Fallback Clearbit
    fallback = sanitize_vendor(vendor) + ".com"
    return jsonify({
        "url": f"https://logo.clearbit.com/{fallback}",
        "link": f"https://{fallback}"
    })

@app.route("/static/<path:filename>")
def serve_static(filename):
    return send_from_directory("static", filename)

if __name__ == "__main__":
    os.makedirs("static", exist_ok=True)
    app.run(host="0.0.0.0", port=8080)
