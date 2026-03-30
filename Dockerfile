FROM python:3.10-slim

WORKDIR /app

# Instalar git y dependencias básicas
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "mega_bot.py"]

