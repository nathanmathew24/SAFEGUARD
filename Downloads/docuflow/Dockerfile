FROM python:3.12-slim

WORKDIR /app

# System deps for psycopg2 and Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /data/uploads

# Run as non-root
RUN useradd -r -s /bin/false appuser && chown -R appuser /app /data
USER appuser

EXPOSE 5000
