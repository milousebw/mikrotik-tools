from flask import Flask, request, jsonify
import requests
import paramiko

app = Flask(__name__)

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
    host = "192.168.0.252"  # IP de ta VM CHR
    username = "admin"
    password = "FG95876"
    command = "/tool bandwidth-test address=82.67.47.226 user=admin password=FG95876 direction=both duration=30s"

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=username, password=password, look_for_keys=False, allow_agent=False)

        stdin, stdout, stderr = client.exec_command(command)
        output = stdout.read().decode()
        error = stderr.read().decode()
        client.close()

        if error:
            return f"Erreur MikroTik :\n{error}", 500
        return output

    except Exception as e:
        return f"Erreur de connexion SSH : {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
