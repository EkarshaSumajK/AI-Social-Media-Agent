FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app ./app
COPY main.py ./
COPY start.sh ./

# Make start script executable
RUN chmod +x start.sh

EXPOSE 8000

# Use bash script to start all services
CMD ["./start.sh"]
