from flask import Flask, request, jsonify, send_from_directory, Response
import os
import requests

app = Flask(__name__)

# Configuration du dossier static pour les logos
LOGO_FOLDER = 'static/logos'
os.makedirs(LOGO_FOLDER, exist_ok=True)

@app.route('/mac', methods=['GET'])
def lookup_mac():
    mac_address = request.args.get('address')
    if not mac_address:
        return jsonify({'error': 'Adresse MAC manquante'}), 400

    # Appel à l'API maclookup pour récupérer le fournisseur
    url = f'https://api.maclookup.app/v2/macs/{mac_address}'
    headers = {
        'Authorization': 'Bearer YOUR_MACLOOKUP_API_KEY'
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return jsonify({'error': 'Erreur lors de la recherche du fournisseur'}), 500

    vendor = response.json().get('company', 'Inconnu')

    # En cas d'erreur ou d'absence de fournisseur, retour avec le nom trouvé
    return jsonify({'vendor': vendor})


@app.route('/logo', methods=['GET'])
def get_logo():
    vendor = request.args.get('vendor')
    if not vendor:
        return "Le nom du fournisseur est manquant", 400

    # Vérification si le logo est déjà en cache local
    logo_path = os.path.join(LOGO_FOLDER, f"{vendor.lower()}.png")
    if os.path.exists(logo_path):
        return send_from_directory(LOGO_FOLDER, f"{vendor.lower()}.png")

    # Sinon, on récupère le logo à partir de l'API Logo.dev
    try:
        logo_url = f'https://api.logo.dev/search?q={vendor}'
        logo_response = requests.get(logo_url, headers={'Authorization': 'Bearer YOUR_LOGODEV_API_KEY'})
        if logo_response.status_code != 200:
            return jsonify({'error': 'Impossible de récupérer le logo'}), 404

        logo_data = logo_response.json()
        if not logo_data or 'logos' not in logo_data:
            return jsonify({'error': 'Logo introuvable'}), 404

        # Récupération du logo
        logo_image_url = logo_data['logos'][0].get('url')
        if not logo_image_url:
            return jsonify({'error': 'Aucun logo trouvé'}), 404

        # Téléchargement et sauvegarde du logo localement
        logo_image = requests.get(logo_image_url)
        if logo_image.status_code == 200:
            with open(logo_path, 'wb') as f:
                f.write(logo_image.content)
            return send_from_directory(LOGO_FOLDER, f"{vendor.lower()}.png")
        else:
            return jsonify({'error': 'Erreur lors du téléchargement du logo'}), 500
    except Exception as e:
        return jsonify({'error': f"Erreur du serveur : {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
