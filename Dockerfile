FROM python:3.10-slim

# Не создавать .pyc, не буферизовать stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Системные зависимости: gcc нужен для сборки некоторых пакетов,
# libpq-dev — для psycopg2 (если понадобится), curl — для healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Сначала зависимости — чтобы кэш слоёв работал при изменении кода
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Затем код
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]