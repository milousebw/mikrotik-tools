FROM python:3.11-slim

# --- Install ffmpeg ---
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

# --- Set working dir ---
WORKDIR /app

# --- Copy and install requirements ---
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Copy rest of files ---
COPY . .

# --- Expose the app ---
EXPOSE 8080

CMD ["python", "app.py"]
