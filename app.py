from flask import Flask, request, jsonify, send_from_directory, render_template
import requests
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/mac', methods=['GET'])
def lookup_mac():
    mac = request.args.get('address')
    if not mac:
        return jsonify({'error': 'Adresse MAC manquante'}), 400

    # Appel à l'API pour obtenir les informations du fournisseur
    api_key = os.getenv("MACLOOKUP_API_KEY")
    headers = {"Authorization": f"Bearer {api_key}"}
    url = f"https://api.maclookup.app/v2/macs/{mac}"

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            vendor = data.get('company', 'Inconnu')

            # Si le fournisseur est trouvé, essayer de récupérer le logo
            logo_url = f"https://mikrotools.familleborg.fr/logo?vendor={vendor}"

            # Vérifier si le logo est accessible
            logo_response = requests.get(logo_url)
            if logo_response.status_code == 200:
                return jsonify({
                    'vendor': vendor,
                    'logo': logo_url
                })

            else:
                return jsonify({
                    'vendor': vendor,
                    'error': 'Erreur de chargement du logo.'
                })
        else:
            return jsonify({'error': 'Fournisseur non trouvé'}), 404

    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Erreur lors de la récupération de l\'adresse MAC : {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True)
