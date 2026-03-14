FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install supervisor to manage multiple processes
RUN apt-get update && apt-get install -y supervisor && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./
COPY app ./app
COPY main.py ./

RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir .

# Copy supervisor config
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

EXPOSE 8000

# Start supervisor which will manage all processes
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
