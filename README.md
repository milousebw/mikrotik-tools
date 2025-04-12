# Mikrotik Tools - Web Dashboard

Un outil réseau tout-en-un avec :

- 🔍 Recherche MAC (API maclookup.app)
- 📶 Test de débit MikroTik via SSH
- 🗣️ TTS ElevenLabs (Jessy 🇫🇷, Gabriel 🇫🇷, Matilda 🇬🇧)

## Lancement

```bash
docker compose up --build -d
```

Accès via http://localhost:8080

## Configuration

Créez un `.env` avec :
```env
ELEVEN_API_KEY=your_eleven_api_key
MACLOOKUP_API_KEY=your_maclookup_key
```

## Sécurité

Accès restreint aux IPs :
- 78.155.148.66
- 192.168.0.203
