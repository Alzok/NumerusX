FROM python:3.10-slim

WORKDIR /app

# Dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libssl-dev \
    libta-lib-dev \
    && rm -rf /var/lib/apt/lists/*

# Génération clés de dev (à retirer en production)
ARG ENVIRONMENT=dev
RUN if [ "$ENVIRONMENT" = "dev" ]; then \
    apt-get update && apt-get install -y python3-cryptography && \
    pip install cryptography==41.0.7 && \
    python3 -c "from cryptography.fernet import Fernet; \
    print(f'ENCRYPTION_KEY={Fernet.generate_key().decode()}\nENCRYPTED_SOLANA_PK=dev_key')" > /app/config/.env; \
fi

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-u", "main.py"]