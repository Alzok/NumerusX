FROM python:3.10-slim

WORKDIR /app

# Dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libssl-dev \
    libta-lib-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy development env file if in dev mode
ARG ENVIRONMENT=dev
COPY docker/dev.env /app/config/.env.example
RUN if [ "$ENVIRONMENT" = "dev" ]; then \
    cp /app/config/.env.example /app/config/.env; \
fi

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-u", "main.py"]