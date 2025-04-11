FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip setuptools packaging && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "app.py"]
