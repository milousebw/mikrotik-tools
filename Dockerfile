# Utilise une image Python légère
FROM python:3.11-slim

# Installe ffmpeg et dépendances minimales
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Définit le répertoire de travail
WORKDIR /app

# Copie le fichier de dépendances et installe-les
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copie tout le reste (code, HTML, .env, etc.)
COPY . .

# Ajoute le port exposé (utile si tu veux mapper dans docker-compose)
EXPOSE 8080

# Lance l'application
CMD ["python", "app.py"]
